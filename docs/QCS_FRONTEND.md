# QCS frontend for Reaper

QCS 1.0 is a hardware-domain syntax frontend integrated into the Reaper Python package.

## Commands

    reaper-qcs check examples/qcs_irq.qcs
    reaper-qcs tokens examples/qcs_irq.qcs
    reaper-qcs ast examples/qcs_irq.qcs
    reaper-qcs check --json examples/qcs_irq.qcs

The same commands are available without installing the console entry point:

    python -m reaper.qcs check examples/qcs_irq.qcs

## Syntax

- [@ ... @] opens a hardware or semantic frame.
- [@ end @] closes the current frame.
- then sequences operations.
- send transfers a value to a receiving operation.
- back returns a resource to its owner or pool.
- state:! declares a required invariant; state:? marks an optional or not-ready state; state:deferred marks deferred work.

Type arguments use parentheses, for example RingBuf(Int16) and Vec4(Float32).
Angle brackets, vertical bars and tildes are rejected by the QCS lexer outside strings and comments.

## Scope and safety

The frontend provides source-located tokens, a recursive-descent parser, a Pratt expression parser, a JSON-serializable AST and a hardware-domain registry covering the 65 distinct frame domains in the 66-language design catalogue.

Domain recognition is not a compiler backend. Parsing domain:dma does not execute DMA, and state:! is a declared contract rather than a formal proof. Type checking, ownership proofs, constant-time verification, hardware lowering and native code generation remain separate future stages.

Run the focused suite with:

    python -m unittest tests.test_qcs -v
