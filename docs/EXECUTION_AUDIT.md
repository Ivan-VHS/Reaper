# Execution audit trail

Reaper can append an optional local JSON Lines audit trail with a SHA-256
hash chain. Each record contains a monotonically increasing sequence number,
UTC timestamp, event name, non-sensitive metadata, previous-record hash, and
its own digest.

## Usage

    python -m reaper examples/hello.rpr --audit-log .reaper/audit.jsonl
    python -m reaper --verify-audit-log .reaper/audit.jsonl

The journal records the source filename, SHA-256 source fingerprint, run
lifecycle status, error type on failure, and number of output lines.
Program output and source contents are not copied into the journal.

## Trust boundary and limitations

The verifier detects modified, missing, reordered, or malformed records in an
existing chain. A local hash chain is tamper-evident, not tamper-proof: a person
who can rewrite the entire file can recompute its hashes. The log is not
digitally signed and is not a trusted remote attestation. It is a single-writer
local journal; concurrent writers to the same file are not coordinated.

Audit mode is opt-in. Without --audit-log, normal interpreter behavior is
unchanged. If an existing journal fails verification, Reaper refuses to append
to it rather than silently starting a new chain.
