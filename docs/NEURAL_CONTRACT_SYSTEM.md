# Neural Contract System v1

**Status:** Reaper-source policy model and versioned JSON contract implemented for the Python reference runtime; native C17 parity and model execution are not implemented.  
**Canonical module:** `stdlib/neural_contract.rpr`  
**Executable fixture:** `examples/neural_contract_system.rpr`  
**Machine-readable schema:** `schemas/neural-contract.v1.schema.json`  
**Contract example:** `examples/neural/neural-contract.v1.json`

## Purpose and naming

The **Neural Contract System (NCS)** is Reaper's versioned agreement layer for model identity, tensor/data interfaces, inference admission, learning authorization, network topology, resource ceilings, security, provenance, lifecycle and output behavior.

The many requested names describe one architecture rather than nineteen competing frameworks:

| Term family | Canonical NCS domain |
|---|---|
| Artificial neural network, neural model, machine model, generative model | Model contract |
| Neural contract, neural agreement, digital neuro-contract, machine neuro-agreement | Versioned contract envelope |
| Network neural contract, distributed or decentralized neuro-contract | Peer and federation contract |
| Cognitive contract, intelligent agreement, programmable neuro-contract | Behavior and output contract |
| System design, system construction, system programming, systems engineering | Architecture and runtime contract |
| Adaptive, self-learning or autonomous model | Explicit learning and lifecycle policy |

NCS owns the contract semantics. It does not claim that a model is intelligent, autonomous, trained or operational merely because a contract exists.

## Architecture

The contract is divided into ten independently reviewable domains:

1. **Model:** stable model identity, family, task and artifact binding.
2. **Data:** typed input/output ports, shape bounds and maximum element counts.
3. **Inference:** request admission, batch limits and deadline ceilings.
4. **Learning:** disabled/offline/federated learning modes, dataset declarations, consent references, step budgets and mandatory operator approval.
5. **Network:** isolated, allowlisted mesh or federated topology, authenticated peers, encryption and payload limits.
6. **Resource:** memory, CPU threads, GPU memory, latency and batch ceilings.
7. **Security:** deny-by-default external transfer, disabled telemetry, denied secret access and narrow filesystem access.
8. **Governance:** immutable contract identity, revision, manual updates and rollback requirements.
9. **Verification:** schema checks, deterministic policy fixtures, positive/negative admission tests and provenance.
10. **Cognitive behavior:** task/output contract, uncertainty policy, confidence floor and invalid-output ceiling.

The dependency direction is explicit:

`dataset provenance → typed data ports → model artifact → runtime adapter → inference/learning admission → output contract → audit`

The contract graph must remain acyclic. A runtime adapter cannot silently grant a capability that the contract did not declare.

## Canonical versioned interfaces

### JSON contract

The authoritative interchange format is `reaper.neural-contract/v1`. The JSON Schema uses Draft 2020-12 and rejects undeclared fields. The checked-in example is intentionally `contract_only`: it has no model weights, no artifact path and no model digest. It is a valid example of a contract, not a runnable neural model.

For a bound artifact:

- the artifact path is relative to an operator-controlled model store;
- traversal and absolute paths are rejected;
- the model artifact must have a SHA-256 digest;
- provenance must identify source and license;
- the loader must verify the digest and the artifact format before use.

A schema-valid manifest is not proof that the artifact is safe, correct or compatible. Runtime loading remains a separate, explicit host operation.

### Reaper reference module

`stdlib/neural_contract.rpr` uses the existing Reaper grammar, ordinary list records and exported `craft` functions. It does not add parser keywords or a second interpreter.

The fixed 14-slot in-memory record is:

| Slot | Value |
|---:|---|
| 0–1 | Contract magic and version |
| 2–3 | Model identifier and family |
| 4–5 | Typed input and output ports |
| 6 | Resource envelope: memory MiB, CPU threads, GPU MiB, maximum latency ms, maximum batch items |
| 7 | Security: transfer allowed, telemetry, secrets, filesystem, network policy |
| 8 | Learning: mode, online flag, manual approval, step ceiling, dataset IDs, consent reference |
| 9 | Topology: mode and peer records |
| 10 | Runtime adapter, version, mode, deterministic flag and local-only flag |
| 11 | Artifact/provenance binding and license |
| 12 | Lifecycle state, revision, update policy and rollback requirement |
| 13 | Task, output contract, uncertainty policy, confidence floor and invalid-output ceiling |

A port record is `[id, direction, dtype, shape, max_elements]`. A peer record is `[id, authenticated, encrypted, allowlisted, max_payload_bytes]`.

The exported policy surface is:

