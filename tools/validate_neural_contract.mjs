#!/usr/bin/env node
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const root = process.cwd();
const schema = JSON.parse(readFileSync(resolve(root, "schemas/neural-contract.v1.schema.json"), "utf8"));
const contractPath = resolve(root, "examples/neural/neural-contract.v1.json");
const contract = JSON.parse(readFileSync(contractPath, "utf8"));

function abort(message) {
  console.error("Neural Contract validation failed: " + message);
  process.exit(1);
}

function requireValue(condition, message) {
  if (!condition) throw new Error(message);
}

function validate(value) {
  requireValue(value && typeof value === "object" && !Array.isArray(value), "contract must be an object");
  requireValue(value.schema === "reaper.neural-contract/v1" && value.version === 1, "unsupported schema or version");
  requireValue(/^[a-z][a-z0-9.-]{2,95}$/.test(value.contract_id), "invalid contract_id");
  requireValue(["contract_only", "validated", "bound", "disabled"].includes(value.status), "invalid lifecycle status");

  const requiredDomains = ["model", "data", "inference", "learning", "network", "resource", "security", "governance", "verification", "cognitive"];
  requireValue(Array.isArray(value.subcontracts), "subcontracts must be an array");
  requireValue(requiredDomains.every((item) => value.subcontracts.includes(item)), "all ten contract domains must be declared");
  requireValue(new Set(value.subcontracts).size === value.subcontracts.length, "duplicate subcontract domain");

  const model = value.model;
  requireValue(model && /^[a-z][a-z0-9._-]{2,95}$/.test(model.id), "invalid model id");
  requireValue(["dense", "convolutional", "recurrent", "transformer", "graph", "hybrid"].includes(model.family), "unsupported model family");
  const artifact = model.artifact;
  requireValue(artifact && ["unbound", "bound"].includes(artifact.state), "invalid artifact state");
  if (artifact.state === "unbound") {
    requireValue(artifact.uri === null && artifact.sha256 === null, "unbound artifact must not claim a path or digest");
  } else {
    requireValue(typeof artifact.uri === "string" && artifact.uri.length > 0 && !artifact.uri.startsWith("/") && !artifact.uri.split("/").includes(".."), "bound artifact path must be relative and traversal-free");
    requireValue(typeof artifact.sha256 === "string" && /^[a-f0-9]{64}$/.test(artifact.sha256), "bound artifact requires a SHA-256 digest");
  }

  const portTypes = new Set(["bool", "i8", "u8", "i16", "u16", "i32", "u32", "i64", "u64", "f16", "f32", "f64", "token"]);
  for (const direction of ["inputs", "outputs"]) {
    const ports = value.ports?.[direction];
    requireValue(Array.isArray(ports) && ports.length > 0 && ports.length <= 64, direction + " must contain 1..64 ports");
    const ids = new Set();
    for (const port of ports) {
      requireValue(port && /^[a-z][a-z0-9._-]{2,95}$/.test(port.id), direction + " contains an invalid port id");
      requireValue(!ids.has(port.id), direction + " contains duplicate port ids");
      ids.add(port.id);
      requireValue(portTypes.has(port.dtype), "unsupported port data type: " + port.dtype);
      requireValue(Array.isArray(port.shape) && port.shape.length > 0 && port.shape.length <= 8, "port shape rank must be 1..8");
      let elements = 1;
      for (const dimension of port.shape) {
        requireValue(Number.isSafeInteger(dimension) && dimension > 0 && dimension <= 65536, "port dimensions must be bounded positive integers");
        elements *= dimension;
        requireValue(Number.isSafeInteger(elements) && elements <= 16777216, "port shape exceeds the element ceiling");
      }
      requireValue(Number.isSafeInteger(port.max_elements) && elements <= port.max_elements && port.max_elements <= 16777216, "max_elements is too small or exceeds its ceiling");
    }
  }

  const runtime = value.runtime;
  requireValue(runtime && ["reference", "local", "trusted-host", "accelerator"].includes(runtime.mode), "invalid runtime mode");
  requireValue(typeof runtime.local_only === "boolean", "runtime.local_only must be boolean");
  requireValue(["strict", "seeded", "best_effort"].includes(runtime.determinism), "invalid determinism policy");

  const resources = value.resources;
  requireValue(Number.isInteger(resources?.memory_mb) && resources.memory_mb >= 1 && resources.memory_mb <= 65536, "memory budget outside 1..65536 MiB");
  requireValue(Number.isInteger(resources?.cpu_threads) && resources.cpu_threads >= 1 && resources.cpu_threads <= 64, "CPU thread budget outside 1..64");
  requireValue(Number.isInteger(resources?.gpu_memory_mb) && resources.gpu_memory_mb >= 0 && resources.gpu_memory_mb <= 65536, "GPU memory budget outside 0..65536 MiB");
  requireValue(Number.isInteger(resources?.max_latency_ms) && resources.max_latency_ms >= 1 && resources.max_latency_ms <= 600000, "latency budget outside 1..600000 ms");
  requireValue(Number.isInteger(resources?.max_batch_items) && resources.max_batch_items >= 1 && resources.max_batch_items <= 4096, "batch budget outside 1..4096");

  const security = value.security;
  requireValue(security && ["deny", "allowlisted"].includes(security.external_transfer), "invalid external transfer policy");
  requireValue(security.telemetry === "disabled" && security.secrets === "deny", "telemetry and secret access must remain disabled");
  requireValue(["none", "model-read-only"].includes(security.filesystem), "filesystem access must be none or model-read-only");
  requireValue(["disabled", "allowlisted"].includes(security.network), "network policy must be disabled or allowlisted");

  const learning = value.learning;
  requireValue(learning && ["disabled", "offline", "federated"].includes(learning.mode), "invalid learning mode");
  requireValue(learning.online_learning === false && learning.manual_approval_required === true, "online learning is prohibited and manual approval is mandatory");
  requireValue(Number.isInteger(learning.max_steps) && learning.max_steps >= 0 && learning.max_steps <= 10000000, "training step budget out of range");
  requireValue(Array.isArray(learning.datasets) && learning.datasets.length <= 128, "datasets must be a bounded array");
  if (learning.mode === "disabled") requireValue(learning.max_steps === 0 && learning.datasets.length === 0, "disabled learning cannot declare datasets or training steps");
  if (learning.mode !== "disabled") {
    requireValue(learning.max_steps > 0 && learning.datasets.length > 0, "enabled learning requires a bounded step budget and datasets");
    const datasetIds = new Set();
    for (const dataset of learning.datasets) {
      requireValue(dataset && /^[a-z][a-z0-9._-]{2,95}$/.test(dataset.id), "invalid dataset id");
      requireValue(typeof dataset.consent_ref === "string" && dataset.consent_ref.length >= 3, "dataset consent reference is required");
      requireValue(!datasetIds.has(dataset.id), "duplicate dataset id");
      datasetIds.add(dataset.id);
    }
  }

  const topology = value.topology;
  requireValue(topology && ["isolated", "mesh", "federated"].includes(topology.mode), "invalid topology");
  requireValue(Array.isArray(topology.peers) && topology.peers.length <= 64, "peer list must be bounded");
  if (topology.mode === "isolated") {
    requireValue(topology.peers.length === 0 && security.network === "disabled" && security.external_transfer === "deny" && runtime.local_only, "isolated topology must have no peers or network transfer");
  } else {
    requireValue(topology.peers.length > 0 && security.network === "allowlisted" && runtime.local_only === false, "distributed topology requires allowlisted peers and a host adapter");
    const peerIds = new Set();
    for (const peer of topology.peers) {
      requireValue(peer && /^[a-z][a-z0-9.-]{2,95}$/.test(peer.id), "invalid peer id");
      requireValue(peer.authenticated === true && peer.encrypted === true && peer.allowlisted === true, "every peer must be authenticated, encrypted and allowlisted");
      requireValue(Number.isInteger(peer.max_payload_bytes) && peer.max_payload_bytes >= 1 && peer.max_payload_bytes <= 1048576, "peer payload limit exceeds 1 MiB");
      requireValue(!peerIds.has(peer.id), "duplicate peer id");
      peerIds.add(peer.id);
    }
  }
  if (learning.mode === "federated") requireValue(topology.mode === "federated", "federated learning requires federated topology");

  const behavior = value.behavior;
  requireValue(behavior && typeof behavior.task === "string" && typeof behavior.output_contract === "string", "behavior contract is incomplete");
  requireValue(["required", "allowed", "disabled"].includes(behavior.uncertainty_policy), "invalid uncertainty policy");
  requireValue(Number.isInteger(behavior.min_confidence_ppm) && behavior.min_confidence_ppm >= 0 && behavior.min_confidence_ppm <= 1000000, "confidence floor must be in ppm");
  requireValue(Number.isInteger(behavior.max_invalid_output_ppm) && behavior.max_invalid_output_ppm >= 0 && behavior.max_invalid_output_ppm <= 1000000, "invalid-output ceiling must be in ppm");

  const lifecycle = value.lifecycle;
  requireValue(lifecycle && lifecycle.state === value.status, "top-level status and lifecycle state must agree");
  requireValue(Number.isInteger(lifecycle.revision) && lifecycle.revision >= 0, "lifecycle revision must be non-negative");
  requireValue(lifecycle.update_policy === "manual_only" && lifecycle.rollback_required === true, "model updates must be manual and rollback-capable");

  const provenance = value.provenance;
  requireValue(provenance && typeof provenance.license === "string" && provenance.license.length >= 3, "license provenance is required");
  requireValue(["authored_specification", "trained", "converted", "third_party"].includes(provenance.model_source), "invalid model source");
  requireValue(Array.isArray(provenance.dataset_ids), "provenance dataset_ids must be an array");
  if (provenance.dataset_digest !== null) requireValue(/^[a-f0-9]{64}$/.test(provenance.dataset_digest), "dataset digest must be SHA-256");
  if (learning.mode === "disabled") requireValue(provenance.dataset_ids.length === 0 && provenance.dataset_digest === null && provenance.training_run_id === null, "untrained contract cannot claim training provenance");
  return true;
}

