# Reaper gaming task-plan contract

**Project author/developer:** Ivan-VHS

Reaper provides a bounded, declarative scheduler-hint adapter for DuckOS game sessions. It translates a validated session profile into role records for the main loop, render loop, audio period, worker pool and deferred background work.

## Contract

Input schema: `duckos.gaming-session-profile.v1`. Output schema: `reaper.gaming-task-plan.v1`.

The plan carries relative role weights, deadline classes, migration hints and the source DuckOS rules (GPR-13…GPR-24). It does not translate those hints into native Windows/Linux scheduling classes because that translation belongs to an authenticated DuckOS executor with measured CPU topology and explicit policy.

## Safety

The adapter never creates threads or processes, changes scheduling priority, sets CPU affinity, changes timer resolution, adjusts CPU frequency or touches driver/interrupt settings. Its output explicitly reports `execution_performed=false` and requires a trusted host executor.

## Verification

```sh
python -m unittest tests.test_gaming_policy_contract -v
```


## Sequential rollout

Rollout gate: this PR stays in draft until DuckOS #75, OPlague #166 and Pytyliki #213 are merged. Then it is the fourth stage of the gaming-policy rollout.
