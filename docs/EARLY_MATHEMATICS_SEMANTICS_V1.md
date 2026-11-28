# Early Mathematics Semantics v1

**Status:** specified; no new runtime primitive is claimed by this document.  
**Ownership:** Reaper owns exact mathematical semantics. DAK owns child-facing curriculum and activity delivery.

## 1. Scope

The early-mathematics domain must be represented without conflating a written numeral, an ordinal position, a cardinal quantity, a container, or a measurement. The model is age-neutral: pedagogy may select an activity for a learner, but age metadata must never alter mathematical truth or runtime semantics.

The canonical learning progression is external to the language runtime:

**object action → observation → verbal relation → model → symbol**.

Reaper provides deterministic representations and checked operations for the model stage. It does not diagnose development or decide when a child is ready for abstraction.

## 2. Core semantic distinctions

| Concept | Formal meaning | Required invariant |
|---|---|---|
| Cardinality | size of a finite collection | a non-negative integer; zero is a valid value |
| Ordinal | position in an ordered sequence | position is interpreted relative to a sequence and its indexing convention |
| Numeral | a token that denotes a number | parsing a glyph does not create or prove a corresponding collection |
| Collection | finite set, multiset or sequence | the collection kind is explicit |
| Measurement | magnitude together with a unit and dimension | unlike dimensions cannot be compared directly |
| Fraction | exact relation between integer numerator and non-zero denominator | canonical sign and reduction rules are explicit |
| Pattern | finite sequence plus a stated repetition or transformation rule | a prefix alone does not prove one unique generating rule |
| Duration | non-negative or signed time interval, depending on the operation | distinct from a wall-clock timestamp |

A value of cardinality zero is not the same thing as a missing value, an invalid value, a null reference or an empty string. A numeral such as 4 is a representation; four objects are a collection whose cardinality is four.

## 3. Collections and counting

The semantic model distinguishes:

- **Finite set:** each element is unique; cardinality counts unique membership.
- **Multiset:** repeated equal values are retained with multiplicity.
- **Sequence:** element order is meaningful; length and element positions are separate properties.

For a finite sequence \(S\), length returns its cardinality and an ordinal lookup selects an element under an explicit zero-based or one-based convention. The public API must never silently mix these conventions.

Counting a collection requires a one-to-one correspondence between visited elements and count steps. Reordering a sequence preserves its cardinality. A bijection between finite sets preserves cardinality. Duplicating an element in a multiset changes its multiplicity and must not be treated as a no-op.

### Required invariants

1. Cardinalities are non-negative and checked for overflow.
2. Reordering, spacing, rotating or regrouping a collection does not change cardinality.
3. Adding a distinct element increases set cardinality by one; adding a repeated value to a multiset increases its multiplicity.
4. A disjoint partition preserves the whole: the sum of part cardinalities equals the whole cardinality.
5. Overlapping parts require an explicit intersection rule; naïvely adding their cardinalities can double-count elements.
6. Counting order does not change the final cardinality, provided every element is visited exactly once.

## 4. Arithmetic and part–whole relationships

Addition models combination of disjoint quantities or a change in quantity. Subtraction models removal or a difference under a defined domain. Equal sharing is a partition operation, not an implicit integer division that silently discards a remainder.

For non-negative integer quantities:

- Addition is valid only when the result is representable.
- Subtraction must define whether negative results are allowed or return a domain error.
- The equation \(a=b+c\) expresses a decomposition into parts.
- Equal sharing of \(n\) items among \(k\) recipients returns quotient and remainder or an explicit equal-partition error; it must not conceal leftovers.

Commutativity applies to addition of the same numeric domain, but not to sequence concatenation. The implementation must attach algebraic laws to the correct operation rather than infer them from surface syntax.

## 5. Exact fractions and measures

Fractions used for halves, quarters and equal sharing should be exact rational values, not binary floating-point approximations.

Canonical rational form:

\[
q = \frac{n}{d}, \quad d > 0, \quad \gcd(|n|,d)=1
\]

A zero denominator is rejected. Sign normalization and reduction are deterministic. If an intermediate numerator or denominator cannot be represented in the selected bounded integer width, return an overflow error rather than wrap or silently round.

