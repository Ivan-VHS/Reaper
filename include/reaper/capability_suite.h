#ifndef REAPER_CAPABILITY_SUITE_H
#define REAPER_CAPABILITY_SUITE_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define REAPER_CAPABILITY_FUNCTIONS_PER_MODULE 6U
#define REAPER_CAPABILITY_MODULES 18U

typedef enum {
    REAPER_CAPABILITY_OK = 0,
    REAPER_CAPABILITY_INVALID_ARGUMENT = -1,
    REAPER_CAPABILITY_NOT_FOUND = -2,
    REAPER_CAPABILITY_ARITY_MISMATCH = -3,
    REAPER_CAPABILITY_OUT_OF_RANGE = -4,
    REAPER_CAPABILITY_NUMERIC_ERROR = -5
} ReaperCapabilityStatus;

typedef struct {
    const char *name;
    size_t min_arity;
    size_t max_arity;
    const char *description;
} ReaperCapabilityFunction;

typedef struct {
    const char *id;
    const char *name;
    const char *domain;
    const ReaperCapabilityFunction *functions;
    size_t function_count;
} ReaperCapabilityModule;

typedef int64_t (*ReaperI64Reducer)(int64_t aggregate, int64_t value,
                                    size_t index, void *context);
typedef int64_t (*ReaperI64Transform)(int64_t value, size_t index,
                                      void *context);

size_t reaper_capability_module_count(void);
const ReaperCapabilityModule *reaper_capability_module_at(size_t index);
const ReaperCapabilityModule *reaper_capability_module_find(const char *id_or_name);
const ReaperCapabilityFunction *reaper_capability_function_find(
    const ReaperCapabilityModule *module, const char *function_name);
ReaperCapabilityStatus reaper_capability_validate_arity(
    const ReaperCapabilityModule *module, const char *function_name,
    size_t argument_count, const ReaperCapabilityFunction **function_out);

/* Native, allocation-free primitives shared by the registered capabilities.
 * map_i64 requires disjoint input/output storage; reverse_i64 permits exact
 * in-place operation or disjoint storage, but not partial overlap. */
ReaperCapabilityStatus reaper_capability_fold_i64(
    const int64_t *items, size_t count, ReaperI64Reducer reducer,
    void *context, int64_t initial, int64_t *result);
ReaperCapabilityStatus reaper_capability_map_i64(
    const int64_t *items, size_t count, ReaperI64Transform transform,
    void *context, int64_t *output, size_t output_capacity);
ReaperCapabilityStatus reaper_capability_reverse_i64(
    const int64_t *items, size_t count, int64_t *output,
    size_t output_capacity);
ReaperCapabilityStatus reaper_capability_clip_f64(
    double value, double minimum, double maximum, double *output);
ReaperCapabilityStatus reaper_capability_chunk_count(
    size_t item_count, size_t chunk_size, size_t *chunk_count);
ReaperCapabilityStatus reaper_capability_calc_delta_f64(
    double current, double baseline, double *absolute_delta,
    double *relative_delta);
ReaperCapabilityStatus reaper_capability_detect_anomalies_f64(
    const double *series, size_t count, double sensitivity,
    unsigned char *flags, size_t flags_capacity, size_t *anomaly_count);
ReaperCapabilityStatus reaper_capability_forecast_trend_f64(
    const double *series, size_t count, size_t horizon, double *forecast);
ReaperCapabilityStatus reaper_capability_check_drift_f64(
    double current, double anchor, double tolerance, int *drifted);
ReaperCapabilityStatus reaper_capability_retry_delay_ms(
    unsigned attempt, unsigned base_delay_ms, unsigned max_delay_ms,
    unsigned *delay_ms);

#ifdef __cplusplus
}
#endif

#endif