try {
  requireValue(schema.$schema === "https://json-schema.org/draft/2020-12/schema", "schema must use JSON Schema 2020-12");
  requireValue(schema.properties?.schema?.const === "reaper.neural-contract/v1", "schema identity mismatch");
  validate(contract);
} catch (error) {
  abort(error.message);
}

// Guardrail regression cases: the validator must reject unsafe mutations.
const rejectionCases = [
  ["telemetry", (copy) => { copy.security.telemetry = "enabled"; }],
  ["online-learning", (copy) => { copy.learning.online_learning = true; }],
  ["duplicate-port", (copy) => { copy.ports.inputs.push({ ...copy.ports.inputs[0] }); }],
  ["open-network-on-isolated", (copy) => { copy.security.network = "allowlisted"; }],
  ["automatic-update", (copy) => { copy.lifecycle.update_policy = "automatic"; }],
];
for (const [name, mutate] of rejectionCases) {
  const copy = structuredClone(contract);
  mutate(copy);
  let rejected = false;
  try { validate(copy); } catch { rejected = true; }
  if (!rejected) abort("negative fixture was not rejected: " + name);
}

console.log("REAPER_NEURAL_CONTRACT_SCHEMA_OK");
console.log("REAPER_NEURAL_CONTRACT_POLICY_OK");
console.log("REAPER_NEURAL_CONTRACT_NEGATIVE_CASES_OK:" + rejectionCases.length);
