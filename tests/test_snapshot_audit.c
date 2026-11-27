#include "reaper/snapshot_audit.h"

#ifdef NDEBUG
#undef NDEBUG
#endif
#include <assert.h>
#include <stdio.h>
#include <string.h>

static void set_digest(uint8_t digest[REAPER_SNAPSHOT_AUDIT_DIGEST_BYTES],
                       uint8_t value) {
    for (size_t i = 0U; i < REAPER_SNAPSHOT_AUDIT_DIGEST_BYTES; ++i) {
        digest[i] = (uint8_t)(value + (uint8_t)i);
    }
}

static void test_sorted_aggregate_diff_is_deterministic(void) {
    ReaperSnapshotShard before[] = {
        {"audio", 1U, 100U, {0}},
        {"kernel", 3U, 20U, {0}},
        {"legacy", 1U, 7U, {0}},
        {"network", 2U, 50U, {0}}
    };
    ReaperSnapshotShard after[] = {
        {"audio", 1U, 100U, {0}},
        {"kernel", 3U, 22U, {0}},
        {"network", 4U, 50U, {0}},
        {"storage", 1U, 0U, {0}}
    };
    set_digest(before[0].digest, 1U);
    set_digest(before[1].digest, 2U);
    set_digest(before[2].digest, 3U);
    set_digest(before[3].digest, 4U);
    set_digest(after[0].digest, 1U);
    set_digest(after[1].digest, 5U);
    set_digest(after[2].digest, 4U);
    set_digest(after[3].digest, 6U);

    const ReaperSnapshotManifest baseline = {10U, 10U, 130U, before, 4U};
    const ReaperSnapshotManifest candidate = {11U, 20U, 140U, after, 4U};
    ReaperSnapshotDelta deltas[8];
    ReaperSnapshotAuditSummary summary;
    ReaperSnapshotAuditError error;
    size_t written = 0U;

    assert(reaper_snapshot_compare(&baseline, &candidate, 21U, deltas, 8U,
                                   &written, &summary, &error) ==
           REAPER_SNAPSHOT_AUDIT_OK);
    assert(written == 5U);
    assert(strcmp(deltas[0].logical_shard_id, "audio") == 0);
    assert(deltas[0].kind == REAPER_SNAPSHOT_DELTA_UNCHANGED);
    assert(strcmp(deltas[1].logical_shard_id, "kernel") == 0);
    assert(deltas[1].kind == REAPER_SNAPSHOT_DELTA_CONTENT_CHANGED);
    assert(strcmp(deltas[2].logical_shard_id, "legacy") == 0);
    assert(deltas[2].kind == REAPER_SNAPSHOT_DELTA_REMOVED);
    assert(strcmp(deltas[3].logical_shard_id, "network") == 0);
    assert(deltas[3].kind == REAPER_SNAPSHOT_DELTA_SCHEMA_CHANGED);
    assert(strcmp(deltas[4].logical_shard_id, "storage") == 0);
    assert(deltas[4].kind == REAPER_SNAPSHOT_DELTA_ADDED);
    assert(summary.unchanged == 1U);
    assert(summary.content_changed == 1U);
    assert(summary.schema_changed == 1U);
    assert(summary.removed == 1U);
    assert(summary.added == 1U);
    assert(strcmp(reaper_snapshot_delta_kind_name(deltas[4].kind), "added") == 0);
}

static void test_manifest_limits_and_order_are_enforced(void) {
    ReaperSnapshotAuditError error;
    ReaperSnapshotShard unsorted[] = {
        {"zeta", 1U, 1U, {0}},
        {"alpha", 1U, 1U, {0}}
    };
    ReaperSnapshotManifest manifest = {1U, 100U, 220U, unsorted, 2U};
    assert(reaper_snapshot_manifest_validate(&manifest, &error) ==
           REAPER_SNAPSHOT_AUDIT_UNSORTED_SHARDS);
    assert(error.shard_index == 1U);

    ReaperSnapshotShard invalid_id[] = {{"person@example", 1U, 1U, {0}}};
    manifest = (ReaperSnapshotManifest){1U, 100U, 220U, invalid_id, 1U};
    assert(reaper_snapshot_manifest_validate(&manifest, &error) ==
           REAPER_SNAPSHOT_AUDIT_INVALID_SHARD_ID);

    manifest = (ReaperSnapshotManifest){1U, 100U, 221U, NULL, 0U};
    assert(reaper_snapshot_manifest_validate(&manifest, &error) ==
           REAPER_SNAPSHOT_AUDIT_INVALID_TTL);
}

