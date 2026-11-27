#!/usr/bin/env node
import { readFileSync } from "node:fs";

function fail(message) {
  console.error("Processor project validation failed: " + message);
  process.exit(1);
}
const [manifestPath, schemaPath] = process.argv.slice(2);
if (!manifestPath || !schemaPath) fail("usage: node tools/validate_processor_project.mjs <manifest.json> <schema.json>");

const parse = (path) => {
  try { return JSON.parse(readFileSync(path, "utf8")); }
  catch (error) { fail("cannot parse " + path + ": " + error.message); }
};
const schema = parse(schemaPath);
const manifest = parse(manifestPath);
const requireValue = (condition, message) => { if (!condition) throw new Error(message); };
const object = (value) => value !== null && typeof value === "object" && !Array.isArray(value);
const text = (value) => typeof value === "string" && value.length > 0;
const integer = (value, min, max) => Number.isInteger(value) && value >= min && value <= max;
const safeRelative = (value) => text(value) && !value.startsWith("/") && !value.includes("\\") &&
  !value.split("/").includes("..") && !value.split("/").includes("");


const exactKeys = (value, expected, label) => {
  requireValue(object(value), label + " must be an object");
  requireValue(
    Object.keys(value).length === expected.length &&
      expected.every((key) => Object.hasOwn(value, key)),
    label + " keys do not match the v1 contract"
  );
};

