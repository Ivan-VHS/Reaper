# Contributing to Reaper

Reaper is a flow-first language with a Python compatibility reference runtime and a separately evolving native C17 track. Keep syntax, semantics, diagnostics, runtime limits and language-service contracts aligned.

## Before opening a pull request

1. Include a minimal .rpr reproduction and the exact command/editor action.
2. Treat source as untrusted input; preserve parser, instruction, collection, text, heap and open-resource limits.
3. Do not describe reserved grammar or roadmap entries as executable capabilities.
4. Keep diagnostic codes stable; add a new code rather than repurposing an existing one.
5. Keep FFI disabled unless a user explicitly opts in; document any new native trust boundary.
6. Update affected localized READMEs and the relevant contract in docs/.

## Local verification

~~~sh
python -m unittest discover -s tests -v
python -m reaper --check examples/flow.rpr
git diff --check
~~~

When native components change, also configure and run the repository's CMake/CTest targets. If NOO TAH changes, run its Node.js compatibility workflow/tests as documented.

## Pull request expectations

Explain grammar and compatibility impact, resource bounds, diagnostics, runtime behavior and test coverage. Include a short .rpr example for syntax changes. Do not promote partial native C17 behavior to full language support.

## Security

Do not commit secrets or untrusted native libraries. Treat DAP launches and explicitly enabled FFI as execution of trusted local code. See [SECURITY.md](SECURITY.md).
