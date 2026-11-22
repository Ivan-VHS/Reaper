Unified report envelope
=======================

All four Ivan-VHS tools can wrap tool-specific JSON output in the common ivan-vhs.report.v1 metadata contract. The result field remains owned and validated by the originating tool.

Usage
-----

    python tools/report_envelope.py --tool reaper --version 0.8.0 --commit "$GITHUB_SHA" < audit.json
    python tools/report_envelope.py --tool oplague --version 1.0.0 --input-file driver.zip < evidence.json

The wrapper reads JSON from standard input and writes an envelope to standard output. When --input-file is used, only the SHA-256 digest is recorded; the local path is omitted. Hashing is streamed in 1 MiB chunks. Commit metadata comes from --commit, GITHUB_SHA or IVAN_VHS_COMMIT. Missing versions are marked unknown rather than guessed.

Contract
--------

The canonical schema is schemas/ivan-vhs.report.v1.schema.json. The shared envelope standardizes tool/version/commit, UTC creation time, wrapper platform, input kind/hash and project limitations. The result payload remains tool-specific.

This envelope is provenance metadata, not a digital signature, security verdict, performance claim, chain of custody or proof of authorship. SHA-256 establishes byte identity only.