static void test_expiry_and_generation_order_are_enforced(void) {
    ReaperSnapshotShard shards[] = {{"runtime", 1U, 0U, {0}}};
    const ReaperSnapshotManifest baseline = {7U, 10U, 20U, shards, 1U};
    const ReaperSnapshotManifest candidate = {8U, 11U, 21U, shards, 1U};
    ReaperSnapshotAuditError error;
    size_t written = 99U;

    assert(reaper_snapshot_compare(&baseline, &candidate, 20U, NULL, 0U,
                                   &written, NULL, &error) ==
           REAPER_SNAPSHOT_AUDIT_EXPIRED);
    assert(written == 0U);

    const ReaperSnapshotManifest stale = {7U, 11U, 21U, shards, 1U};
    assert(reaper_snapshot_compare(&baseline, &stale, 12U, NULL, 0U,
                                   &written, NULL, &error) ==
           REAPER_SNAPSHOT_AUDIT_INVALID_ORDER);
}

static void test_output_capacity_failure_does_not_write(void) {
    ReaperSnapshotShard before[] = {{"alpha", 1U, 1U, {0}}};
    ReaperSnapshotShard after[] = {
        {"alpha", 1U, 1U, {0}},
        {"beta", 1U, 1U, {0}}
    };
    const ReaperSnapshotManifest baseline = {1U, 1U, 10U, before, 1U};
    const ReaperSnapshotManifest candidate = {2U, 2U, 11U, after, 2U};
    ReaperSnapshotDelta output[1];
    output[0].logical_shard_id = "sentinel";
    output[0].kind = REAPER_SNAPSHOT_DELTA_REMOVED;
    ReaperSnapshotAuditSummary summary = {9U, 9U, 9U, 9U, 9U};
    ReaperSnapshotAuditError error;
    size_t written = 99U;

    assert(reaper_snapshot_compare(&baseline, &candidate, 3U, output, 1U,
                                   &written, &summary, &error) ==
           REAPER_SNAPSHOT_AUDIT_BUFFER_TOO_SMALL);
    assert(written == 0U);
    assert(strcmp(output[0].logical_shard_id, "sentinel") == 0);
    assert(output[0].kind == REAPER_SNAPSHOT_DELTA_REMOVED);
    assert(summary.unchanged == 0U && summary.added == 0U);
}

static void test_transient_comparison_retains_no_buffer(void) {
    const unsigned char left[] = {0x10U, 0x20U, 0x30U, 0x40U};
    const unsigned char same[] = {0x10U, 0x20U, 0x30U, 0x40U};
    const unsigned char different[] = {0x10U, 0x20U, 0x31U, 0x40U};
    assert(reaper_snapshot_transient_equal(left, same, sizeof left));
    assert(!reaper_snapshot_transient_equal(left, different, sizeof left));
    assert(!reaper_snapshot_transient_equal(left, same, sizeof left - 1U));
    assert(!reaper_snapshot_transient_equal(NULL, same, sizeof same));
    assert(reaper_snapshot_transient_equal(NULL, NULL, 0U));
}

int main(void) {
    test_sorted_aggregate_diff_is_deterministic();
    test_manifest_limits_and_order_are_enforced();
    test_expiry_and_generation_order_are_enforced();
    test_output_capacity_failure_does_not_write();
    test_transient_comparison_retains_no_buffer();
    puts("native snapshot audit tests: 5 groups passed");
    return 0;
}
