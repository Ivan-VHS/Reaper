#include <stdint.h>
#include <limits.h>

static int reaper_add_i64(int64_t a, int64_t b, int64_t *out) {
    if ((b > 0 && a > INT64_MAX - b) || (b < 0 && a < INT64_MIN - b)) return 0;
    *out = a + b; return 1;
}
static int reaper_sub_i64(int64_t a, int64_t b, int64_t *out) {
    if ((b < 0 && a > INT64_MAX + b) || (b > 0 && a < INT64_MIN + b)) return 0;
    *out = a - b; return 1;
}
static int reaper_mul_i64(int64_t a, int64_t b, int64_t *out) {
    if (a == 0 || b == 0) { *out = 0; return 1; }
    if ((a == -1 && b == INT64_MIN) || (b == -1 && a == INT64_MIN)) return 0;
    if (a > 0) {
        if ((b > 0 && a > INT64_MAX / b) || (b < 0 && b < INT64_MIN / a)) return 0;
    } else {
        if ((b > 0 && a < INT64_MIN / b) || (b < 0 && a < INT64_MAX / b)) return 0;
    }
    *out = a * b; return 1;
}
static int reaper_div_i64(int64_t a, int64_t b, int64_t *out) {
    if (b == 0 || (a == INT64_MIN && b == -1)) return 0;
    *out = a / b; return 1;
}

int reaper_generated_entry(int64_t *result) {
    if (result == 0) return 0;
    int64_t v0 = INT64_C(19);
    int64_t v1 = INT64_C(23);
    int64_t v2;
    if (!reaper_add_i64(v0, v1, &v2)) return 0;
    *result = v2;
    return 1;
}
