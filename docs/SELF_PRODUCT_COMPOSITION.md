# Self-product composition

`reaper.self_product` provides deterministic, bounded repeated transformation passes.

| Rule | Contract |
|---|---|
| Input | explicit function and immutable seed value |
| Iteration | finite pass count |
| Result | ordered trace + final value |
| Safety | no implicit file, network or process effects |
| Verification | tests for identity, order and limit failures |

Repeated composition does not grant autonomous repository modification or merge authority.
