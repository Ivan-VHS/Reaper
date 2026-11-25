# Reaper as a systems and hardware language

**Language authority:** [Reaper Language Canon v1](LANGUAGE_CANON.md)  
**Author and project maintainer:** Ivan-VHS  
**Status:** architecture and first checked MMIO adapter contract  
**Scope:** language, compiler, runtime, embedded targets and Reaper Studio

All source-level constructs described here are subordinate to the [Language Canon](LANGUAGE_CANON.md). A hardware example or target proposal is not accepted `.rpr` syntax until it has a versioned grammar rule, semantic/type/effect contract, implementation and conformance tests.

Reaper is being repositioned from a flow-first general-purpose language toward a systems language for firmware, embedded software, platform services and hardware-adjacent development. The existing .rpr surface and Python runtime remain part of the compatibility product while a native compiler path grows toward the canonical execution route.

This document separates what is already in the repository from the target design. A syntax proposal or registry entry is not an implemented compiler feature.
