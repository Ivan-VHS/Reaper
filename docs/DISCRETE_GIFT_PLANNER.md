# Discrete Gift Planner

Reaper exposes a deterministic Python reference API for allocating a finite integer budget, selecting a stock-limited candy basket, counting combinations and routing greeting templates.

## API

```python
from reaper import Candy, plan_gift

catalog = (
    Candy("Praline", "chocolate", price=18, stock=30, preference=5, weight_grams=14),
    Candy("Fruit caramel", "caramel", price=8, stock=40, preference=2, weight_grams=10),
)
plan = plan_gift(500, 5, catalog, ("Happy day!", "Best wishes!"))
assert plan.verify()
```

- `allocate_equal` assigns exact integer shares and gives remainder units to earlier recipients.
- `allocate_weighted` uses the largest-remainder method with stable index tie-breaking.
- `percent_of` and `combination_count` use exact integer arithmetic.
- `build_candy_basket` respects prices, stock and budget. It orders items by preference/price and is intentionally a heuristic, not an optimal knapsack claim.
- `build_greeting_graph` creates directed sender-to-recipient links and rotates greeting-template indexes deterministically.
- `plan_gift` combines allocations, stock-aware baskets and greeting edges, then verifies budget conservation.

## Run

```sh
python -m reaper.gift_planner --budget 500 --recipients 5 --senders 1
python -m unittest tests.test_gift_planner -v
```

The planner performs no network requests and does not purchase goods. Currency units are caller-defined integers; use whole UAH or kopiykas consistently.
