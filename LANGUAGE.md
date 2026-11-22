# Reaper language — expressive reference runtime

Reaper is an expression-oriented language with a Python-hosted compatibility runtime and a
separate, incomplete native C17 compiler track. The Python reference runtime supports the
constructs below; native C17 parity is not implied.

## Bindings and functions

\`\`\`reaper
make fixed := 7
vary current := 1
change current := current + fixed

craft double(value) { yield value * 2 }
\`\`\`

\`make\` declares an immutable binding, \`vary\` a mutable binding, \`change\` updates a mutable
binding, \`craft\` declares a closure-capable function, and \`yield\` returns from a function.
It does not create a resumable generator.

## Conditions, matching and destructuring

\`\`\`reaper
emit true ? "yes" : "no"
emit nothing ?? "fallback"

make user := {profile: {avatar: "duck"}}
emit user?.profile?.avatar
emit user?.profile?.missing ?? "no image"

match Ok(42) {
    case Ok(value) if value > 40 { emit value }
    case Err(message) { emit message }
    case _ { emit "unknown" }
}

craft first(values) {
    let [head, tail] := values else { yield nothing }
    yield head
}
\`\`\`

Patterns support literals, bindings, \`_\`, fixed-length lists, maps and the built-in tagged
variants \`Ok\`, \`Err\` and \`Some\`. A guard is an \`if\` expression after the pattern. A failing
\`let ... else\` branch must leave the current function (for example, with \`yield\`).

\`?.\` supports map keys, sequence \`length\`, and optional index \`?.[index]\`. A missing member,
out-of-range optional index or \`nothing\` base yields \`nothing\`.

## Ranges and comprehensions

\`\`\`reaper
emit 4 in 1..5
emit 5 in 1..=5
emit [x * 2 for x in 1..8 if x % 2 == 0]
emit zip([1, 2], ["a", "b"])
emit enumerate(["x", "y"], 4)
\`\`\`

\`..\` has an exclusive end; \`..=\` includes the end. List comprehensions accept one finite
source and an optional filter. Their input and output obey the configured collection limit.

## Functional composition and transducers

\`\`\`reaper
craft add(a, b) { yield a + b }
craft double(x) { yield x * 2 }

emit compose(double, double)(3)
emit partial(add, 10)(5)
emit curry(add, 2)(10)(5)
emit transduce(1..20, filtering(positive), mapping(double), taking(4))
\`\`\`

\`compose(f, g)\` applies right-to-left; \`pipe_fn(f, g)\` applies left-to-right.
The \`::\` operator is Reaper's value-pipeline spelling:
\`values :: map(double) :: keep(positive) :: sum()\`.

The transducer helpers are \`mapping(fn)\`, \`filtering(fn)\` and \`taking(n)\`. They are consumed
by a single bounded \`transduce(values, ...steps)\` pass and do not materialize intermediate
mapped/filtered lists.

## Result values, memoization and contracts

\`\`\`reaper
craft recover(message) { yield "recovered: " ++ message }
make outcome := try_result(double, 4)
emit is_ok(outcome)
emit unwrap(outcome)
emit or_else(Err("offline"), recover)
emit invariant_guard(2 + 2 == 4, "math invariant")
\`\`\`

Built-in tagged results: \`Ok(value)\`, \`Err(error)\`, \`Some(value)\`.
Helpers: \`is_ok\`, \`is_err\`, \`is_some\`, \`unwrap\`, \`or_else\`, \`try_result\`.
Runtime contract helpers: \`requires\`, \`ensures\`, \`invariant_guard\`.

\`memoize(fn, max_entries)\` uses a bounded cache. \`memo_ttl(fn, ttl_ms, max_entries)\` adds a
monotonic expiration time. Cache wrappers are local to the returned function; use them with
pure functions or explicitly account for captured mutable state.

## Limits and compatibility

The interpreter bounds steps, recursion depth, collections, text, managed heap and open
resources. The new expressive AST forms are shared by tree-walk and VM execution; the VM
currently delegates those AST forms to the Python reference evaluator. The native C17 track
does not yet implement this syntax.

See [the 66-construct maturity map](docs/EXPRESSIVE_CONSTRUCTS_66.md) and
[runtime limits](docs/RUNTIME_PLATFORM.md).
