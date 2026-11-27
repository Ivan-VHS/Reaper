# Early mathematics as executable invariants

This example connects Reaper's existing bounded collection operations to the mathematical ideas behind early quantity play. It is a language conformance example, not a child-facing application or a claim about developmental assessment.

## Formal ideas

- **Cardinality:** the number of members in a finite collection is its size, independent of order or spatial arrangement.
- **One-to-one correspondence:** pair one item from each collection exactly once. Equal sizes are necessary for a bijection, but the actual pairing must still be performed and checked.
- **Partition conservation:** for disjoint groups that cover the original collection, the sum of group sizes equals the original size.
- **Balanced sharing:** when indivisible objects are distributed among non-empty groups, the largest and smallest portions differ by at most one.
- **Number composition:** two non-negative parts compose a target when their sum equals it.

The Reaper runtime already provides bounded `size`, `partition`, `distribute`, `flatten`, `sorted`, `reverse`, `first`, `map` and `sum` operations. The example composes those operations; it does not add new runtime semantics.

## Example coverage

`examples/early_math.rpr` checks that rearranging five objects preserves cardinality, partitioning five toys into three groups loses no objects, a 10-to-3 distribution is `[4, 3, 3]`, twelve objects can be shared equally by three groups, and alternate pairs compose five and ten.

The balanced-distribution invariant is:

- sum(shares) equals the original number of objects;
- max(shares) minus min(shares) is at most one.

Here, n is the number of indivisible objects and k is a positive group count.

## Scope and safety

All operations are deterministic and resource-bounded by the interpreter's collection and execution limits. The example performs no filesystem, network, process, device or audio actions. It contains no child profiles, scoring, timers or learning analytics. In teaching, actual object pairing and adult conversation remain more important than a computed result.
