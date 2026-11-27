# Platform evidence contract v1

The Reaper standard library defines the shared envelope for normalized platform hardware evidence emitted by Pytyliki adapters.

## Contract

The schema is \`pytyliki.platform-evidence.v1\`. It carries:

- provider: \`windows-whea\` or \`linux-edac\`;
- event code, event kind and event severity;
- source record ID and cumulative counter as decimal strings;
- epoch nanoseconds as a decimal string, preserving the full u64 range;
- CPU identity when the provider actually reports one, otherwise JSON null;
- a bounded source identity and three SHA-256 digests.

Large unsigned integers are decimal strings so JavaScript and other IEEE-754 consumers do not silently lose precision. The source adapter must not invent a CPU ID or application worker ID when hardware records do not carry that attribution.

## Reaper validation

\`stdlib/platform_evidence.rpr\` validates the schema, field types, supported providers, event classes, bounded identity strings, digest shape and contiguous sequence numbers. It is a deterministic contract validator; it does not open event logs or read sysfs.

The TypeScript verifier checks the actual event digest and append-only chain. The evidence ledger in Pytyliki is the producer of those digests. A shape-valid digest string is not, by itself, cryptographic verification.

## Trust boundaries

- Windows WHEA events are read through the Windows Event Log API from records published by the WHEA ETW provider. The adapter does not enable, disable or inject WHEA error sources.
- Linux EDAC counters are read from sysfs. The adapter does not load EDAC modules, write sysfs values or issue device commands.
- Hardware source records and application-thread faults remain distinct. CPU correlation is permitted only when the source record actually identifies a CPU and the caller supplies a matching time window.
- Unknown CPU attribution remains null. A memory-controller record is not silently relabelled as a CPU-thread fault.

The sample values in the conformance example are synthetic fixtures and do not represent a machine measurement.
