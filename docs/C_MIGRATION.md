# Native C Migration

**Target:** a self-contained Reaper implementation in portable C17, with an optional C23 upgrade after compiler support is established.

## Migration rule

The Python implementation remains the semantic reference until the C implementation passes the same conformance suite. Do not delete or bypass reference tests before parity is demonstrated. The final release must not require Python for build, test, installation, or execution.

## Native architecture

    src/
      main.c          CLI, file loading, exit-code contract
      lexer.c         UTF-8 byte-oriented scanner and source locations
      parser.c        recursive-descent statements + Pratt expressions
      ast.c           owned AST nodes and destruction
      value.c         tagged values, strings, lists and numeric semantics
      env.c           lexical environments and mutable bindings
      runtime.c       evaluator, closures, built-ins and execution budgets
      systems.c       the 20-track engineering contract registry
    include/reaper/   public C interfaces
    tests/            C unit and language conformance tests

The initial native commit establishes the C17 build, public lexer contract, native CLI bring-up mode, and lexer tests. It is deliberately not advertised as a complete interpreter.

## Semantic compatibility requirements

The C runtime must preserve make/vary/change; craft, lexical closures, recursion and yield; when/otherwise, each and loop while; nothing, booleans, numbers, UTF-8 text and lists; operator precedence, short-circuit logic and left-associative flow; all documented built-ins; source diagnostics; and all execution/resource limits.

## Memory and error model

Every allocation has a documented owner. AST nodes and tokens have explicit destructors. Runtime values use a tagged union with clear copy/move rules; closures retain their lexical environment safely. Allocation failure becomes a controlled host error. Never use non-local jumps across owned resources. Arithmetic checks division by zero, overflow and non-finite floating-point results.

## Build and test

Requires a C17 compiler and CMake 3.16+.

    cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
    cmake --build build --parallel
    ctest --test-dir build --output-on-failure

## Completion gates

1. Native lexer and diagnostics.
2. Parser and owned AST.
3. Tagged values, lexical environments and evaluator.
4. Closures, control flow, built-ins, flow operator and limits.
5. Differential conformance: every existing .rpr fixture produces the same output or corresponding diagnostic in Python and C.
6. Native CLI parity (--check, --steps, --items, --text-length, --systems, --version).
7. Native-only CI and build/install documentation.
8. Remove Python package and Python CI only after the parity gate is green.
