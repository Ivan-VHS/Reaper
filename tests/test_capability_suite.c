#include "reaper/capability_suite.h"

#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

static int64_t sum_values(int64_t aggregate, int64_t value,
                          size_t index, void *context) {
    (void)index;
    (void)context;
    return aggregate + value;
}

static int64_t multiply_value(int64_t value, size_t index, void *context) {
    const int64_t multiplier = *(const int64_t *)context;
    return value * multiplier + (int64_t)index;
}

static void registry_exposes_all_modules_and_operations(void) {
    static const char *const ids[REAPER_CAPABILITY_MODULES] = {
        "operandu", "dropaul", "zdoro", "pyemont", "dilly", "baplap",
        "sretuo", "kali", "zalam", "liur", "keel-koh", "vorof",
        "vprof", "profe", "prossee", "vprossee", "professiya", "profevo"
    };
    size_t total = 0U;
    assert(reaper_capability_module_count() == REAPER_CAPABILITY_MODULES);
    for (size_t i = 0U; i < REAPER_CAPABILITY_MODULES; ++i) {
        const ReaperCapabilityModule *module = reaper_capability_module_at(i);
        assert(module != NULL);
        assert(strcmp(module->id, ids[i]) == 0);
        assert(module->function_count == REAPER_CAPABILITY_FUNCTIONS_PER_MODULE);
        total += module->function_count;
    }
    assert(total == 108U);
    assert(reaper_capability_module_at(REAPER_CAPABILITY_MODULES) == NULL);
    assert(reaper_capability_module_find("KEEL-KOH") != NULL);
    assert(reaper_capability_module_find("Operandu")->id[0] == 'o');
    assert(reaper_capability_module_find("missing") == NULL);
}

static void function_signatures_validate_arity(void) {
    const ReaperCapabilityModule *module =
        reaper_capability_module_find("operandu");
    const ReaperCapabilityFunction *function = NULL;
    assert(module != NULL);
    assert(reaper_capability_validate_arity(
        module, "fold_series", 3U, &function) == REAPER_CAPABILITY_OK);
    assert(function != NULL && function->min_arity == 3U);
    assert(reaper_capability_validate_arity(
        module, "fold_series", 2U, NULL) == REAPER_CAPABILITY_ARITY_MISMATCH);
    assert(reaper_capability_validate_arity(
        module, "not_registered", 1U, NULL) == REAPER_CAPABILITY_NOT_FOUND);
    assert(reaper_capability_validate_arity(
        NULL, "fold_series", 3U, NULL) == REAPER_CAPABILITY_INVALID_ARGUMENT);
}

static void fold_and_map_are_bounded_and_non_mutating(void) {
    const int64_t input[] = { 1, 2, 3, 4 };
    int64_t mapped[4] = { 0, 0, 0, 0 };
    int64_t aggregate = -1;
    const int64_t multiplier = 3;
    assert(reaper_capability_fold_i64(
        input, 4U, sum_values, NULL, 0, &aggregate) == REAPER_CAPABILITY_OK);
    assert(aggregate == 10);
    assert(reaper_capability_map_i64(
        input, 4U, multiply_value, (void *)&multiplier,
        mapped, 4U) == REAPER_CAPABILITY_OK);
    assert(mapped[0] == 3 && mapped[1] == 7 &&
           mapped[2] == 11 && mapped[3] == 15);
    assert(input[0] == 1 && input[3] == 4);
    assert(reaper_capability_map_i64(
        input, 4U, multiply_value, (void *)&multiplier,
        mapped, 3U) == REAPER_CAPABILITY_OUT_OF_RANGE);
}

static void reverse_supports_copy_and_in_place(void) {
    const int64_t input[] = { 5, 7, 9, 11 };
    int64_t output[4] = { 0, 0, 0, 0 };
    int64_t mutable_values[] = { 1, 2, 3 };
    assert(reaper_capability_reverse_i64(
        input, 4U, output, 4U) == REAPER_CAPABILITY_OK);
    assert(output[0] == 11 && output[3] == 5);
    assert(reaper_capability_reverse_i64(
        mutable_values, 3U, mutable_values, 3U) == REAPER_CAPABILITY_OK);
    assert(mutable_values[0] == 3 && mutable_values[2] == 1);
}

