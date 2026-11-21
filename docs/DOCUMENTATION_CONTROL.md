# Documentation Control

**Status:** normative  
**Scope:** all public documentation, examples, grammars, registries, schemas, release notes and repository metadata.

Published documentation is a controlled language and product contract. It defines supported syntax, semantics, observable runtime behavior and versioned interfaces. It is not an archive of planning sessions, private inputs or implementation history.

## Publication requirements

1. **Normative authority:** the versioned language specification and checked-in conformance tests define language behavior. Examples and secondary pages MUST NOT override them.
2. **Private material:** public documentation MUST NOT identify, quote or fingerprint private attachments, local working files, Library objects, chat threads, prompts, personal notes, internal share handles or unpublished reference material. Do not publish filenames, hashes, sizes, line counts or storage identifiers.
3. **Capability status:** distinguish implemented, partial, reserved, planned and unsupported syntax or runtime behavior. A lexical reservation MUST NOT be described as an executable construct. A roadmap item MUST NOT be described as shipped.
4. **Normative language:** use MUST, MUST NOT, SHOULD, SHOULD NOT and MAY consistently. Every normative rule MUST identify its scope and an observable acceptance condition.
5. **Compatibility:** language, grammar, token aliases, bytecode, ABI and serialized data changes MUST declare compatibility impact. Breaking changes require a versioned contract or migration rule.
6. **Security boundary:** distinguish interpreter quotas from operating-system isolation. In-process native FFI executes trusted code and MUST NOT be represented as a sandbox.
7. **Public surface:** expose supported syntax, stable CLI behavior, documented data formats and minimum integration obligations. Omit unpublished design history, private workflow details, local paths and internal implementation maps unless required by a supported integration.
8. **Evidence:** implemented claims MUST be backed by code and conformance tests. Proposals, registries and architectural diagrams alone do not establish implementation.

## Review gate

Before publication, verify examples against the current interpreter, run the relevant test suite, resolve internal links, label reserved and planned behavior, and remove private provenance and unnecessary internal detail. When prose conflicts with executable conformance tests, the tests and versioned specification take precedence.
