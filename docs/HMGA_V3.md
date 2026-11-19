# HMGA v3.0 — bounded operator matrix and repository-evolution contract

Status: implemented planning catalogue and normative engineering policy. This document does not authorize unrestricted source generation, direct writes to `main`, or execution of generated code.

## 1. Purpose and interpretation

HMGA (Hyper-Scale Modular Generative Architecture) expresses 20 engineering axioms as a directed Cartesian product. The product contains exactly 400 ordered operator descriptors:

\[
M = A \times A,\qquad |M| = 20 \times 20 = 400
\]

The matrix is a **planning and traceability model**. It is not a claim that arbitrary functions can be multiplied, that every pair is semantically compatible, or that the repository should be rewritten 400 times. An enumerated operator is a candidate review lens; it becomes an implementation task only when there is a concrete gap, a compatibility argument, an acceptance criterion, and a rollback plan.

The native C17 implementation in `src/hmga_v3.c` exposes the immutable axiom catalogue, deterministic operator enumeration, and finite budget calculation. It performs no filesystem, Git, network, build, code-generation, or source-execution operation.

## 2. The 20-axiom basis

| ID | Imperative | Quality | Engineering vector |
|---|---|---|---|
| A01 | Lock | Naturalness | Compose functions |
| A02 | Fix | Organicity | Automated tests |
| A03 | Establish | Ease | Review-gated delivery |
| A04 | Reserve | Naturalness | Optional startup |
| A05 | Prepare | Sincerity | Native application |
| A06 | Assign | Authenticity | Desktop application |
| A07 | Approve | Genuineness | White-red-blue design |
| A08 | Standardize | Individuality | Version and dependency updates |
| A09 | Expose | Vitality | New functions |
| A10 | Apply | Compatibility | Apply compatible functions to compatible inputs |
| A11 | Configure | Simplicity | Configuration |
| A12 | Integrate | Directness | Merge after review |
| A13 | Ensure | Wholeness | Unify compatible modules |
| A14 | Protect | Organicity | Systematize |
| A15 | Set | Unobtrusiveness | Consolidate modules |
| A16 | Refine | Freedom | Improve code readability |
| A17 | Improve | Integrity | Improve quality |
| A18 | Scale | Relevance | Expand useful capabilities |
| A19 | Strengthen | Harmony | Improve robustness |
| A20 | Continue | Knowledge | Continue evolution |

The wording retains the intent of the supplied 20 triplets while translating the operational meaning into enforceable engineering terms. In particular, “autopush” becomes review-gated delivery, and “apply each function to each” is constrained to compatible signatures, effects, and declared inputs.

## 3. Deterministic matrix enumeration

For a zero-based index \(k \in [0,399]\):

\[
left(k)=\lfloor k/20\rfloor+1,\quad
right(k)=(k\bmod 20)+1,\quad
sequence(k)=k+1
\]

This includes the 20 diagonal self-pairs. The orientation matters: \(T_{i,j}\) and \(T_{j,i}\) are separate descriptors. Enumeration is stable and has no side effects.

Public native C API:

- `hmga_v3_get_axioms` returns the 20 immutable triplets.
- `hmga_v3_get_operator_count` returns 400.
- `hmga_v3_get_operator` maps an index to one unique ordered pair.
- `hmga_v3_budget_for_rounds` validates a finite planning budget.

The budget is **1–64 rounds**, or at most **25,600 operator-descriptor evaluations**. A round enumerates policy descriptors; it does not invoke repository functions or create 400 patches. Invalid budgets fail closed.

## 4. Composition and function compatibility

“Apply every function to every function” is not a safe default. For a proposed composition \(f \circ g\), the planner must establish:

1. the output type and ownership/effect contract of \(g\) are accepted by \(f\);
2. input constraints, error behavior, side effects, and resource bounds compose;
3. the composition does not introduce a dependency cycle or violate module boundaries;
4. a focused positive test, negative test, and regression test exist;
5. measured benefits justify complexity when performance is claimed.

Incompatible pairs are recorded as `not-applicable`, not forced into the code. The matrix is a review cross-product, not an executable call graph.

## 5. Repository history and feature identity

The canonical baseline is the current default branch. Open PRs, stale branches, and historical commits are evidence sources, not code that should be replayed indiscriminately.

Every proposal must carry a stable feature ID and record its origin (current main, PR, branch, or issue), current implementation status, dependencies, public API/ABI impact, tests, and superseded IDs. Duplicate capabilities are consolidated only after semantic comparison. A PR branch is not assumed compatible merely because it exists.

Do not merge every historical PR into every other branch. Resolve dependencies and conflicts deliberately, then test the resulting integration as one coherent change.

## 6. Governed evolution cycle

1. **Observe:** inventory relevant C17 modules, platform support, tests, CI and current implementation evidence.
2. **Diagnose:** state one measurable defect, missing capability, or maintainability gap.
3. **Plan:** select applicable matrix operators and list incompatible or not-applicable pairs.
4. **Implement:** make one scoped, reviewable change on a dedicated branch.
5. **Verify:** run CMake, CTest, native C17 conformance tests, Python compatibility tests where configured, and focused regression checks.
6. **Evaluate:** compare correctness and resource use; performance claims require reproducible before/after measurements.
7. **Review:** open a PR with evidence, limitations, risks, and rollback instructions.
8. **Integrate:** merge only through repository policy after independent review and required checks. GitHub auto-merge may be enabled only where those gates are already enforced.
9. **Learn:** record failed hypotheses, regressions, test flakiness, and accepted/rejected changes.

## 7. Reaper/MOST product boundary

HMGA is development infrastructure for language, compiler, optimizer, runtime, standard-library, and IDE evolution. Reaper remains a standalone native C17 implementation; MOST continues to feed the canonical semantic IR. The matrix must not become a second language runtime or a Python production dependency. Any proposed language change needs a versioned grammar/semantic specification, AST/IR impact analysis, positive and negative conformance tests, differential checks, fuzz evidence, compatibility review, and rollback path.

Keep compiler passes deterministic and bounded. Do not add ambient filesystem, network, shell, process, or hardware effects to the language through a matrix operator. Generated patches remain proposals until inspected and approved. Self-hosting, native code generation, IDE services, and other roadmap items remain unimplemented until actual code and conformance evidence exist.

## 8. Non-goals and safety invariants

- No infinite loops, astronomical iteration constants, unbounded retries, or exponential push attempts.
- No direct push to `main`, force-push, branch-protection bypass, self-approval, or self-merge.
- No source execution during static review and no implicit capability or permission expansion.
- No fabricated function counts, performance gains, hardware properties, or test evidence.
- No silent rewriting of tests or weakening of CI to make a proposal green.
- Every persistent change has a reviewable diff and a revert path.

The large numeric constants in the original HMGA v3 proposal are descriptive placeholders, not runnable settings. The executable contract is the finite, deterministic 400-operator catalogue and its validated 64-round ceiling.

## 9. Verification

The HMGA CTest target verifies all 20 entries, all 400 unique ordered pairs, index boundaries, the diagonal, and valid/invalid planning budgets. Repository CI remains authoritative for native C17 and compatibility validation. A passing matrix unit test proves enumeration only; it does not certify a language transformation or replace the existing REAPER evolution evidence gate.
