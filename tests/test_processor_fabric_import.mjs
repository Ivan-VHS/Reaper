import test from "node:test";
import assert from "node:assert/strict";
import crypto from "node:crypto";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

import {
  importProcessorFabric,
  ProcessorFabricImportError
} from "../tools/import_processor_fabric.mjs";

const source = Buffer.from("device café { read status }\n", "utf8");
const digest = crypto.createHash("sha256").update(source).digest("hex");
const bodyStart = source.indexOf(Buffer.from("{"));
const bodyLength = Buffer.byteLength("{ read status }", "utf8");

function fixtures() {
  const topology = {
    schema: "pytyliki.processor-topology-evidence.v2",
    version: 2,
    generation: 7,
    captured_at: "2026-11-28T00:00:00Z",
    collector: {
      provider: "fixture",
      interface: "fixture",
      read_only: true,
      platform_release: null
    },
    completeness: "partial",
    topology: {
      logical_processor_count: 1,
      online_logical_processor_count: 1,
      logical_processors: [{
        logical_id: 0, os_id: 0, group_id: null, online: true,
        package_id: null, die_id: null, core_id: null, numa_node_id: null,
        evidence: "unknown"
      }],
      caches: [],
      numa_nodes: []
    },
    isa: {
      architecture: "x86-64",
      vendor: null,
      model: null,
      features: {
        sse2: { hardware_present: true, os_usable: true, evidence: "cpuid" },
        avx: { hardware_present: true, os_usable: false, evidence: "os-state" }
      }
    },
    execution_performed: false,
    hardware_access_performed: false,
    processor_state_changed: false
  };
  const fabric = {
    schema: "pytyliki.processor-fabric-graph.v2",
    abi_major: 2,
    generation: 7,
    node_count: 3,
    edge_count: 1,
    nodes: [
      { id: 1, kind: "process-pool", state: "declared", parent_id: null, generation: 7 },
      { id: 2, kind: "process", state: "ready", parent_id: 1, generation: 7 },
      { id: 3, kind: "device", state: "declared", parent_id: null, generation: 7,
        semantic_ref: "sensor-device" }
    ],
    edges: [{ from_id: 2, to_id: 3, kind: "uses" }]
  };
  const resources = {
    schema: "pytyliki.hardware-resource-contract.v1",
    version: 1,
    generation: 7,
    devices: [{ id: "sensor-device", generation: 7 }],
    address_spaces: [],
    memory_regions: [],
    register_banks: [],
    dma_buffers: []
  };
  const bridge = {
    schema: "pytyliki.hardware-ir-bridge.v1",
    version: 1,
    generation: 7,
    source: {
      unit_id: "fixture.rpr",
      digest,
      byte_length: source.length
    },
    construct: {
      node_id: 10,
      semantic_id: "pytyliki.device.v1",
      kind: "device",
      name: "café",
      body_kind: "block",
      source_span: { start: 0, length: source.length - 1 },
      body_span: { start: bodyStart, length: bodyLength }
    },
    graph: {
      process_id: 2,
      resource_refs: [3],
      dependency_refs: []
    },
    semantic_status: {
      name_resolution: "pending",
      typing: "pending",
      effects: "pending",
      ownership: "pending",
      capabilities: "pending"
    },
    reaper: {
      canonical_ir_emitted: false,
      typed_ir_schema: "reaper.processor-fabric-typed-ir.v1",
      span_source_map_required: true,
      validation_required: true
    },
    execution_performed: false,
    hardware_access_performed: false
  };
  return { topology, fabric, resources, bridge };
}

function withFiles(callback) {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), "reaper-pfi-"));
  const base = fixtures();
  const paths = {
    source: path.join(directory, "source.rpr"),
    topology: path.join(directory, "topology.json"),
    fabric: path.join(directory, "fabric.json"),
    bridge: path.join(directory, "bridge.json"),
    resources: path.join(directory, "resources.json")
  };
  const write = (key, value) => {
    fs.writeFileSync(paths[key], key === "source" ? value : JSON.stringify(value));
  };
  write("source", source);
  write("topology", base.topology);
  write("fabric", base.fabric);
  write("bridge", base.bridge);
  write("resources", base.resources);
  try {
    return callback({ base, paths, write });
  } finally {
    fs.rmSync(directory, { recursive: true, force: true });
  }
}

function importFiles(paths) {
  return importProcessorFabric({
    sourceFile: paths.source,
    topologyFile: paths.topology,
    fabricFile: paths.fabric,
    bridgeFile: paths.bridge,
    resourcesFile: paths.resources
  });
}

