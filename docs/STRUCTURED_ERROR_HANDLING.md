# Structured error handling

Reaper's Python reference runtime supports a structured error-handling statement:

```reaper
attempt {
    emit "starting"
    emit 10 / 0
} recover failure {
    emit "recovered"
} finally {
    emit "cleanup"
}
```

The clauses have the following contract:

- `attempt` executes its body in a nested lexical scope.
- `recover name` is optional. It runs only after a `ReaperRuntimeError`; `name` is bound to the diagnostic text in a recovery-local scope.
- `finally` is optional. It runs after normal completion, a recovered error, an uncaught language error, or an early `yield`.
- At least one of `recover` or `finally` is required. Clause order is `recover` followed by `finally`.
- `ExecutionLimitError` is deliberately not recoverable. A program cannot catch its way out of the configured execution budget.
- Errors raised by arbitrary host callbacks are not converted into language exceptions by this statement.

## Russian aliases

The МОСТ lexical profile accepts exact aliases:

| Reaper | Russian alias |
|---|---|
| `attempt` | `попытка` |
| `recover` | `обработать` |
| `finally` | `наконец` |

Example:

```reaper
попытка { вывести 1 / 0 }
обработать ошибка { вывести "caught" }
наконец { вывести "closed" }
```

## Execution engines and limits

The feature is implemented in the Python reference tree-walk interpreter and the canonical IR/stack VM. The same language tests exercise both engines, including cleanup during function return. The native C17 parser/runtime, Node.js integration, and the optional peer-project C ABI adapters do not yet implement this statement; no native parity is implied.

Run the example and tests with:

```sh
python -m reaper examples/error_handling.rpr
python -m unittest tests.test_language -v
```
