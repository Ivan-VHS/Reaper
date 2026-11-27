#include "reaper/snapshot_audit.h"

#include <stdio.h>
#include <string.h>

static ReaperSnapshotAuditStatus reject(
    ReaperSnapshotAuditError *error,
    ReaperSnapshotAuditStatus status,
    size_t shard_index,
    const char *message
) {
    if (error != NULL) {
        error->status = status;
        error->shard_index = shard_index;
        (void)snprintf(error->message, sizeof error->message, "%s", message);
    }
    return status;
}

static int valid_shard_id(const char *value) {
    size_t length = 0U;
    if (value == NULL || value[0] == '\0') {
        return 0;
    }
    while (value[length] != '\0') {
        const unsigned char ch = (unsigned char)value[length];
        const int alpha = (ch >= (unsigned char)'A' && ch <= (unsigned char)'Z') ||
                          (ch >= (unsigned char)'a' && ch <= (unsigned char)'z');
        const int digit = ch >= (unsigned char)'0' && ch <= (unsigned char)'9';
        const int punctuation = ch == (unsigned char)'.' ||
                                ch == (unsigned char)'_' ||
                                ch == (unsigned char)'-';
        if ((!alpha && !digit && !punctuation) ||
            length >= REAPER_SNAPSHOT_AUDIT_MAX_SHARD_ID_BYTES) {
            return 0;
        }
        ++length;
    }
    return length != 0U;
}

ReaperSnapshotAuditStatus reaper_snapshot_manifest_validate(
    const ReaperSnapshotManifest *manifest,
    ReaperSnapshotAuditError *error
) {
    if (error != NULL) {
        error->status = REAPER_SNAPSHOT_AUDIT_OK;
        error->shard_index = 0U;
        error->message[0] = '\0';
    }
    if (manifest == NULL) {
        return reject(error, REAPER_SNAPSHOT_AUDIT_INVALID_ARGUMENT, 0U,
                      "snapshot manifest is required");
    }
    if (manifest->generation == 0U) {
        return reject(error, REAPER_SNAPSHOT_AUDIT_INVALID_MANIFEST, 0U,
                      "snapshot generation must be non-zero");
    }
    if (manifest->valid_until_day_utc <= manifest->created_day_utc ||
        manifest->valid_until_day_utc - manifest->created_day_utc >
            REAPER_SNAPSHOT_AUDIT_MAX_TTL_DAYS) {
        return reject(error, REAPER_SNAPSHOT_AUDIT_INVALID_TTL, 0U,
                      "snapshot validity must be 1..120 UTC calendar days");
    }
    if (manifest->shard_count > REAPER_SNAPSHOT_AUDIT_MAX_SHARDS) {
        return reject(error, REAPER_SNAPSHOT_AUDIT_LIMIT_EXCEEDED, 0U,
                      "snapshot exceeds the shard limit");
    }
    if (manifest->shard_count != 0U && manifest->shards == NULL) {
        return reject(error, REAPER_SNAPSHOT_AUDIT_INVALID_ARGUMENT, 0U,
                      "shard storage is required for a non-empty manifest");
    }

    for (size_t i = 0U; i < manifest->shard_count; ++i) {
        const ReaperSnapshotShard *shard = &manifest->shards[i];
        if (!valid_shard_id(shard->logical_shard_id)) {
            return reject(error, REAPER_SNAPSHOT_AUDIT_INVALID_SHARD_ID, i,
                          "logical shard ID must be 1..96 ASCII letters, digits, dot, underscore or hyphen");
        }
        if (shard->schema_version == 0U) {
            return reject(error, REAPER_SNAPSHOT_AUDIT_INVALID_MANIFEST, i,
                          "shard schema version must be non-zero");
        }
        if (i != 0U &&
            strcmp(manifest->shards[i - 1U].logical_shard_id,
                   shard->logical_shard_id) >= 0) {
            return reject(error, REAPER_SNAPSHOT_AUDIT_UNSORTED_SHARDS, i,
                          "shards must be strictly sorted with unique logical IDs");
        }
    }
    if (error != NULL) {
        error->status = REAPER_SNAPSHOT_AUDIT_OK;
        error->shard_index = 0U;
        (void)snprintf(error->message, sizeof error->message, "%s", "ok");
    }
    return REAPER_SNAPSHOT_AUDIT_OK;
}

