#ifndef REAPER_SNAPSHOT_AUDIT_H
#define REAPER_SNAPSHOT_AUDIT_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define REAPER_SNAPSHOT_AUDIT_ABI_VERSION 1U
#define REAPER_SNAPSHOT_AUDIT_DIGEST_BYTES 32U
#define REAPER_SNAPSHOT_AUDIT_MAX_SHARDS 4096U
#define REAPER_SNAPSHOT_AUDIT_MAX_SHARD_ID_BYTES 96U
#define REAPER_SNAPSHOT_AUDIT_MAX_TTL_DAYS 120U

typedef struct {
    const char *logical_shard_id;
    uint32_t schema_version;
    uint64_t item_count;
    uint8_t digest[REAPER_SNAPSHOT_AUDIT_DIGEST_BYTES];
} ReaperSnapshotShard;

typedef struct {
    uint64_t generation;
    uint32_t created_day_utc;
    /* Exclusive UTC day boundary. The snapshot is invalid on this day. */
    uint32_t valid_until_day_utc;
    const ReaperSnapshotShard *shards;
    size_t shard_count;
} ReaperSnapshotManifest;

typedef enum {
    REAPER_SNAPSHOT_AUDIT_OK = 0,
    REAPER_SNAPSHOT_AUDIT_INVALID_ARGUMENT,
    REAPER_SNAPSHOT_AUDIT_LIMIT_EXCEEDED,
    REAPER_SNAPSHOT_AUDIT_INVALID_MANIFEST,
    REAPER_SNAPSHOT_AUDIT_INVALID_TTL,
    REAPER_SNAPSHOT_AUDIT_EXPIRED,
    REAPER_SNAPSHOT_AUDIT_INVALID_SHARD_ID,
    REAPER_SNAPSHOT_AUDIT_UNSORTED_SHARDS,
    REAPER_SNAPSHOT_AUDIT_INVALID_ORDER,
    REAPER_SNAPSHOT_AUDIT_BUFFER_TOO_SMALL
} ReaperSnapshotAuditStatus;

typedef enum {
    REAPER_SNAPSHOT_DELTA_UNCHANGED = 0,
    REAPER_SNAPSHOT_DELTA_CONTENT_CHANGED,
    REAPER_SNAPSHOT_DELTA_SCHEMA_CHANGED,
    REAPER_SNAPSHOT_DELTA_ADDED,
    REAPER_SNAPSHOT_DELTA_REMOVED
} ReaperSnapshotDeltaKind;

typedef struct {
    const char *logical_shard_id;
    ReaperSnapshotDeltaKind kind;
    uint32_t before_schema_version;
    uint32_t after_schema_version;
    uint64_t before_item_count;
    uint64_t after_item_count;
} ReaperSnapshotDelta;

typedef struct {
    size_t unchanged;
    size_t content_changed;
    size_t schema_changed;
    size_t added;
    size_t removed;
} ReaperSnapshotAuditSummary;

typedef struct {
    ReaperSnapshotAuditStatus status;
    size_t shard_index;
    char message[160];
} ReaperSnapshotAuditError;

/* Validate bounded, aggregate-only metadata. Shards must be sorted by
 * logical_shard_id in ascending bytewise order and IDs must be ASCII-safe. */
ReaperSnapshotAuditStatus reaper_snapshot_manifest_validate(
    const ReaperSnapshotManifest *manifest,
    ReaperSnapshotAuditError *error
);

/* Produce a deterministic union diff of logical shard aggregates only.
 * No row-level keys or payloads are read or emitted. Output shard IDs borrow
 * storage from the input manifests and remain valid only as long as they do.
 * current_day_utc uses UTC days since 1970-01-01; expiry is exclusive.
 * On failure, written is zero and the output array is not modified. */
ReaperSnapshotAuditStatus reaper_snapshot_compare(
    const ReaperSnapshotManifest *baseline,
    const ReaperSnapshotManifest *candidate,
    uint32_t current_day_utc,
    ReaperSnapshotDelta *deltas,
    size_t delta_capacity,
    size_t *written,
    ReaperSnapshotAuditSummary *summary,
    ReaperSnapshotAuditError *error
);

/* Compare caller-owned transient bytes without allocating, copying, logging
 * or retaining them. The caller owns buffer lifetime and zeroization. */
int reaper_snapshot_transient_equal(
    const void *left,
    const void *right,
    size_t length
);

const char *reaper_snapshot_audit_status_name(ReaperSnapshotAuditStatus status);
const char *reaper_snapshot_delta_kind_name(ReaperSnapshotDeltaKind kind);

#ifdef __cplusplus
}
#endif

#endif
