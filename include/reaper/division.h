#ifndef REAPER_DIVISION_H
#define REAPER_DIVISION_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define REAPER_DIVISION_MAX_PARTITIONS 65536U

typedef struct {
    int64_t quotient;
    int64_t remainder;
} ReaperEuclideanResult;

typedef struct {
    size_t item_count;
    size_t partition_count;
    size_t base_count;
    size_t remainder_count;
} ReaperPartitionPlan;

/* Returns 0 on success. Remainder is always in [0, abs(divisor)). */
int reaper_euclidean_divmod_i64(
    int64_t dividend, int64_t divisor, ReaperEuclideanResult *out
);
int reaper_is_divisible_i64(int64_t dividend, int64_t divisor, int *out);

/* Balanced contiguous ranges; the first remainder_count ranges get one extra item. */
int reaper_partition_plan_init(
    size_t item_count, size_t partition_count, ReaperPartitionPlan *out
);
int reaper_partition_plan_range(
    const ReaperPartitionPlan *plan, size_t index, size_t *offset, size_t *count
);

/* Advisory worker count based on available workers and a minimum work grain. */
int reaper_recommend_partition_count(
    size_t work_items, size_t available_workers, size_t minimum_grain,
    size_t *recommended
);

#ifdef __cplusplus
}
#endif

#endif