int reaper_snapshot_transient_equal(
    const void *left,
    const void *right,
    size_t length
) {
    if (length == 0U) {
        return 1;
    }
    if (left == NULL || right == NULL) {
        return 0;
    }

    const unsigned char *left_bytes = (const unsigned char *)left;
    const unsigned char *right_bytes = (const unsigned char *)right;
    volatile unsigned char difference = 0U;
    for (size_t i = 0U; i < length; ++i) {
        difference = (unsigned char)(difference |
                                     (unsigned char)(left_bytes[i] ^ right_bytes[i]));
    }
    return difference == 0U;
}

static size_t union_count(
    const ReaperSnapshotManifest *baseline,
    const ReaperSnapshotManifest *candidate
) {
    size_t left = 0U;
    size_t right = 0U;
    size_t count = 0U;

    while (left < baseline->shard_count || right < candidate->shard_count) {
        if (left == baseline->shard_count) {
            ++right;
        } else if (right == candidate->shard_count) {
            ++left;
        } else {
            const int order = strcmp(
                baseline->shards[left].logical_shard_id,
                candidate->shards[right].logical_shard_id
            );
            if (order < 0) {
                ++left;
            } else if (order > 0) {
                ++right;
            } else {
                ++left;
                ++right;
            }
        }
        ++count;
    }
    return count;
}

static void add_delta(
    ReaperSnapshotDelta *deltas,
    size_t *written,
    ReaperSnapshotAuditSummary *summary,
    const char *shard_id,
    ReaperSnapshotDeltaKind kind,
    const ReaperSnapshotShard *before,
    const ReaperSnapshotShard *after
) {
    ReaperSnapshotDelta *delta = &deltas[*written];
    delta->logical_shard_id = shard_id;
    delta->kind = kind;
    delta->before_schema_version = before != NULL ? before->schema_version : 0U;
    delta->after_schema_version = after != NULL ? after->schema_version : 0U;
    delta->before_item_count = before != NULL ? before->item_count : 0U;
    delta->after_item_count = after != NULL ? after->item_count : 0U;
    ++(*written);

    switch (kind) {
    case REAPER_SNAPSHOT_DELTA_UNCHANGED: ++summary->unchanged; break;
    case REAPER_SNAPSHOT_DELTA_CONTENT_CHANGED: ++summary->content_changed; break;
    case REAPER_SNAPSHOT_DELTA_SCHEMA_CHANGED: ++summary->schema_changed; break;
    case REAPER_SNAPSHOT_DELTA_ADDED: ++summary->added; break;
    case REAPER_SNAPSHOT_DELTA_REMOVED: ++summary->removed; break;
    }
}

