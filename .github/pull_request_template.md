## What changed

Describe the user-visible result and the language/tooling layer affected.

## Verification

- [ ] Python unit tests pass.
- [ ] Native tests pass when native components changed.
- [ ] CLI, LSP and DAP behaviour is consistent where relevant.
- [ ] New diagnostics have stable codes and help text.

## Language and safety review

- [ ] New syntax is documented and not merely reserved.
- [ ] Resource budgets and FFI opt-in remain intact.
- [ ] Existing source compatibility is preserved or explicitly versioned.
- [ ] No automatic source rewrite or network side effect was introduced.
- [ ] No private source, credentials or generated build artefacts were added.
