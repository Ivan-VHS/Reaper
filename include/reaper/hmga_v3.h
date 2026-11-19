#ifndef HMGA_V3_H
#define HMGA_V3_H

#include <stddef.h>
#include <stdint.h>

#define HMGA_V3_AXIOM_COUNT 20u
#define HMGA_V3_OPERATOR_COUNT 400u
#define HMGA_V3_MAX_ROUNDS 64u

typedef struct {
    const char *imperative;
    const char *quality;
    const char *engineering_vector;
} hmga_v3_axiom;

typedef struct {
    uint16_t sequence;       /* 1..400 */
    uint8_t left_axiom;      /* 1..20 */
    uint8_t right_axiom;     /* 1..20 */
} hmga_v3_operator;

typedef struct {
    uint32_t rounds;
    uint64_t operator_evaluations;
} hmga_v3_budget;

/* Returns the immutable 20-element axiom catalogue. */
const hmga_v3_axiom *hmga_v3_get_axioms(size_t *count);

/* Returns 400 ordered operators, including all 20 diagonal self-pairs. */
size_t hmga_v3_get_operator_count(void);

/* index is zero-based; output IDs use one-based axiom indices. */
int hmga_v3_get_operator(size_t index, hmga_v3_operator *out);

/* Computes a finite descriptor-evaluation budget; does not execute code. */
int hmga_v3_budget_for_rounds(uint32_t rounds, hmga_v3_budget *out);

#endif
