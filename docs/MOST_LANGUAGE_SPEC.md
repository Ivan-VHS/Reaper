# REAPER / МОСТ — единая спецификация русского профиля

**Статус:** МОСТ — русская запись языка REAPER, а не отдельный язык с независимыми правилами. REAPER является единственным источником грамматики, типов, семантики, IR, runtime, ABI и backend. МОСТ заменяет ограниченный набор ключевых слов REAPER точными русскими лексическими псевдонимами. Реализация C17 и Python reference runtime принадлежат REAPER; отдельные компилятор, AST, библиотека исполнения или backend для МОСТ не создаются.

## Единые инварианты REAPER / МОСТ

1. No subject-oriented receiver keywords. `@` denotes the current lexical receiver/context.
2. No implicit allocation, conversion, thread creation, exception unwinding, or ambient global state.
3. Static types, immutable bindings by default, explicit mutation, explicit effects.
4. No tracing garbage collector. Region/arena allocation and linear resource ownership are checked statically.
5. A single source model lowers to verified typed IR, then to native or WASM backends.
6. The Python interpreter remains a compatibility oracle until the native implementation passes differential conformance; it is not a MOST backend.
7. Every capability has an implementation state and executable acceptance tests. Roadmap text never counts as implementation.
8. Russian is the primary source-language vocabulary of MOST; compatible REAPER syntax remains available and shares the same semantics.
9. Morphology and synonyms are explicit, scoped lookup tables. The compiler never guesses a program meaning from unrestricted natural-language text.
10. Unicode validation and source mapping are общие контракты REAPER; spoken prosody and voice recognition are external host concerns.
11. МОСТ does not define its own parser, grammar engine, AST, type checker, standard library, runtime, bytecode, ABI or backend.
12. A Russian keyword is an exact alias of one existing REAPER keyword/token. Aliases may not add a new operation or alter evaluation semantics.
13. No automatic stemming, case inference, free-form synonym resolution or probabilistic intent selection is part of compilation. Use exact spellings and ordinary REAPER identifiers.

## Каноническая русская запись

МОСТ использует только конструкции REAPER. Русские слова — точные написания уже существующих ключевых слов; типы, операторы, приоритеты, области видимости, ошибки и вычисления принадлежат REAPER.

### Рабочее подмножество

~~~most
функция удвоить(значение) {
    вернуть значение * 2
}

пусть значение := 5
переменная итог := 0

для элемент в range(1, 4) {
    изменить итог := итог + удвоить(элемент)
}

если итог == 12 {
    вывести "готово"
} иначе {
    вывести "ошибка"
}
~~~

