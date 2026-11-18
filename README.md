# Reaper

**Reaper is an independent, flow-first programming language.** Its surface is designed to stay readable, make mutation explicit, and let values move through composable transformations.

Reaper 0.1 turns the accompanying design manifesto into an executable first milestone: it includes a lexer, parser, tree-walking interpreter, command-line runner, examples, documentation, and tests.

## First program

~~~reaper
craft double(value) {
    yield value * 2
}

make numbers := [1, 2, 3, 4]
make answer := numbers ~> map(double) ~> sum()
emit "answer = " ++ text(answer)
~~~

The central operator ~> passes the value on its left as the first argument to the operation on its right. make creates an immutable binding. Use vary for a mutable binding and change to reassign it.

## Run Reaper

Requires Python 3.10 or newer. The interpreter has no third-party runtime dependencies.

~~~sh
python -m reaper examples/hello.rpr
python -m reaper examples/flow.rpr
python -m reaper --check examples/flow.rpr
python -m reaper --target-info
python -m reaper --items 50000 --text-length 500000 examples/flow.rpr
~~~

To install the reaper command:

~~~sh
python -m pip install -e .
reaper examples/hello.rpr
~~~

## Included in 0.1

- Position-aware lexer with Unicode identifiers, comments, and escaped text literals.
- Recursive-descent statement parser and Pratt expression parser.
- Immutable make bindings; explicit vary and change mutation.
- Functions, lexical closures, recursion, and yield.
- Lists, indexing, arithmetic, comparisons, booleans, and strict text concatenation.
- when / otherwise, each, and loop while.
- Flow composition with ~>, map, keep, fold, sum, and related built-ins.
- Explicit console effects through emit, say, and ask.
- Source-aware diagnostics, instruction budget, bounded function-call depth, collection-item limits and text-concatenation limits.
- Standard-library unit tests and GitHub Actions CI for Python 3.10–3.12.

## Documentation

- LANGUAGE.md — language design, syntax and runtime limits.
- docs/ARCHITECTURE.md — implementation layers and product boundaries.
- docs/ARCHITECTURE_66.md — 66 enforceable autonomy, modularity and safety requirements.
- docs/AETHER_ANAS_ROADMAP.md — staged AETHER-ANAS integration plan with explicit implementation status and acceptance gates.
- docs/CONSTITUTION_666_PROFILE.md — project-specific application of all six sections and 666 constitutional rules, with conformance states and staged implementation.
- docs/ELBRUS_E2K.md — E2K host identification and the staged AETHER-ANAS backend boundary.
- docs/CHINESE_PROVERBS_100_ENGINEERING_CROSSWALK.md — source-derived 100-item engineering ledger with defensive security interpretation and evidence gates.
- examples/ — runnable programs.
- tests/ — conformance, boundary and runtime tests.

Run the standard-library test suite with `python -m unittest discover -s tests -v`.

## Roadmap

Reaper starts with a small, executable core. Static type checking, explicit effect types, safe foreign-function boundaries, bytecode/native backends, structured concurrency, semantic graph tooling, package management, and self-hosting are future milestones. GPU and distributed execution will only be claimed after actual backends and conformance tests exist. See the [AETHER-ANAS integration roadmap](docs/AETHER_ANAS_ROADMAP.md) for the staged design and acceptance gates.
Reaper starts with a small, executable core. Static type checking, explicit effect types, safe foreign-function boundaries, bytecode/native backends, structured concurrency, semantic graph tooling, package management, and self-hosting are future milestones. GPU and distributed execution will only be claimed after actual backends and conformance tests exist.

## License

Reaper is distributed under the Apache License 2.0. See LICENSE.