function validate(value) {
  requireValue(object(value), "manifest must be an object");
  const rootKeys = ["schema","version","project","target","toolchain","memory","workload","sources","output","verification"];
  requireValue(Object.keys(value).length === rootKeys.length && rootKeys.every((key) => Object.hasOwn(value,key)), "manifest root keys do not match v1 contract");
  requireValue(value.schema === "reaper.processor-project/v1" && value.version === 1, "unsupported project schema");
  exactKeys(value.project, ["id","name","purpose"], "project");
  requireValue(/^[a-z][a-z0-9.-]{2,63}$/.test(value.project.id) && text(value.project.name) && value.project.name.length <= 96 && text(value.project.purpose) && value.project.purpose.length <= 256, "project identity is invalid");

  const target = value.target;
  exactKeys(target, ["architecture","triple","abi","address_bits","endianness","required_isa","minimum_logical_processors"], "target");
  requireValue(["x86-64","x86","ARM64","ARM","riscv64","e2k","wasm32"].includes(target.architecture), "unsupported target architecture");
  requireValue(text(target.triple) && target.triple.length <= 128, "target triple is invalid");
  requireValue(["SYSV64","WIN64","AAPCS64","RISCV64","DABI64","WASM32","C"].includes(target.abi), "unsupported ABI");
  requireValue([32,64].includes(target.address_bits) && ["little","big"].includes(target.endianness), "address width or endianness is invalid");
  requireValue(Array.isArray(target.required_isa) && target.required_isa.length <= 32, "required_isa must be a bounded array");
  const supportedIsa = new Set(["sse2","sse4_2","avx","avx2","avx512f","aes","fma","neon","sve","rvv"]);
  requireValue(new Set(target.required_isa).size === target.required_isa.length && target.required_isa.every((item) => supportedIsa.has(item)), "required_isa contains duplicates or unsupported entries");
  requireValue(integer(target.minimum_logical_processors,1,4096), "minimum logical processors must be in 1..4096");
  if (target.architecture === "x86-64") requireValue(target.address_bits === 64 && target.endianness === "little", "x86-64 requires 64-bit little-endian target");
  if (target.architecture === "x86") requireValue(target.address_bits === 32, "x86 target requires a 32-bit address model");
  if (target.architecture === "riscv64") requireValue(target.address_bits === 64, "riscv64 requires 64-bit address model");
  if (target.abi === "SYSV64") requireValue(target.architecture === "x86-64" && target.address_bits === 64, "SYSV64 requires x86-64");
  if (target.abi === "WIN64") requireValue(target.architecture === "x86-64" && target.address_bits === 64, "WIN64 requires x86-64");
  if (target.abi === "AAPCS64") requireValue(target.architecture === "ARM64" && target.address_bits === 64, "AAPCS64 requires ARM64");
  if (target.abi === "RISCV64") requireValue(target.architecture === "riscv64" && target.address_bits === 64, "RISCV64 requires riscv64");
  if (target.abi === "WASM32") requireValue(target.architecture === "wasm32" && target.address_bits === 32, "WASM32 requires wasm32");
  for (const feature of target.required_isa) {
    if (["sse2","sse4_2","avx","avx2","avx512f","aes","fma"].includes(feature))
      requireValue(["x86-64","x86"].includes(target.architecture), "x86 ISA feature cannot target a non-x86 processor");
    if (["neon","sve"].includes(feature))
      requireValue(["ARM64","ARM"].includes(target.architecture), "ARM ISA feature cannot target a non-ARM processor");
    if (feature === "rvv") requireValue(target.architecture === "riscv64", "RVV requires a RISC-V target");
  }

  const toolchain = value.toolchain;
  exactKeys(toolchain, ["compiler","family","backend","execution_scope","target_qualified"], "toolchain");
  requireValue(text(toolchain.compiler) && toolchain.compiler.length <= 64, "toolchain compiler descriptor is invalid");
  requireValue(["gcc","clang","msvc","vendor","unknown"].includes(toolchain.family), "unsupported toolchain family");
  requireValue(toolchain.backend === "scalar-c17" && toolchain.execution_scope === "host-only" && toolchain.target_qualified === false, "this v1 vertical slice only accepts unqualified host scalar-C17 AOT");
  exactKeys(value.output, ["path","kind"], "output");
  exactKeys(value.verification, ["benchmark_repetitions","require_integrity","require_source_smoke","deterministic_replay"], "verification");
  requireValue(value.output.kind === "host-executable" && safeRelative(value.output.path), "scalar-C17 output must be a safe relative host-executable path");

  const memory = value.memory;
  exactKeys(memory, ["minimum_available_mib","working_set_mib","stack_bytes","heap_bytes","dma_bytes"], "memory");
  requireValue(integer(memory.minimum_available_mib,1,1048576), "minimum_available_mib is invalid");
  requireValue(integer(memory.working_set_mib,1,65536) && memory.working_set_mib <= memory.minimum_available_mib, "working_set_mib must fit the declared minimum");
  requireValue(integer(memory.stack_bytes,1024,1073741824), "stack budget is invalid");
  requireValue(integer(memory.heap_bytes,0,1073741824), "heap budget is invalid");
  requireValue(memory.dma_bytes === 0, "DMA is outside the host scalar-AOT profile");

  const workload = value.workload;
  exactKeys(workload, ["kind","entry","max_iterations","memory_mib","passes","max_steps"], "workload");
  requireValue(workload.kind === "scalar-probe" && /^[A-Za-z_][A-Za-z0-9_]{0,63}$/.test(workload.entry), "only the scalar-probe workload is admitted in v1");
  requireValue(integer(workload.max_iterations,1,100000000), "max_iterations is invalid");
  requireValue(integer(workload.memory_mib,1,64) && workload.memory_mib <= memory.working_set_mib, "workload memory exceeds project working set");
  requireValue(integer(workload.passes,1,32) && integer(workload.max_steps,1,1000000), "workload bounds exceed the current scalar AOT step ceiling");

  requireValue(Array.isArray(value.sources) && value.sources.length > 0 && value.sources.length <= 64, "sources must contain 1..64 entries");
  requireValue(new Set(value.sources).size === value.sources.length && value.sources.every((item) => safeRelative(item) && item.endsWith(".rpr")), "source paths must be unique, relative .rpr paths without traversal");
  requireValue(integer(value.verification.benchmark_repetitions,1,100), "benchmark repetitions are invalid");
  for (const field of ["require_integrity","require_source_smoke","deterministic_replay"]) requireValue(typeof value.verification[field] === "boolean", "verification." + field + " must be boolean");
  requireValue(value.verification.deterministic_replay === true, "deterministic replay is mandatory");
  return true;
}

try {
  requireValue(schema.$schema === "https://json-schema.org/draft/2020-12/schema", "schema must use Draft 2020-12");
  requireValue(schema.properties?.schema?.const === "reaper.processor-project/v1", "schema identity mismatch");
  validate(manifest);
} catch (error) { fail(error.message); }

const negatives = [
  ["dma-enabled", (copy) => { copy.memory.dma_bytes = 4096; }],
  ["qualified-unsupported-backend", (copy) => { copy.toolchain.target_qualified = true; }],
  ["source-path-traversal", (copy) => { copy.sources[0] = "../private.rpr"; }],
  ["invalid-address-width", (copy) => { copy.target.address_bits = 32; }],
];
for (const [name, mutate] of negatives) {
  const copy = structuredClone(manifest);
  mutate(copy);
  let rejected = false;
  try { validate(copy); } catch { rejected = true; }
  if (!rejected) fail("negative case was not rejected: " + name);
}
console.log("REAPER_PROCESSOR_PROJECT_SCHEMA_OK");
console.log("REAPER_PROCESSOR_PROJECT_POLICY_OK");
console.log("REAPER_PROCESSOR_PROJECT_NEGATIVE_CASES_OK:" + negatives.length);
