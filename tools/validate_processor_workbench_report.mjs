#!/usr/bin/env node
import { readFileSync } from "node:fs";

function fail(message) {
  console.error("Processor workbench report validation failed: " + message);
  process.exit(1);
}
const [reportPath, schemaPath] = process.argv.slice(2);
if (!reportPath || !schemaPath) fail("usage: node tools/validate_processor_workbench_report.mjs <report.json> <schema.json>");
const parse = (path) => {
  try { return JSON.parse(readFileSync(path, "utf8")); }
  catch (error) { fail("cannot parse " + path + ": " + error.message); }
};
const report = parse(reportPath);
const schema = parse(schemaPath);
const check = (condition, message) => { if (!condition) throw new Error(message); };
const object = (value) => value !== null && typeof value === 'object' && !Array.isArray(value);
try {
  check(schema.$schema === "https://json-schema.org/draft/2020-12/schema", "schema must use Draft 2020-12");
  check(schema.properties?.schema?.const === "reaper.processor-workbench-report.v1", "schema identity mismatch");
  check(object(report) && report.schema === "reaper.processor-workbench-report.v1", "report identity mismatch");
  for (const key of ['target','host','benchmark','compiler','hardware_effects']) check(object(report[key]), key + ' object is missing');
  check(report.compiler.backend === 'scalar-c17' && report.compiler.execution_scope === 'host-only' && report.compiler.target_qualified === false && report.compiler.cross_compilation === false, 'compiler maturity boundary was weakened');
  for (const key of ['processor_settings_changed','affinity_changed','device_registers_written','firmware_or_microcode_written','drivers_changed']) check(report.hardware_effects[key] === false, 'hardware effect flag must remain false: ' + key);
  check(report.benchmark.producer === 'Pytyliki' && report.benchmark.schema === 'pytyliki.suite.v1', 'benchmark provenance is invalid');
  check(report.benchmark.repeat === report.benchmark.warmup_runs + report.benchmark.measured_runs, 'benchmark counts do not reconcile');
  check(report.benchmark.all_integrity_checks_passed === true, 'all benchmark integrity checks must pass');
  check(report.host.architecture === report.target.architecture, 'host and project architectures do not match');
  for (const key of ['sse2','sse4_2','avx_hardware','osxsave','avx_usable','avx2_usable','avx512f_usable','aes','fma_usable','virtualization']) check(typeof report.host.usable_isa[key] === 'boolean', 'ISA observation missing: ' + key);
  const isaFields = { sse2: 'sse2', sse4_2: 'sse4_2', avx: 'avx_usable', avx2: 'avx2_usable', avx512f: 'avx512f_usable', aes: 'aes', fma: 'fma_usable' };
  for (const feature of report.target.required_isa) {
    check(isaFields[feature] && report.host.usable_isa[isaFields[feature]] === true, 'required target ISA is not usable: ' + feature);
  }
  const negative = structuredClone(report);
  negative.hardware_effects.device_registers_written = true;
  let rejected = false;
  try { check(negative.hardware_effects.device_registers_written === false, 'device register writes must remain false'); } catch { rejected = true; }
  check(rejected, 'negative hardware-effect fixture was not rejected');
} catch (error) { fail(error.message); }
console.log("REAPER_PROCESSOR_WORKBENCH_REPORT_SCHEMA_OK");
console.log("REAPER_PROCESSOR_WORKBENCH_REPORT_SAFETY_OK");