static void range_and_chunk_primitives_validate_boundaries(void) {
    double clipped = 0.0;
    size_t chunks = 0U;
    assert(reaper_capability_clip_f64(
        12.0, 0.0, 10.0, &clipped) == REAPER_CAPABILITY_OK);
    assert(clipped == 10.0);
    assert(reaper_capability_clip_f64(
        3.0, 5.0, 2.0, &clipped) == REAPER_CAPABILITY_OUT_OF_RANGE);
    assert(reaper_capability_chunk_count(
        10U, 4U, &chunks) == REAPER_CAPABILITY_OK);
    assert(chunks == 3U);
    assert(reaper_capability_chunk_count(
        0U, 4U, &chunks) == REAPER_CAPABILITY_OK && chunks == 0U);
    assert(reaper_capability_chunk_count(
        10U, 0U, &chunks) == REAPER_CAPABILITY_INVALID_ARGUMENT);
}

static void analytics_primitives_return_checked_results(void) {
    const double series[] = { 1.0, 1.0, 1.0, 100.0 };
    unsigned char flags[4] = { 0U, 0U, 0U, 0U };
    size_t anomaly_count = 0U;
    double absolute_delta = 0.0, relative_delta = 0.0, forecast = 0.0;
    assert(reaper_capability_calc_delta_f64(
        125.0, 100.0, &absolute_delta,
        &relative_delta) == REAPER_CAPABILITY_OK);
    assert(absolute_delta == 25.0 && relative_delta == 0.25);
    assert(reaper_capability_calc_delta_f64(
        1.0, 0.0, &absolute_delta,
        &relative_delta) == REAPER_CAPABILITY_NUMERIC_ERROR);
    assert(reaper_capability_detect_anomalies_f64(
        series, 4U, 1.5, flags, 4U,
        &anomaly_count) == REAPER_CAPABILITY_OK);
    assert(anomaly_count == 1U && flags[3] == 1U);
    assert(reaper_capability_detect_anomalies_f64(
        series, 4U, 1.5, flags, 3U,
        &anomaly_count) == REAPER_CAPABILITY_OUT_OF_RANGE);
    {
        const double trend[] = { 2.0, 4.0, 6.0 };
        assert(reaper_capability_forecast_trend_f64(
            trend, 3U, 1U, &forecast) == REAPER_CAPABILITY_OK);
        assert(forecast > 7.999 && forecast < 8.001);
        assert(reaper_capability_forecast_trend_f64(
            trend, 3U, 2U, &forecast) == REAPER_CAPABILITY_OK);
        assert(forecast > 9.999 && forecast < 10.001);
    }
}

static void drift_and_retry_are_saturating(void) {
    int drifted = 0;
    unsigned delay = 0U;
    assert(reaper_capability_check_drift_f64(
        10.2, 10.0, 0.1, &drifted) == REAPER_CAPABILITY_OK);
    assert(drifted == 1);
    assert(reaper_capability_check_drift_f64(
        10.05, 10.0, 0.1, &drifted) == REAPER_CAPABILITY_OK);
    assert(drifted == 0);
    assert(reaper_capability_retry_delay_ms(
        0U, 10U, 100U, &delay) == REAPER_CAPABILITY_OK && delay == 10U);
    assert(reaper_capability_retry_delay_ms(
        4U, 10U, 100U, &delay) == REAPER_CAPABILITY_OK && delay == 100U);
    assert(reaper_capability_retry_delay_ms(
        1U, 101U, 100U, &delay) == REAPER_CAPABILITY_INVALID_ARGUMENT);
}

int main(void) {
    registry_exposes_all_modules_and_operations();
    function_signatures_validate_arity();
    fold_and_map_are_bounded_and_non_mutating();
    reverse_supports_copy_and_in_place();
    range_and_chunk_primitives_validate_boundaries();
    analytics_primitives_return_checked_results();
    drift_and_retry_are_saturating();
    puts("native capability suite tests: 7 groups passed (18 modules, 108 contracts)");
    return 0;
}