Этот пример выполняется в Python reference runtime REAPER через существующие конструкции Reaper: \`craft/yield\`, \`make/vary/change\`, \`each/in\`, \`when/otherwise\` и \`emit\`. Он не создаёт отдельную модель исполнения МОСТ.

### Точное соответствие ключевых слов

| Русское написание | Единственное соответствие REAPER |
|---|---|
| пусть | make |
| переменная | vary |
| изменить | change |
| функция | craft |
| вернуть | yield |
| вывести | emit |
| если | when |
| иначе | otherwise |
| для | each |
| в | in |
| цикл | loop |
| пока | while |
| истина / ложь / ничего | true / false / nothing |
| и / или / не | and / or / not |
| импорт / экспорт / как | import / export / as |
| модуль / структура / перечисление / типаж | module / struct / enum / trait |
| тип / константа / область / арена / сигнал | type / const / region / arena / signal |
| асинхронно / ожидать | async / await |
| тест / вычислить_при_сборке | test / comptime |
| требует / гарантирует | requires / ensures |
| небезопасно / внешний / где | unsafe / extern / where |
| прервать / продолжить / отложить / уничтожить | break / continue / defer / drop |
| сказать / спросить | документированные host/API-псевдонимы; не новые runtime-операции |

Псевдоним становится зарезервированным словом только там, где его английский оригинал уже является ключевым словом REAPER. Русские названия типов и переменных, например \`счётчик\`, \`состояние\`, \`целое32\`, — обычные идентификаторы, а не новые встроенные типы или ключевые слова.

### Только REAPER-совместимая поверхность

- Исходная грамматика — грамматика REAPER; русское слово заменяет только соответствующий ключевой токен.
- Существующий оператор потока REAPER \`::\` сохраняет точную семантику.
- Существующие значения, функции, коллекции, модули, типы и ошибки не дублируются под другой runtime.
- Неподдерживаемая конструкция REAPER остаётся неподдерживаемой и в МОСТ; русский псевдоним не делает её исполняемой.
- Фрагмент МОСТ должен после замены псевдонимов давать тот же REAPER-код и тот же результат.

### Что не входит в МОСТ

Нет отдельной русской грамматики свободного порядка слов, самостоятельной морфологической модели, автоматического склонения, синонимического угадывания, голосового парсера, новых типов, нового стандарта библиотеки или своего AST. Для нескольких имён используются обычные идентификаторы, функции, модули и aliases, уже предусмотренные REAPER.

## Compiler pipeline

`UTF-8 source → exact Russian keyword alias mapping → REAPER token stream → REAPER parser/AST → REAPER name/type/effect checks → REAPER ownership/region analysis → REAPER Canonical IR → REAPER verifier/optimizer → existing REAPER backends`.

The REAPER IR remains immutable, source-mapped, deterministic and independently verifiable. The alias layer does not emit or own an AST/IR. The same REAPER parser and backend consume both spellings.

## Memory and safety model

- **Regions:** lexical region scopes own bulk allocations; escape analysis prevents references outliving a region.
- **Borrows:** shared immutable borrows may alias; mutable borrows are exclusive. The compiler rejects overlapping mutable access.
- **Linear resources:** file/socket/lock handles are consumed by close, transfer, or a verified scope destructor exactly once.
- **Raw operations:** pointer arithmetic, inline assembly and hardware access require an explicit unsafe function/block and are excluded from safe proofs.
- **Slices:** pointer-plus-length values carry bounds; safe indexing checks bounds or is proven safe.
- **Drop:** deterministic reverse declaration order; cleanup paths are inserted on every control-flow exit.
- **Arithmetic:** checked by default; wrapping and saturating operators are distinct semantics.
- **Optionals:** tagged option types; pointer niche optimization is permitted only when ABI and validity rules prove it sound.

A region allocator is not a substitute for borrow checking. Runtime tests alone cannot establish memory safety.

## Types and language semantics

The type system includes fixed-width integers, floats, booleans, UTF-8 strings/slices, arrays, tuples, structs, enums with payloads, option/result types, function types, traits, and explicit pointer/ABI types. Exhaustive matching is a compile-time property. Generic monomorphization and compile-time evaluation must be bounded and deterministic.

`::` passes the left expression as the first argument. `??` unwraps an optional with a fallback. `+%` is wrapping addition; `+|` is saturating addition. More than two call arguments require labels in canonical source mode. Effects (I/O, allocation, mutation, unsafe, async) are explicit in function signatures or verified effect declarations.

## Web and WASM boundary

The web layer is a typed host binding, not a second dynamic language. DOM nodes, events, Canvas, WebGL, WebGPU, Fetch and AudioContext are represented by capability-bearing handles. Signals compile to direct dependency updates; no Virtual DOM is required. UI syntax lowers through the same AST and typed IR. Strings are escaped by default; trusted HTML requires a distinct unsafe-capability type.

The browser still supplies Web APIs and a JavaScript host boundary where the platform requires it. MOST removes application-framework dependence; it cannot make browser APIs cease to exist. Server rendering, hydration, routing and CSS scoping are separate milestones.

## Native and C interoperability

C ABI declarations must specify layout, alignment, calling convention, ownership and error mapping. Header ingestion begins with a constrained declarator parser; full preprocessing and arbitrary macro evaluation are not assumed. SIMD abstractions lower per target with scalar fallbacks. Endian wrappers and bit-width integers have explicit serialization rules. Bare-metal targets require a documented target description and linker/runtime contract.

## 66-rule language-formation ledger

The 66 human-language principles are used only to improve the Russian readability, consistency and learnability of REAPER's surface syntax. They do not authorize a second compiler, new semantics, morphology engine or separate runtime. See [MOST_RUSSIAN_66_RULES.md](MOST_RUSSIAN_66_RULES.md).

| Rules | MOST interpretation | Acceptance owner |
|---|---|---|
| 1–11 | Clear commands, functions, scopes, explicit results, quantities, capabilities and teachable examples | Grammar, symbols, types, effects, docs |
| 12–22 | Reuse of REAPER modules, imports, naming and compatibility policy | Existing REAPER modules and package/version manager |
| 23–33 | Contrastive spelling, Unicode identifiers, formatter rules and strict separation of written syntax from speech | Lexer, Unicode validator, formatter, optional host adapter |
| 34–44 | Exact aliases, REAPER identifiers, composition and existing import/API contracts | Existing REAPER lexer, parser, name resolver and standard library |
| 45–55 | Exact REAPER grammar, fixed token mapping, typing, provenance and grammar versioning | Existing REAPER parser and type/effect checker |
| 56–66 | Learnability, stable core, composition, bounded recursion, introspection, documentation and governed evolution | Runtime, tooling, CI, edition policy |

The human-language mechanisms do not become hidden execution behavior: intonation does not change syntax, tone does not change values, social prestige does not select overloads, and natural-language ambiguity is a compile error. See the linked document for the complete rule-by-rule mapping and delivery stages.

## Delivery phases and truthful status

- **M0 — Russian aliases:** map exact Russian spellings to existing REAPER keyword tokens. The Python compatibility subset is executable; the C17 lexer recognizes the Russian vocabulary.
- **M1 — REAPER grammar:** complete the existing REAPER parser once; the Russian aliases are accepted by this same parser, with no MOST grammar fork.
- **M2 — REAPER semantic core:** symbol tables, static types, inference, ADTs, exhaustive match, contracts and typed REAPER IR.
- **M3 — Safe memory:** regions, borrows, move/linear checking, slices, drop elaboration and allocator interfaces.
- **M4 — Native executable:** portable object/ELF first, then PE and Mach-O; C ABI and target-specific codegen.
- **M5 — WASM:** WASI and browser WASM targets, host bindings, UI and signals.
- **M6 — Toolchain:** tests, fuzzing, docs tests, profiler, reproducible builds, package hashes and self-hosting.

No claim of sub-5-MB self-hosting, full C-header parsing, 15-KB universal web bundles, constant-time cryptography, all-platform cross-compilation, or 30-year ABI stability is made until independently measured and tested.

## Compatibility policy

The REAPER 1.0 core grammar and semantics are authoritative for both English and Russian spellings. A change to REAPER grammar automatically governs МОСТ aliases; there is no independent MOST edition or compatibility promise. Security fixes and compiler bug fixes must not silently change valid program meaning.


## 147-feature architecture extension

The extended architecture backlog, including all 147 proposed capabilities, semantic constraints, platform caveats, duplicate resolution, implementation waves and truthful status ledger, is maintained in [MOST_147_FEATURE_REGISTRY.md](MOST_147_FEATURE_REGISTRY.md). The registry extends the 66 foundational rules; it does not imply that the listed features are already implemented. The canonical numbering is normalized to seven non-overlapping groups (1–21 through 127–147).
