# Native HIR, MIR and LIR status

## Current front-end pipeline

The C17 frontend separates parsing from semantic validation:

~~~text
.rpr source
  -> UTF-8-aware lexer
  -> Pratt expression and statement parser
  -> owned flat AST
  -> HIR name, scope, mutability and type checks
~~~

The native program AST has nodes for declarations, mutable bindings, functions and parameters, blocks, yield/emit, conditionals, each/while loops, lists, calls, indexing and the :: pipeline.

The HIR pass owns its node and symbol storage. It checks lexical scope, shadowing, duplicate declarations, make versus vary mutability, change assignments, function parameters, call arity, built-in arity, basic operator types, boolean conditions, list iteration, yield placement and the pipeline rule that inserts the left value as the first argument to the right-hand operation.

The inferred type set is unit, i64, f64, bool, string, list, function and unknown. Unknown stays explicit when source syntax does not declare a type or an expression depends on runtime values. Generic inference and whole-program effect analysis are not yet implemented.

## MIR — planned control-flow representation

MIR is not yet a compiler stage. The next representation is designed around:

- one function per craft plus a generated program entry;
- explicit local slots, typed values and call arguments;
- basic blocks with jump, conditional branch or return terminators;
- when as branch and join blocks;
- loop while as condition/body/exit blocks with a back edge;
- each as iterator-init/iterator-next plus branch;
- :: as a call with the piped value inserted at argument zero;
- source locations retained for diagnostics and debug information.

MIR verification will reject missing terminators, invalid block targets, local-slot errors and use-before-definition. The source-level parser does not itself make a loop executable.

## LIR — current expression representation

ReaperIrModule is the existing bounded, topologically ordered value IR for signed-i64 expressions. It contains constants, checked addition/subtraction/multiplication/division and one final return. The System V and DABI64 expression backends currently consume this representation.

This is not yet a general LIR: there are no function boundaries, virtual-register allocation, call ABI lowering, memory operations, branches, source maps or relocations.

## Targets

- x86_64-sysv emits GNU assembly using the System V ELF function convention.
- duckos-dabi64-v1 emits GNU assembly using the separate DuckOS DABI64 v1 frame/result convention and .note.duckos.abi.

The DABI64 expression entry validates its frame magic/version/size, current no-argument layout, flags and result-slot alignment. It emits explicit status codes and writes its typed result only on success.

## Object and runtime boundary

Both backends still emit assembly text; the host assembler/linker creates test objects. Reaper does not yet write relocations or link a DuckOS executable. DuckOS has a versioned ABI header and host-tested frame/result validators, but no kernel syscall dispatcher, ELF loader, process startup or runtime library yet.

A construct is considered natively compiled only after AST representation, HIR semantics, MIR lowering, verified LIR, target code generation and executable tests exist. Parser support alone is not compilation.
