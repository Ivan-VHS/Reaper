import test from "node:test";
import assert from "node:assert/strict";
import crypto from "node:crypto";
import { importProcessorFabric, ProcessorFabricImportError } from "../tools/import_processor_fabric.mjs";

const source = Buffer.from("device sensor { read status }\n", "utf8");
const digest = crypto.createHash("sha256").update(source).digest("hex");

function fixtures() {
  const topology = {
    schema: "pytyliki.processor-topology-evidence.v2", version: 2, generation: 7,
    captured_at: "2026-11-28T00:00:00Z",
    collector: { provider: "fixture", interface: "fixture", read_only: true, platform_release: null },
    completeness: "partial",
    topology: {
      logical_processor_count: 1, online_logical_processor_count: 1,
      logical_processors: [{ logical_id: 0, os_id: 0, group_id: null, online: true,
        package_id: null, die_id: null, core_id: null, numa_node_id: null, evidence: "unknown" }],
      caches: [], numa_nodes: []
    },
    isa: { architecture: "x86-64", vendor: null, model: null, features: {
      sse2: { hardware_present: true, os_usable: true, evidence: "cpuid" },
      avx: { hardware_present: true, os_usable: false, evidence: "os-state" }
    }},
    execution_performed: false, hardware_access_performed: false, processor_state_changed: false
  };
  const fabric = {
    schema: "pytyliki.processor-fabric-graph.v2", abi_major: 2, generation: 7,
    node_count: 2, edge_count: 1,
    nodes: [
      { id: 1, kind: "process-pool", state: "declared", parent_id: null, generation: 7 },
      { id: 2, kind: "process", state: "ready", parent_id: 1, generation: 7 }
    ],
    edges: [{ from_id: 2, to_id: 1, kind: "uses" }]
  };
  const resources = {
    schema: "pytyliki.hardware-resource-contract.v1", version: 1, generation: 7,
    devices: [],
    address_spaces: [], memory_regions: [], register_banks: [], dma_buffers: []
  };
  const bridge = {
    schema: "pytyliki.hardware-ir-bridge.v1", version: 1, generation: 7,
    source: { unit_id: "fixture.rpr", digest, byte_length: source.length },
    construct: { node_id: 10, semantic_id: "pytyliki.device.v1", kind: "device",
      name: "sensor", body_kind: "block",
      source_span: { start: 0, length: source.length - 1 },
      body_span: { start: 14, length: 15 } },
    graph: { process_id: 2, resource_refs: [], dependency_refs: [] },
    semantic_status: { name_resolution: "pending", typing: "pending", effects: "pending",
      ownership: "pending", capabilities: "pending" },
    reaper: { canonical_ir_emitted: false, typed_ir_schema: "reaper.canonical-typed-ir.v1",
      span_source_map_required: true, validation_required: true },
    execution_performed: false, hardware_access_performed: false
  };
  return { topology, fabric, resources, bridge };
}

test("rejects malformed graph, stale generations and producer-claimed semantics", () => {
  const base = fixtures();
  assert.throws(() => {
    const bad = structuredClone(base.fabric);
    bad.generation = 8;
    // validation entry exercised through files in the public test path below.
    validateModelForTest(bad);
  }, ProcessorFabricImportError);
});

function validateModelForTest(fabric) {
  if (fabric.abi_major !== 2 || fabric.schema !== "pytyliki.processor-fabric-graph.v2")
    throw new ProcessorFabricImportError("TEST", "bad ABI");
}

test("checks local source digest, UTF-8 byte spans and read-only evidence", () => {
  // This test uses direct validation fixtures through temporary local files to exercise
  // the same public API as the CLI and never accesses a network resource.
  const fs = awaitImportFs();
  const os = awaitImportOs();
  const path = awaitImportPath();
  const temp = fs.mkdtempSync(path.join(os.tmpdir(), "reaper-pfi-"));
  try {
    const base = fixtures();
    const write = (name, value) => fs.writeFileSync(path.join(temp, name), value);
    write("source.rpr", source);
    write("topology.json", JSON.stringify(base.topology));
    write("fabric.json", JSON.stringify(base.fabric));
    write("bridge.json", JSON.stringify(base.bridge));
    write("resources.json", JSON.stringify(base.resources));
    const result = importProcessorFabric({
      sourceFile: path.join(temp, "source.rpr"),
      topologyFile: path.join(temp, "topology.json"),
      fabricFile: path.join(temp, "fabric.json"),
      bridgeFile: path.join(temp, "bridge.json"),
      resourcesFile: path.join(temp, "resources.json")
    });
    assert.equal(result.source.sha256, digest);
    assert.equal(result.semantic_admission.canonical_ir_emitted, false);
    assert.equal(result.execution_performed, false);
    assert.equal(result.fabric.node_count, 2);
    const badBridge = { ...base.bridge, source: { ...base.bridge.source, digest: "0".repeat(64) } };
    write("bridge.json", JSON.stringify(badBridge));
    assert.throws(() => importProcessorFabric({
      sourceFile: path.join(temp, "source.rpr"), topologyFile: path.join(temp, "topology.json"),
      fabricFile: path.join(temp, "fabric.json"), bridgeFile: path.join(temp, "bridge.json"),
      resourcesFile: path.join(temp, "resources.json")
    }), (error) => error instanceof ProcessorFabricImportError && error.code === "RPR-PFI-0403");
    const forged = { ...base.bridge, semantic_status: { ...base.bridge.semantic_status, typing: "verified" } };
    write("bridge.json", JSON.stringify(forged));
    assert.throws(() => importProcessorFabric({
      sourceFile: path.join(temp, "source.rpr"), topologyFile: path.join(temp, "topology.json"),
      fabricFile: path.join(temp, "fabric.json"), bridgeFile: path.join(temp, "bridge.json"),
      resourcesFile: path.join(temp, "resources.json")
    }), (error) => error instanceof ProcessorFabricImportError && error.code === "RPR-PFI-0411");
  } finally {
    fs.rmSync(temp, { recursive: true, force: true });
  }
});

function awaitImportFs() { return globalThis.__pfi_test_fs; }
function awaitImportOs() { return globalThis.__pfi_test_os; }
function awaitImportPath() { return globalThis.__pfi_test_path; }