ReaperSnapshotAuditStatus reaper_snapshot_compare(
    const ReaperSnapshotManifest *baseline,
    const ReaperSnapshotManifest *candidate,
    uint32_t current_day_utc,
    ReaperSnapshotDelta *deltas,
    size_t delta_capacity,
    size_t *written,
    ReaperSnapshotAuditSummary *summary,
    ReaperSnapshotAuditError *error
) {
    if (written == NULL) {
        return reject(error, REAPER_SNAPSHOT_AUDIT_INVALID_ARGUMENT, 0U,
                      "written output is required");
    }
    *written = 0U;
    if (summary != NULL) {
        memset(summary, 0, sizeof *summary);
    }

    ReaperSnapshotAuditStatus status =
        reaper_snapshot_manifest_validate(baseline, error);
    if (status != REAPER_SNAPSHOT_AUDIT_OK) {
        return status;
    }
    status = reaper_snapshot_manifest_validate(candidate, error);
    if (status != REAPER_SNAPSHOT_AUDIT_OK) {
        return status;
    }
    if (candidate->generation <= baseline->generation ||
        candidate->created_day_utc < baseline->created_day_utc) {
        return reject(error, REAPER_SNAPSHOT_AUDIT_INVALID_ORDER, 0U,
                      "candidate generation and creation day must advance");
    }
    if (current_day_utc < baseline->created_day_utc ||
        current_day_utc < candidate->created_day_utc) {
        return reject(error, REAPER_SNAPSHOT_AUDIT_INVALID_ORDER, 0U,
                      "snapshot cannot be audited before its creation day");
    }
    if (current_day_utc >= baseline->valid_until_day_utc ||
        current_day_utc >= candidate->valid_until_day_utc) {
        return reject(error, REAPER_SNAPSHOT_AUDIT_EXPIRED, 0U,
                      "snapshot validity window has expired");
    }

    const size_t required = union_count(baseline, candidate);
    if (required > delta_capacity || (required != 0U && deltas == NULL)) {
        return reject(error, REAPER_SNAPSHOT_AUDIT_BUFFER_TOO_SMALL, 0U,
                      "delta output capacity is smaller than the required union");
    }

    ReaperSnapshotAuditSummary local_summary = {0U, 0U, 0U, 0U, 0U};
    size_t left = 0U;
    size_t right = 0U;
    size_t output_index = 0U;

    while (left < baseline->shard_count || right < candidate->shard_count) {
        if (left == baseline->shard_count) {
            const ReaperSnapshotShard *after = &candidate->shards[right++];
            add_delta(deltas, &output_index, &local_summary,
                      after->logical_shard_id, REAPER_SNAPSHOT_DELTA_ADDED,
                      NULL, after);
            continue;
        }
        if (right == candidate->shard_count) {
            const ReaperSnapshotShard *before = &baseline->shards[left++];
            add_delta(deltas, &output_index, &local_summary,
                      before->logical_shard_id, REAPER_SNAPSHOT_DELTA_REMOVED,
                      before, NULL);
            continue;
        }

        const ReaperSnapshotShard *before = &baseline->shards[left];
        const ReaperSnapshotShard *after = &candidate->shards[right];
        const int order = strcmp(before->logical_shard_id, after->logical_shard_id);
        if (order < 0) {
            ++left;
            add_delta(deltas, &output_index, &local_summary,
                      before->logical_shard_id, REAPER_SNAPSHOT_DELTA_REMOVED,
                      before, NULL);
        } else if (order > 0) {
            ++right;
            add_delta(deltas, &output_index, &local_summary,
                      after->logical_shard_id, REAPER_SNAPSHOT_DELTA_ADDED,
                      NULL, after);
        } else {
            ReaperSnapshotDeltaKind kind = REAPER_SNAPSHOT_DELTA_UNCHANGED;
            if (before->schema_version != after->schema_version) {
                kind = REAPER_SNAPSHOT_DELTA_SCHEMA_CHANGED;
            } else if (before->item_count != after->item_count ||
                       !reaper_snapshot_transient_equal(
                           before->digest, after->digest,
                           REAPER_SNAPSHOT_AUDIT_DIGEST_BYTES)) {
                kind = REAPER_SNAPSHOT_DELTA_CONTENT_CHANGED;
            }
            ++left;
            ++right;
            add_delta(deltas, &output_index, &local_summary,
                      before->logical_shard_id, kind, before, after);
        }
    }

    *written = output_index;
    if (summary != NULL) {
        *summary = local_summary;
    }
    if (error != NULL) {
        error->status = REAPER_SNAPSHOT_AUDIT_OK;
        error->shard_index = 0U;
        (void)snprintf(error->message, sizeof error->message, "%s", "ok");
    }
    return REAPER_SNAPSHOT_AUDIT_OK;
}

const char *reaper_snapshot_audit_status_name(ReaperSnapshotAuditStatus status) {
    switch (status) {
    case REAPER_SNAPSHOT_AUDIT_OK: return "ok";
    case REAPER_SNAPSHOT_AUDIT_INVALID_ARGUMENT: return "invalid-argument";
    case REAPER_SNAPSHOT_AUDIT_LIMIT_EXCEEDED: return "limit-exceeded";
    case REAPER_SNAPSHOT_AUDIT_INVALID_MANIFEST: return "invalid-manifest";
    case REAPER_SNAPSHOT_AUDIT_INVALID_TTL: return "invalid-ttl";
    case REAPER_SNAPSHOT_AUDIT_EXPIRED: return "expired";
    case REAPER_SNAPSHOT_AUDIT_INVALID_SHARD_ID: return "invalid-shard-id";
    case REAPER_SNAPSHOT_AUDIT_UNSORTED_SHARDS: return "unsorted-shards";
    case REAPER_SNAPSHOT_AUDIT_INVALID_ORDER: return "invalid-order";
    case REAPER_SNAPSHOT_AUDIT_BUFFER_TOO_SMALL: return "buffer-too-small";
    }
    return "unknown";
}

const char *reaper_snapshot_delta_kind_name(ReaperSnapshotDeltaKind kind) {
    switch (kind) {
    case REAPER_SNAPSHOT_DELTA_UNCHANGED: return "unchanged";
    case REAPER_SNAPSHOT_DELTA_CONTENT_CHANGED: return "content-changed";
    case REAPER_SNAPSHOT_DELTA_SCHEMA_CHANGED: return "schema-changed";
    case REAPER_SNAPSHOT_DELTA_ADDED: return "added";
    case REAPER_SNAPSHOT_DELTA_REMOVED: return "removed";
    }
    return "unknown";
}
