#include "reaper/division.h"

#include <limits.h>

int reaper_euclidean_divmod_i64(
    int64_t dividend, int64_t divisor, ReaperEuclideanResult *out
) {
    int64_t quotient;
    int64_t remainder;

    if (out == NULL || divisor == 0 ||
        (dividend == INT64_MIN && divisor == -1)) {
        return -1;
    }

    quotient = dividend / divisor;
    remainder = dividend % divisor;
    if (remainder < 0) {
        if (divisor > 0) {
            --quotient;
            remainder += divisor;
        } else {
            ++quotient;
            remainder -= divisor;
        }
    }

    out->quotient = quotient;
    out->remainder = remainder;
    return 0;
}

int reaper_is_divisible_i64(int64_t dividend, int64_t divisor, int *out) {
    ReaperEuclideanResult result;
    if (out == NULL ||
        reaper_euclidean_divmod_i64(dividend, divisor, &result) != 0) {
        return -1;
    }
    *out = result.remainder == 0 ? 1 : 0;
    return 0;
}

int reaper_partition_plan_init(
    size_t item_count, size_t partition_count, ReaperPartitionPlan *out
) {
    if (out == NULL || partition_count == 0U ||
        partition_count > REAPER_DIVISION_MAX_PARTITIONS) {
        return -1;
    }
    out->item_count = item_count;
    out->partition_count = partition_count;
    out->base_count = item_count / partition_count;
    out->remainder_count = item_count % partition_count;
    return 0;
}

int reaper_partition_plan_range(
    const ReaperPartitionPlan *plan, size_t index, size_t *offset, size_t *count
) {
    if (plan == NULL || offset == NULL || count == NULL ||
        plan->partition_count == 0U ||
        plan->partition_count > REAPER_DIVISION_MAX_PARTITIONS ||
        index >= plan->partition_count) {
        return -1;
    }
    *count = plan->base_count + (index < plan->remainder_count ? 1U : 0U);
    *offset = index * plan->base_count +
        (index < plan->remainder_count ? index : plan->remainder_count);
    return 0;
}

int reaper_recommend_partition_count(
    size_t work_items, size_t available_workers, size_t minimum_grain,
    size_t *recommended
) {
    size_t candidate;
    if (recommended == NULL || available_workers == 0U || minimum_grain == 0U) {
        return -1;
    }
    if (work_items == 0U) {
        *recommended = 0U;
        return 0;
    }
    candidate = work_items / minimum_grain;
    if (candidate == 0U) candidate = 1U;
    if (candidate > available_workers) candidate = available_workers;
    if (candidate > work_items) candidate = work_items;
    if (candidate > REAPER_DIVISION_MAX_PARTITIONS)
        candidate = REAPER_DIVISION_MAX_PARTITIONS;
    *recommended = candidate;
    return 0;
}
