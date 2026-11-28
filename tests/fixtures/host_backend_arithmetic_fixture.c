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
    int64_t v0 = INT64_C(7);
    int64_t v1 = INT64_C(2);
    int64_t v2 = INT64_C(3);
    int64_t v3;
    if (!reaper_mul_i64(v1, v2, &v3)) return 0;
    int64_t v4;
    if (!reaper_sub_i64(v0, v3, &v4)) return 0;
    int64_t v5 = INT64_C(8);
    int64_t v6 = INT64_C(2);
    int64_t v7;
    if (!reaper_div_i64(v5, v6, &v7)) return 0;
    int64_t v8;
    if (!reaper_add_i64(v4, v7, &v8)) return 0;
    *result = v8;
    return 1;
}
