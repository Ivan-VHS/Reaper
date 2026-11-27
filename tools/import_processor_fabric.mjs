import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import { TextDecoder } from "node:util";

const MAX_SOURCE_BYTES = 1024 * 1024;
const MAX_JSON_BYTES = 16 * 1024 * 1024;

export class ProcessorFabricImportError extends Error {
  constructor(code, message) {
    super(message);
    this.name = "ProcessorFabricImportError";
    this.code = code;
  }
}

function fail(code, message) {
  throw new ProcessorFabricImportError(code, message);
}

function isRecord(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function requireRecord(value, field) {
  if (!isRecord(value)) fail("RPR-PFI-0001", field + " must be a JSON object");
  return value;
}

function requireInteger(value, field, minimum = 0, maximum = Number.MAX_SAFE_INTEGER) {
  if (!Number.isSafeInteger(value) || value < minimum || value > maximum)
    fail("RPR-PFI-0002", field + " is outside its integer bounds");
  return value;
}

function requireText(value, field, maximum = 256) {
  if (typeof value !== "string" || value.length === 0 || value.length > maximum)
    fail("RPR-PFI-0003", field + " must be non-empty text within its bound");
  return value;
}

function parseUnsigned(value, field) {
  if (typeof value === "number") {
    if (!Number.isSafeInteger(value) || value < 0) fail("RPR-PFI-0010", field + " is not a safe unsigned integer");
    return BigInt(value);
  }
  if (typeof value !== "string" || !/^0x[0-9a-f]+$/i.test(value))
    fail("RPR-PFI-0010", field + " must be an unsigned integer or hexadecimal string");
  return BigInt(value);
}

function requireDigest(value, field) {
  if (typeof value !== "string" || !/^[0-9a-f]{64}$/.test(value))
    fail("RPR-PFI-0004", field + " must be a lowercase SHA-256 digest");
  return value;
}

function readLocalFile(filePath, maximum, label) {
  const absolute = path.resolve(filePath);
  let stat;
  try { stat = fs.lstatSync(absolute); }
  catch (error) { fail("RPR-PFI-0005", label + " cannot be read: " + error.message); }
  if (stat.isSymbolicLink() || !stat.isFile())
    fail("RPR-PFI-0006", label + " must be a regular local file, not a symlink");
  if (stat.size > maximum) fail("RPR-PFI-0007", label + " exceeds the configured byte limit");
  let bytes;
  try { bytes = fs.readFileSync(absolute); }
  catch (error) { fail("RPR-PFI-0008", label + " read failed: " + error.message); }
  return { absolute, bytes };
}

function readJsonFile(filePath, label) {
  const { absolute, bytes } = readLocalFile(filePath, MAX_JSON_BYTES, label);
  let text;
  try { text = new TextDecoder("utf-8", { fatal: true }).decode(bytes); }
  catch { fail("RPR-PFI-0009", label + " is not valid UTF-8"); }
  try { return { value: JSON.parse(text), path: absolute, bytes }; }
  catch (error) { fail("RPR-PFI-0011", label + " is not valid JSON: " + error.message); }
}

function hash(bytes) {
  return crypto.createHash("sha256").update(bytes).digest("hex");
}

function validateTopology(topology) {
  requireRecord(topology, "topologyEvidence");
  if (topology.schema !== "pytyliki.processor-topology-evidence.v2" || topology.version !== 2)
    fail("RPR-PFI-0101", "unsupported host topology evidence schema");
  const generation = requireInteger(topology.generation, "topology generation", 1);
  requireText(topology.captured_at, "topology captured_at", 40);
  const collector = requireRecord(topology.collector, "topology collector");
  requireText(collector.provider, "collector provider", 64);
  requireText(collector.interface, "collector interface", 64);
  if (collector.read_only !== true) fail("RPR-PFI-0102", "topology evidence must be read-only");
  if (!["complete", "partial", "unknown"].includes(topology.completeness))
    fail("RPR-PFI-0103", "topology completeness is invalid");
  const body = requireRecord(topology.topology, "topology body");
  const logical = body.logical_processors;
  if (!Array.isArray(logical) || logical.length < 1 || logical.length > 4096)
    fail("RPR-PFI-0104", "logical processor inventory is empty or oversized");
  const byId = new Map();
  const byOs = new Set();
  let online = 0;
  for (const [index, cpuValue] of logical.entries()) {
    const cpu = requireRecord(cpuValue, "logical_processors[" + index + "]");
    const id = requireInteger(cpu.logical_id, "logical_id", 0, 4095);
    const osId = requireInteger(cpu.os_id, "os_id", 0, 65535);
    const groupId = cpu.group_id === null ? null : requireInteger(cpu.group_id, "group_id", 0, 255);
    if (byId.has(id)) fail("RPR-PFI-0105", "duplicate logical CPU identifier " + id);
    const osKey = String(groupId) + ":" + osId;
    if (byOs.has(osKey)) fail("RPR-PFI-0106", "duplicate OS processor identity " + osKey);
    byId.set(id, cpu);
    byOs.add(osKey);
    if (typeof cpu.online !== "boolean") fail("RPR-PFI-0107", "CPU online state must be boolean");
    if (cpu.online) online++;
    if (!["observed", "partially-observed", "unknown"].includes(cpu.evidence))
      fail("RPR-PFI-0108", "CPU evidence state is invalid");
    for (const key of ["package_id", "die_id", "core_id", "numa_node_id"])
      if (cpu[key] !== null) requireInteger(cpu[key], "CPU " + key, 0);
  }
  if (body.logical_processor_count !== logical.length || body.online_logical_processor_count !== online)
    fail("RPR-PFI-0109", "topology CPU counts do not match their inventory");

  if (!Array.isArray(body.numa_nodes) || body.numa_nodes.length > 1024)
    fail("RPR-PFI-0110", "NUMA node list is invalid");
  const numaIds = new Set();
  for (const nodeValue of body.numa_nodes) {
    const node = requireRecord(nodeValue, "NUMA node");
    const id = requireInteger(node.node_id, "NUMA node id", 0);
    if (numaIds.has(id)) fail("RPR-PFI-0111", "duplicate NUMA node id " + id);
    numaIds.add(id);
    if (!Array.isArray(node.logical_ids)) fail("RPR-PFI-0112", "NUMA logical_ids must be an array");
    const seen = new Set();
    for (const cpuId of node.logical_ids) {
      requireInteger(cpuId, "NUMA logical id", 0, 4095);
      if (!byId.has(cpuId) || seen.has(cpuId)) fail("RPR-PFI-0113", "NUMA node contains an unknown or duplicate logical CPU");
      seen.add(cpuId);
      if (byId.get(cpuId).numa_node_id !== id) fail("RPR-PFI-0114", "NUMA membership disagrees with CPU record");
    }
  }
  if (!Array.isArray(body.caches) || body.caches.length > 16384)
    fail("RPR-PFI-0115", "cache list is invalid");
  for (const cacheValue of body.caches) {
    const cache = requireRecord(cacheValue, "cache");
    requireInteger(cache.cache_id, "cache id", 0);
    requireInteger(cache.level, "cache level", 1, 4);
    if (!Array.isArray(cache.sharing_logical_ids)) fail("RPR-PFI-0116", "cache sharing IDs must be an array");
    const seen = new Set();
    for (const cpuId of cache.sharing_logical_ids) {
      requireInteger(cpuId, "cache sharing CPU", 0, 4095);
      if (!byId.has(cpuId) || seen.has(cpuId)) fail("RPR-PFI-0117", "cache sharing set contains unknown or duplicate CPU");
      seen.add(cpuId);
    }
  }
  const isa = requireRecord(topology.isa, "ISA evidence");
  requireText(isa.architecture, "ISA architecture", 32);
  if (!isRecord(isa.features)) fail("RPR-PFI-0118", "ISA feature map is missing");
  for (const [name, value] of Object.entries(isa.features)) {
    const feature = requireRecord(value, "ISA feature " + name);
    for (const field of ["hardware_present", "os_usable"])
      if (![true, false, null].includes(feature[field]))
        fail("RPR-PFI-0119", "ISA " + name + "." + field + " must be true, false or null");
    if (feature.os_usable === true && feature.hardware_present !== true)
      fail("RPR-PFI-0120", "OS-usable ISA cannot be true when hardware presence is unknown or false");
  }
  if (topology.execution_performed === true ||
      topology.hardware_access_performed === true ||
      topology.processor_state_changed === true)
    fail("RPR-PFI-0121", "read-only topology evidence contains a hardware-effect claim");
  return { generation, cpuCount: logical.length, onlineCount: online, byId };
}

function validateFabric(fabric, topology) {
  requireRecord(fabric, "fabric");
  if (fabric.schema !== "pytyliki.processor-fabric-graph.v2" || fabric.abi_major !== 2)
    fail("RPR-PFI-0201", "unsupported PPF graph ABI/schema");
  const generation = requireInteger(fabric.generation, "PPF generation", 1);
  if (generation !== topology.generation)
    fail("RPR-PFI-0202", "PPF graph and topology evidence generations differ");
  if (!Array.isArray(fabric.nodes) || !Array.isArray(fabric.edges))
    fail("RPR-PFI-0203", "PPF nodes and edges must be arrays");
  if (fabric.nodes.length < 1 || fabric.nodes.length > 4096 || fabric.edges.length > 16384)
    fail("RPR-PFI-0204", "PPF graph exceeds import limits");
  if (fabric.node_count !== fabric.nodes.length || fabric.edge_count !== fabric.edges.length)
    fail("RPR-PFI-0205", "PPF node/edge counts are inconsistent");

  const nodes = new Map();
  const processIds = new Set();
  for (const [index, nodeValue] of fabric.nodes.entries()) {
    const node = requireRecord(nodeValue, "PPF node " + index);
    const id = requireInteger(node.id, "PPF node id", 1);
    if (nodes.has(id)) fail("RPR-PFI-0206", "duplicate PPF node id " + id);
    requireText(node.kind, "PPF node kind", 48);
    if (!["declared", "verified", "ready", "available", "blocked", "completed",
          "failed", "disabled", "retired"].includes(node.state))
      fail("RPR-PFI-0207", "invalid PPF node state for id " + id);
    if (node.generation !== undefined && node.generation !== generation)
      fail("RPR-PFI-0208", "PPF node generation differs from graph generation");
    if (node.parent_id !== undefined && node.parent_id !== null)
      requireInteger(node.parent_id, "PPF parent id", 1);
    if (node.kind === "process") processIds.add(id);
    if (node.kind === "logical-processor" && node.logical_id !== undefined) {
      const logicalId = requireInteger(node.logical_id, "PPF logical CPU id", 0, 255);
      if (!topology.byId.has(logicalId))
        fail("RPR-PFI-0209", "PPF graph contains a logical CPU absent from topology evidence");
    }
    nodes.set(id, node);
  }
  for (const node of nodes.values()) {
    if (node.parent_id !== undefined && node.parent_id !== null && !nodes.has(node.parent_id))
      fail("RPR-PFI-0210", "PPF node references a missing parent");
  }
  const parentMarks = new Map();
  function visitParent(id) {
    const mark = parentMarks.get(id) || 0;
    if (mark === 1) fail("RPR-PFI-0211", "PPF parent graph contains a cycle");
    if (mark === 2) return;
    parentMarks.set(id, 1);
    const node = nodes.get(id);
    if (node.parent_id !== undefined && node.parent_id !== null) visitParent(node.parent_id);
    parentMarks.set(id, 2);
  }
  for (const id of nodes.keys()) visitParent(id);

  const dependencyAdj = new Map();
  const edgeKeys = new Set();
  for (const [index, edgeValue] of fabric.edges.entries()) {
    const edge = requireRecord(edgeValue, "PPF edge " + index);
    const from = requireInteger(edge.from_id, "PPF edge from", 1);
    const to = requireInteger(edge.to_id, "PPF edge to", 1);
    const kind = requireText(edge.kind, "PPF edge kind", 48);
    if (!nodes.has(from) || !nodes.has(to)) fail("RPR-PFI-0212", "PPF edge references a missing node");
    const key = from + ":" + to + ":" + kind;
    if (edgeKeys.has(key)) fail("RPR-PFI-0213", "duplicate PPF edge " + key);
    edgeKeys.add(key);
    const a = nodes.get(from), b = nodes.get(to);
    if (kind === "depends-on") {
      if (a.kind !== "process" || b.kind !== "process")
        fail("RPR-PFI-0214", "depends-on must connect process nodes");
      const list = dependencyAdj.get(from) || [];
      list.push(to);
      dependencyAdj.set(from, list);
    } else if (kind === "maps-to") {
      if (!(a.kind === "memory-region" && b.kind === "address-space"))
        fail("RPR-PFI-0215", "maps-to must connect a memory region to an address space");
    } else if (kind === "uses") {
      const allowedTargets = ["logical-processor", "execution-unit", "register-bank",
        "isa-profile", "address-space", "memory-region", "device"];
      if (a.kind !== "process" || !allowedTargets.includes(b.kind))
        fail("RPR-PFI-0216", "uses must connect a process to a typed worker or resource");
    } else if (kind === "produces") {
      if (a.kind !== "process" || b.kind !== "artifact")
        fail("RPR-PFI-0217", "produces must connect process to artifact");
    } else {
      fail("RPR-PFI-0219", "unknown PPF edge kind " + kind);
    }
  }
  const marks = new Map();
  function visitDependency(id) {
    const mark = marks.get(id) || 0;
    if (mark === 1) fail("RPR-PFI-0220", "PPF dependency graph contains a cycle");
    if (mark === 2) return;
    marks.set(id, 1);
    for (const next of dependencyAdj.get(id) || []) visitDependency(next);
    marks.set(id, 2);
  }
  for (const id of processIds) visitDependency(id);
  return { generation, nodes, processIds, edgeCount: fabric.edges.length, edges: fabric.edges };
}

function validateResources(resources, generation) {
  requireRecord(resources, "resourceContract");
  if (resources.schema !== "pytyliki.hardware-resource-contract.v1" || resources.version !== 1)
    fail("RPR-PFI-0301", "unsupported hardware resource contract schema");
  if (requireInteger(resources.generation, "resource generation", 1) !== generation)
    fail("RPR-PFI-0302", "resource and topology generations differ");
  const devices = new Map();
  for (const device of resources.devices || []) {
    const id = requireText(device.id, "device id", 96);
    if (devices.has(id)) fail("RPR-PFI-0303", "duplicate hardware device id " + id);
    if (device.generation !== generation) fail("RPR-PFI-0304", "stale hardware device generation");
    devices.set(id, device);
  }
  const spaces = new Map();
  for (const space of resources.address_spaces || []) {
    const id = requireText(space.id, "address-space id", 96);
    if (spaces.has(id)) fail("RPR-PFI-0305", "duplicate address-space id " + id);
    requireInteger(space.address_bits, "address width", 1, 64);
    if (space.device_id != null && !devices.has(space.device_id))
      fail("RPR-PFI-0306", "address space references an unknown device");
    spaces.set(id, space);
  }
  const regions = new Map();
  const ranges = [];
  for (const region of resources.memory_regions || []) {
    const id = requireText(region.id, "memory-region id", 96);
    if (regions.has(id)) fail("RPR-PFI-0307", "duplicate memory-region id " + id);
    const space = spaces.get(region.space_id);
    if (!space) fail("RPR-PFI-0308", "memory region references an unknown address space");
    const base = parseUnsigned(region.base, "memory region base");
    const length = parseUnsigned(region.length, "memory region length");
    const alignment = BigInt(requireInteger(region.alignment, "memory region alignment", 1, 0x7fffffff));
    if (length === 0n || (alignment & (alignment - 1n)) !== 0n ||
        base % alignment !== 0n || length % alignment !== 0n)
      fail("RPR-PFI-0309", "memory region has invalid length/alignment");
    const end = base + length - 1n;
    if (end > ((1n << BigInt(space.address_bits)) - 1n))
      fail("RPR-PFI-0310", "memory region exceeds its address-space width");
    if (!Array.isArray(region.permissions) || region.permissions.length === 0)
      fail("RPR-PFI-0311", "memory region permissions are empty");
    if (region.device_id != null && !devices.has(region.device_id))
      fail("RPR-PFI-0312", "memory region references an unknown device");
    for (const previous of ranges) {
      if (previous.spaceId === region.space_id && base <= previous.end && previous.base <= end)
        fail("RPR-PFI-0313", "overlapping memory regions are not admitted by the interchange importer");
    }
    ranges.push({ spaceId: region.space_id, base, end });
    regions.set(id, region);
  }
  const banks = new Map();
  for (const bank of resources.register_banks || []) {
    const id = requireText(bank.id, "register-bank id", 96);
    if (banks.has(id)) fail("RPR-PFI-0314", "duplicate register-bank id " + id);
    if (!regions.has(bank.region_id) || !spaces.has(bank.space_id))
      fail("RPR-PFI-0315", "register bank references a missing region/address space");
    banks.set(id, bank);
  }
  for (const bank of banks.values()) {
    const region = regions.get(bank.region_id);
    const length = parseUnsigned(region.length, "register region length");
    const registerRanges = [];
    for (const register of bank.registers || []) {
      const width = requireInteger(register.width_bits, "register width", 8, 128);
      if (![8, 16, 32, 64, 128].includes(width)) fail("RPR-PFI-0316", "unsupported register width");
      const offset = parseUnsigned(register.offset, "register offset");
      const bytes = BigInt(width / 8);
      const alignment = BigInt(requireInteger(register.alignment, "register alignment", 1, 0x7fffffff));
      if ((alignment & (alignment - 1n)) !== 0n || offset % alignment !== 0n ||
          alignment < bytes || offset > length || bytes > length - offset)
        fail("RPR-PFI-0317", "register alignment or range is invalid");
      for (const previous of registerRanges)
        if (offset <= previous.end && previous.base <= offset + bytes - 1n)
          fail("RPR-PFI-0318", "register descriptors overlap");
      registerRanges.push({ base: offset, end: offset + bytes - 1n });
      if (typeof register.volatile !== "boolean") fail("RPR-PFI-0319", "register volatile must be boolean");
      if (!["read-only", "write-only", "read-write", "write-one-to-clear", "write-one-to-set", "read-clear"].includes(register.access))
        fail("RPR-PFI-0320", "register access mode is invalid");
      if (!["cpu", "device", "shared", "unowned"].includes(register.owner))
        fail("RPR-PFI-0321", "register owner is invalid");
    }
  }
  for (const dma of resources.dma_buffers || []) {
    requireText(dma.id, "DMA buffer id", 96);
    if (!devices.has(dma.device_id) || !spaces.has(dma.space_id))
      fail("RPR-PFI-0322", "DMA buffer references a missing device or address space");
    if (dma.generation !== generation) fail("RPR-PFI-0323", "stale DMA buffer generation");
    const base = parseUnsigned(dma.base, "DMA base");
    const length = parseUnsigned(dma.length, "DMA length");
    const alignment = BigInt(requireInteger(dma.alignment, "DMA alignment", 1, 0x7fffffff));
    if (length === 0n || (alignment & (alignment - 1n)) !== 0n || base % alignment !== 0n)
      fail("RPR-PFI-0324", "DMA descriptor alignment/length is invalid");
    const end = base + length - 1n;
    if (end > ((1n << BigInt(spaces.get(dma.space_id).address_bits)) - 1n))
      fail("RPR-PFI-0325", "DMA buffer exceeds its address-space width");
    if (!["coherent", "non-coherent-explicit-sync", "unknown"].includes(dma.coherency))
      fail("RPR-PFI-0326", "DMA coherency is invalid");
    if (dma.state === "device_owned" && dma.coherency === "unknown")
      fail("RPR-PFI-0327", "device ownership is denied when DMA coherency is unknown");
  }
  return { devices: devices.size, addressSpaces: spaces.size, memoryRegions: regions.size,
    registerBanks: banks.size, dmaBuffers: (resources.dma_buffers || []).length };
}

function validateBridge(bridge, sourceBytes, sourceDigest, fabric, resourceInfo) {
  requireRecord(bridge, "hardwareIrBridge");
  if (bridge.schema !== "pytyliki.hardware-ir-bridge.v1" || bridge.version !== 1)
    fail("RPR-PFI-0401", "unsupported Hardware AST bridge schema");
  if (bridge.generation !== fabric.generation)
    fail("RPR-PFI-0402", "bridge and PPF generations differ");
  const source = requireRecord(bridge.source, "bridge source");
  if (requireDigest(source.digest, "bridge source digest") !== sourceDigest)
    fail("RPR-PFI-0403", "Hardware AST bridge digest does not match the supplied source file");
  if (source.byte_length !== sourceBytes.length)
    fail("RPR-PFI-0404", "Hardware AST bridge source byte length does not match supplied file");
  const construct = requireRecord(bridge.construct, "Hardware AST construct");
  requireText(construct.semantic_id, "construct semantic id", 128);
  const sourceSpan = requireRecord(construct.source_span, "construct source span");
  const bodySpan = requireRecord(construct.body_span, "construct body span");
  const start = requireInteger(sourceSpan.start, "source span start", 0, sourceBytes.length);
  const length = requireInteger(sourceSpan.length, "source span length", 0, sourceBytes.length);
  if (length > sourceBytes.length - start) fail("RPR-PFI-0405", "construct source span exceeds source bytes");
  const bodyStart = requireInteger(bodySpan.start, "body span start", start, sourceBytes.length);
  const bodyLength = requireInteger(bodySpan.length, "body span length", 0, sourceBytes.length);
  if (bodyLength > sourceBytes.length - bodyStart ||
      bodyStart + bodyLength > start + length)
    fail("RPR-PFI-0406", "construct body span is not contained in source span");
  const graph = requireRecord(bridge.graph, "bridge process graph");
  const processId = requireInteger(graph.process_id, "bridge process id", 1);
  if (!fabric.processIds.has(processId)) fail("RPR-PFI-0407", "construct references a missing PPF process");
  const resourceIds = resourceInfo.resourceIds || new Set();
  if (!Array.isArray(graph.resource_refs) || !Array.isArray(graph.dependency_refs))
    fail("RPR-PFI-0408", "bridge resource/dependency references must be arrays");
  const resourceRefs = new Set();
  for (const idValue of graph.resource_refs) {
    const id = requireInteger(idValue, "bridge resource ref", 1);
    if (resourceRefs.has(id)) fail("RPR-PFI-0409", "duplicate bridge resource reference " + id);
    resourceRefs.add(id);
    const node = fabric.nodes.get(id);
    if (!node || !["address-space", "memory-region", "register-bank", "device",
        "register", "dma-buffer"].includes(node.kind))
      fail("RPR-PFI-0409", "bridge resource reference must identify a PPF resource node");
    if (typeof node.semantic_ref !== "string" || !resourceIds.has(node.semantic_ref))
      fail("RPR-PFI-0409", "PPF resource node has no matching hardware resource contract reference");
  }
  const dependencyRefs = new Set();
  for (const idValue of graph.dependency_refs) {
    const id = requireInteger(idValue, "bridge dependency ref", 1);
    if (dependencyRefs.has(id)) fail("RPR-PFI-0410", "duplicate bridge dependency reference " + id);
    dependencyRefs.add(id);
    if (!fabric.processIds.has(id)) fail("RPR-PFI-0410", "bridge dependency references an unknown process");
    if (!fabric.edges.some(edge => edge.kind === "depends-on" &&
        edge.from_id === processId && edge.to_id === id))
      fail("RPR-PFI-0410", "bridge dependency is not present in the PPF process graph");
  }
  const status = requireRecord(bridge.semantic_status, "producer semantic status");
  for (const key of ["name_resolution", "typing", "effects", "ownership", "capabilities"]) {
    if (status[key] !== "pending")
      fail("RPR-PFI-0411", "producer cannot mark Reaper semantic admission as " + status[key]);
  }
  const reaper = requireRecord(bridge.reaper, "Reaper handoff");
  if (reaper.canonical_ir_emitted !== false || reaper.span_source_map_required !== true ||
      reaper.validation_required !== true)
    fail("RPR-PFI-0412", "producer cannot emit or bypass Reaper Canonical Typed IR validation");
  return {
    processId, semanticId: construct.semantic_id, kind: construct.kind, name: construct.name,
    sourceSpan: { start, length }, bodySpan: { start: bodyStart, length },
    resourceRefs: [...resourceRefs].sort((a, b) => a - b),
    dependencyRefs: [...dependencyRefs].sort((a, b) => a - b)
  };
}

export function importProcessorFabric(input) {
  requireRecord(input, "import arguments");
  const sourceFile = readLocalFile(requireText(input.sourceFile, "sourceFile"), MAX_SOURCE_BYTES, "source");
  let sourceText;
  try { sourceText = new TextDecoder("utf-8", { fatal: true }).decode(sourceFile.bytes); }
  catch { fail("RPR-PFI-0009", "source is not valid UTF-8"); }
  const sourceDigest = hash(sourceFile.bytes);
  const topologyInput = readJsonFile(requireText(input.topologyFile, "topologyFile"), "topology evidence");
  const fabricInput = readJsonFile(requireText(input.fabricFile, "fabricFile"), "PPF graph");
  const bridgeInput = readJsonFile(requireText(input.bridgeFile, "bridgeFile"), "Hardware AST bridge");
  const resourcesInput = readJsonFile(requireText(input.resourcesFile, "resourcesFile"), "hardware resource contract");

  const topology = validateTopology(topologyInput.value);
  const fabric = validateFabric(fabricInput.value, topology);
  const resourceInfo = validateResources(resourcesInput.value, topology.generation);
  const bridge = validateBridge(bridgeInput.value, sourceFile.bytes, sourceDigest, fabric,
    { ...resourceInfo, resourceIds: new Set([
      ...(resourcesInput.value.memory_regions || []).map(x => x.id),
      ...(resourcesInput.value.register_banks || []).map(x => x.id),
      ...(resourcesInput.value.address_spaces || []).map(x => x.id),
      ...(resourcesInput.value.dma_buffers || []).map(x => x.id),
      ...(resourcesInput.value.devices || []).map(x => x.id)
    ]) });

  const nodes = fabricInput.value.nodes;
  const rootCount = nodes.filter(n => n.parent_id == null).length;
  return {
    schema: "reaper.processor-fabric-import-report.v1",
    version: 1,
    imported_at: new Date().toISOString(),
    producer: { name: "Pytyliki", abi_major: 2 },
    source: {
      unit_id: bridgeInput.value.source.unit_id,
      sha256: sourceDigest,
      byte_length: sourceFile.bytes.length,
      offset_unit: "utf8-byte"
    },
    host_evidence: {
      schema: topologyInput.value.schema,
      generation: topology.generation,
      sha256: hash(topologyInput.bytes),
      completeness: topologyInput.value.completeness,
      logical_processor_count: topology.cpuCount,
      online_logical_processor_count: topology.onlineCount
    },
    fabric: {
      schema: fabricInput.value.schema,
      abi_major: 2,
      generation: fabric.generation,
      node_count: nodes.length,
      edge_count: fabric.edgeCount,
      root_count: rootCount,
      nodes: [...fabric.nodes.values()].sort((a, b) => a.id - b.id),
      edges: [...fabric.edges].sort((a, b) =>
        a.from_id - b.from_id || a.to_id - b.to_id || a.kind.localeCompare(b.kind))
    },
    constructs: [bridge],
    resources: resourceInfo,
    resource_contract: resourcesInput.value,
    topology_evidence: topologyInput.value,
    semantic_admission: {
      name_resolution: "pending",
      types: "pending",
      effects: "pending",
      ownership: "pending",
      capabilities: "pending",
      canonical_ir_emitted: false
    },
    diagnostics: [],
    execution_performed: false,
    hardware_access_performed: false
  };
}

function parseArgs(argv) {
  const result = {};
  for (let i = 0; i < argv.length; ++i) {
    const key = argv[i];
    if (!key.startsWith("--") || i + 1 >= argv.length)
      fail("RPR-PFI-0501", "expected --option value pairs");
    const name = key.slice(2);
    if (!["source", "topology", "fabric", "bridge", "resources", "output"].includes(name))
      fail("RPR-PFI-0502", "unknown option " + key);
    result[name] = argv[++i];
  }
  for (const key of ["source", "topology", "fabric", "bridge", "resources", "output"])
    if (!result[key]) fail("RPR-PFI-0503", "missing --" + key);
  return result;
}

if (process.argv[1] && path.resolve(process.argv[1]) === path.resolve(new URL(import.meta.url).pathname)) {
  try {
    const args = parseArgs(process.argv.slice(2));
    const output = importProcessorFabric({
      sourceFile: args.source, topologyFile: args.topology, fabricFile: args.fabric,
      bridgeFile: args.bridge, resourcesFile: args.resources
    });
    const outputPath = path.resolve(args.output);
    fs.writeFileSync(outputPath, JSON.stringify(output, null, 2) + "\n", { flag: "wx" });
    process.stdout.write("Reaper Processor Fabric import validated: " + output.fabric.node_count +
      " nodes, " + output.fabric.edge_count + " edges; Canonical Typed IR remains pending.\n");
  } catch (error) {
    process.stderr.write((error.code || "RPR-PFI-9999") + ": " + error.message + "\n");
    process.exitCode = 1;
  }
}
