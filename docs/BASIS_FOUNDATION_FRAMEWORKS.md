# Basis and Foundation Frameworks — batches 06–07

## Basis (06)

- Integer Range: exact signed/unsigned fixed-width bounds for 8/16/32/64/128-bit integers.
- Checked Addition: arithmetic that rejects values outside the declared width.
- Checked Multiplication: arithmetic that rejects values outside the declared width.
- Ratio: reduce integer fractions with the Euclidean GCD and a positive denominator.
- Alignment: align addresses upward to power-of-two boundaries within the 64-bit address space.

## Foundation (07)

- Boot Order: validate a supplied permutation against prerequisite edges.
- Bootstrap Order: compute a deterministic topological order; cycles or malformed edges return an empty result.
- Preflight: validate named boolean checks and enforce a minimum passing count.
- Rollback: reverse a unique completed-step journal into compensation order.
- Checkpoint: select the newest valid checkpoint from a validated checkpoint journal.

All modules are independent Reaper `.rpr` sources. They are deterministic and operate only on passed values; they do not allocate physical memory, run a boot sequence, mutate host state or perform actual recovery.