function rejectsCode(run, code) {
  assert.throws(run, error =>
    error instanceof ProcessorFabricImportError && error.code === code
  );
}

test("imports local read-only evidence and preserves exact UTF-8 byte spans", () => {
  withFiles(({ paths }) => {
    const result = importFiles(paths);
    assert.equal(result.source.sha256, digest);
    assert.equal(result.source.byte_length, source.length);
    assert.equal(result.source.offset_unit, "utf8-byte");
    assert.equal(result.semantic_admission.canonical_ir_emitted, false);
    assert.equal(result.execution_performed, false);
    assert.equal(result.hardware_access_performed, false);
    assert.equal(result.fabric.node_count, 3);
    assert.equal(result.fabric.edges.length, 1);
    assert.equal(result.constructs[0].sourceSpan.length, source.length - 1);
    assert.equal(result.constructs[0].bodySpan.start, bodyStart);
    assert.equal(result.constructs[0].bodySpan.length, bodyLength);
    assert.deepEqual(result.constructs[0].resourceRefs, [3]);
  });
});

test("rejects stale topology/PPF generations", () => {
  withFiles(({ paths, base, write }) => {
    write("fabric", { ...base.fabric, generation: 8 });
    rejectsCode(() => importFiles(paths), "RPR-PFI-0202");
  });
});

test("rejects stale hardware resource and bridge generations", () => {
  withFiles(({ paths, base, write }) => {
    write("resources", { ...base.resources, generation: 8 });
    rejectsCode(() => importFiles(paths), "RPR-PFI-0302");
    write("resources", base.resources);
    write("bridge", { ...base.bridge, generation: 8 });
    rejectsCode(() => importFiles(paths), "RPR-PFI-0402");
  });
});

test("rejects source digest mismatch and producer-claimed type/effect verification", () => {
  withFiles(({ paths, base, write }) => {
    write("bridge", {
      ...base.bridge,
      source: { ...base.bridge.source, digest: "0".repeat(64) }
    });
    rejectsCode(() => importFiles(paths), "RPR-PFI-0403");
    write("bridge", {
      ...base.bridge,
      semantic_status: { ...base.bridge.semantic_status, typing: "verified" }
    });
    rejectsCode(() => importFiles(paths), "RPR-PFI-0411");
  });
});

test("rejects missing PPF resource references and dependency edges", () => {
  withFiles(({ paths, base, write }) => {
    write("bridge", {
      ...base.bridge,
      graph: { ...base.bridge.graph, resource_refs: [99] }
    });
    rejectsCode(() => importFiles(paths), "RPR-PFI-0409");
    write("bridge", {
      ...base.bridge,
      graph: { ...base.bridge.graph, dependency_refs: [1] }
    });
    rejectsCode(() => importFiles(paths), "RPR-PFI-0410");
  });
});

test("rejects graph parent cycles and unsafe region overlap", () => {
  withFiles(({ paths, base, write }) => {
    write("fabric", {
      ...base.fabric,
      nodes: base.fabric.nodes.map(node => node.id === 1
        ? { ...node, parent_id: 2 }
        : node)
    });
    rejectsCode(() => importFiles(paths), "RPR-PFI-0211");
    write("fabric", base.fabric);
    const resources = {
      ...base.resources,
      address_spaces: [{
        id: "bar", kind: "device-bar", address_bits: 32,
        endianness: "little", owner: "device", device_id: "sensor-device"
      }],
      memory_regions: [
        { id: "r1", space_id: "bar", base: "0x1000", length: "0x100",
          alignment: 16, permissions: ["read"], cache_policy: "device",
          owner: "device", device_id: "sensor-device" },
        { id: "r2", space_id: "bar", base: "0x1080", length: "0x100",
          alignment: 16, permissions: ["read"], cache_policy: "device",
          owner: "device", device_id: "sensor-device" }
      ]
    };
    write("resources", resources);
    rejectsCode(() => importFiles(paths), "RPR-PFI-0313");
  });
});

test("rejects symlinked input files", () => {
  withFiles(({ paths }) => {
    const linkPath = paths.source + ".link";
    fs.symlinkSync(paths.source, linkPath);
    assert.throws(() => importProcessorFabric({
      sourceFile: linkPath,
      topologyFile: paths.topology,
      fabricFile: paths.fabric,
      bridgeFile: paths.bridge,
      resourcesFile: paths.resources
    }), error => error instanceof ProcessorFabricImportError && error.code === "RPR-PFI-0006");
  });
});