| API | Contract |
|---|---|
| `port`, `peer`, `contract` | Construct canonical descriptors |
| `validate` | Validate record structure and cross-domain invariants |
| `inference_admit` | Decide whether a bounded inference request is permitted |
| `training_admit` | Require declared data, verified consent and operator approval |
| `peer_exchange_admit` | Check allowlisted peer and bounded payload before host networking |
| `update_admit` | Require bound artifact, trusted signature, operator approval and rollback readiness |
| `output_accept` | Check output size, invalid-output rate and uncertainty threshold |

The APIs return decisions and diagnostics. They do not load tensors, call an inference engine, open a socket, write an artifact or train a model.

## Security and trust policy

Defaults are deliberately restrictive:

- Model execution is local and isolated unless a reviewed host adapter is selected.
- External transfer, telemetry and access to secrets are denied by default.
- A distributed topology must name every peer; every peer must be authenticated, encrypted and allowlisted.
- Online learning is prohibited. Offline/federated learning requires a declared dataset, a consent reference, a finite step ceiling and explicit operator approval.
- Model updates are manual-only. A candidate must be signature-verified, approved and paired with a verified rollback target.
- Model files are read-only to inference. A model cannot grant itself filesystem, process, network, clock, shell, driver or hardware privileges.
- Logs should record stable contract IDs and redacted diagnostics, never prompts, source data, secrets or raw tensors by default.

The Reaper policy functions are not an OS sandbox, cryptographic verifier, access-control enforcement point or network firewall. Those controls belong to the host runtime and must be independently enforced there.

## Runtime and learning lifecycle

The supported contract states are:

`contract_only → validated → bound → disabled`

Transitions are revisioned. The current reference module validates lifecycle shape and only admits updates under the manual-only policy. It does not activate a new artifact.

Inference admission checks the contract, lifecycle, batch size, deadline and transfer request. It returns `admit` or `deny`; an adapter may execute only after independently enforcing the same limits.

Training admission requires all of the following:

1. learning mode is `offline` or `federated`;
2. the dataset ID is declared;
3. the consent reference matches and is verified by the host;
4. the operator explicitly approves the run;
5. requested steps stay within the declared ceiling.

The Reaper library checks the supplied consent-verification result; it does not establish legal consent or inspect the dataset itself.

## Reaper example

```reaper
import "../stdlib/neural_contract.rpr" as ncs

make input := ncs["port"]("features", "input", "f32", [128], 128)
make output := ncs["port"]("scores", "output", "f32", [4], 4)

make model := ncs["contract"](
    "example.local-classifier", "dense",
    [input], [output],
    [512, 2, 0, 25, 8],
    [false, false, false, "none", "none"],
    ["disabled", false, true, 0, [], ""],
    ["isolated", []],
    ["reference.cpu", "1.0.0", "reference", true, true],
    ["unbound", "", "", "", "Apache-2.0"],
    ["contract_only", 0, "manual_only", true],
    ["multiclass-classification", "scores.v1", "required", 750000, 1000]
)

make validation := ncs["validate"](model)
assert(validation[0], "neural contract must validate")
```

Run the executable policy fixture:

```sh
python -m reaper --check examples/neural_contract_system.rpr
python -m reaper examples/neural_contract_system.rpr
python -m reaper --engine vm examples/neural_contract_system.rpr
node tools/validate_neural_contract.mjs
```

The CLI commands execute Reaper source through the current reference runtime/VM. They do not execute a neural network.

## Integration boundaries

| Project/layer | Ownership |
|---|---|
| Reaper | Canonical contract schema, policy semantics, source locations, diagnostics and future typed IR lowering |
| Duck OS | Future host-owned process/runtime adapter, resource enforcement, storage and capabilities; no privileges are granted by a Reaper manifest |
| Pytyliki | Future explicit hardware/accelerator observation and ABI evidence; it does not own model data consent or learning policy |
| V.E.R.S.E. / RFS-01 | May become an expressive composition profile over the same Reaper contract values; it does not get a second model registry, type system or runtime |

Cross-project adapters remain planned until their own versioned interfaces, security review, implementation and integration tests exist.

## Maturity and non-goals

| Capability | Status |
|---|---|
| Versioned neural contract schema and checked example | Implemented |
| Reaper-source record constructors and policy validation | Implemented in reference runtime |
| Inference/training/network/update admission decisions | Implemented as policy checks only |
| JSON semantic guardrail and negative fixtures | Implemented |
| Tree-walk and bytecode-VM fixture execution | CI-gated |
| Actual model loading and inference backend | Not implemented |
| Model training or federated optimizer | Not implemented |
| Network transport, encryption and peer authentication | Not implemented by this module |
| Native C17 compiler/runtime parity | Not implemented |
| Duck and Pytyliki adapters | Planned, separate contracts required |

Do not mark an end-to-end neural capability delivered until a real adapter exists and passes artifact integrity, model-format compatibility, output correctness, bounded-resource, privacy, isolation, determinism and rollback tests.
