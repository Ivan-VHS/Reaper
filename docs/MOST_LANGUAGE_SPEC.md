# МОСТ — exact Russian keyword aliases

МОСТ is a lexical spelling profile for Reaper, not a second language. Alias normalization produces the same canonical tokens, AST and runtime behavior as the corresponding English syntax.

| Layer | Count | Status |
|---|---:|---|
| Runtime aliases | 31 | executable in the Python reference grammar |
| Additional aliases | 23 | lexically reserved; not yet executable |
| Total exact aliases | 54 | no stemming or synonym inference |

Executable forms include declarations, functions, return, conditionals, loops, break/continue, imports/exports and core expressions. Examples: `пусть → make`, `связать → let`, `изменяемый → mut`, `процедура → fn`, `вернуть → yield`, `возврат → return`, `условие → if`, `альтернатива → else`, `для_каждого → for`, `прервать → break`, `продолжить → continue`.

Reserved forms such as `структура`, `перечисление`, `типаж`, `реализация`, `асинхронно` and `ожидать` still do not imply parsing or runtime support.

See [MOST implementation ledger](MOST_IMPLEMENTATION_STATUS.md) and [Language Reference 0.2](LANGUAGE_REFERENCE_0.2.md).