A measure consists of a magnitude, a unit identifier and a physical dimension. Unit conversion is explicit and exact where the conversion ratio is rational. Length may be expressed in metres, centimetres or an explicitly declared non-standard measure such as a block or hand span. Values from different dimensions are not directly comparable.

## 6. Geometry and spatial relations

The model distinguishes:

- 2D shapes and their boundaries;
- 3D solids and their surfaces;
- points, vectors and coordinate frames;
- shape identity from orientation, position, scale and material appearance.

Rotation or translation preserves shape identity and relevant dimensions. Scaling changes dimensions according to the declared transformation. A triangle is not defined by one canonical visual orientation. A shape classifier must not reject a valid rotated or differently proportioned instance merely because it differs from a familiar icon.

Spatial relations such as inside, outside, above, below, left-of, right-of and between require a reference frame where that frame affects interpretation. Left and right are not absolute without an observer or coordinate convention.

## 7. Patterns and logic

A pattern representation contains:

- a finite observed sequence;
- a candidate rule or a set of candidate rules;
- the domain of its symbols;
- a bounded prefix length and evaluation budget.

ABAB, AAB and ABC patterns can be represented as periodic sequences. Growing patterns such as 1, 2, 3, 4 need an explicit transition rule such as “add one”. A finite prefix may admit multiple rules; the model must not report a rule as uniquely proven merely because it fits the visible prefix.

“Find the odd one out” tasks may have multiple valid answers when the criterion is under-specified. The evaluator should accept a supported criterion and a coherent explanation, not a single hidden answer key.

## 8. Time and order

A temporal sequence, a duration and a calendar label are distinct. “Before” and “after” are ordering relations. “Fast” and “slow” require a comparable duration or rate under a shared task definition. A day part or weekday is a human calendar concept, not a fixed elapsed-time unit.

## 9. Determinism, bounds and diagnostics

- Every public operation defines input domain, output domain, complexity bound and failure behavior.
- Integer arithmetic is checked; no wraparound is permitted in semantic quantity operations.
- Exact rational operations report overflow instead of silently changing precision.
- Collections and pattern evaluation have explicit item and step budgets.
- Serialization records the semantic kind, numeric width, unit identity and version; it does not infer them from display text.
- Unknown schema versions and unknown unit identifiers fail closed.
- Failure results use Reaper's existing result/error conventions; no new diagnostic identifier is considered registered until the diagnostic catalogue and tests include it.

Potential diagnostic families for future registration include invalid denominator, dimension mismatch, cardinality overflow, ambiguous indexing and unbounded pattern evaluation.

## 10. Conformance suite required before implementation is marked complete

| Area | Positive cases | Negative and invariant cases |
|---|---|---|
| Cardinality | empty and non-empty collections | negative value, overflow, missing versus zero |
| Counting | stable count after reorder | duplicated or skipped visit |
| Part–whole | disjoint partitions | overlapping parts, hidden remainder |
| Rational | reduced halves and quarters | zero denominator, sign drift, overflow |
| Measurement | exact conversion within one dimension | dimension mismatch, unknown unit |
| Geometry | rotated and translated shapes | invalid coordinates, frame mismatch |
| Pattern | AB, AAB, ABC, growth rule | ambiguous prefix, budget exhaustion |
| Serialization | deterministic round trip | unknown version, lost unit identity |

Tests must cover reference-runtime behavior and native conformance separately. A Python reference implementation passing tests does not prove native compiler, VM or Duck ABI parity.

## 11. Federation boundary

- DAK publishes declarative, localized learning activities and owns child-facing copy, accessibility and safety policy.
- Reaper owns mathematical types, invariants and deterministic arithmetic semantics.
- Pytyliki may provide an optional bounded native compute adapter; it is not a required runtime dependency.
- OPlague may provide read-only package inspection; its verdict is not a pedagogical or developmental assessment.
- VentuSample may generate offline rhythm examples; audio timing does not replace exact number semantics.

No peer repository code is loaded implicitly. Interoperability requires an explicit versioned contract and an opt-in adapter.
