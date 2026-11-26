# Typed craft signatures and explicit result contracts v1

**Status:** partial Reaper-native frontend milestone  
**Source of truth:** the .rpr parser and signature validator in this directory

## Syntax

A craft can declare parameter types, a return type, and type parameters:

\`\`\`reaper
craft identity<T>(value: T) -> T {
    yield value
}

craft parse_count(raw: text) -> Result<Option<u64>, ParseError> {
    when raw == "" {
        yield err("empty input")
    } otherwise {
        yield ok(some(42))
    }
}
\`\`\`

The signature type grammar is deliberately small:

\`\`\`text
Type       := Identifier [ "<" Type ( "," Type )* ">" ]
Parameter  := Identifier [ ":" Type ]
Signature  := "craft" Identifier [ "<" Identifier ( "," Identifier )* ">" ]
              "(" [ Parameter ( "," Parameter )* ] ")"
              [ "->" Type ]
\`\`\`

Result<T, E> has exactly two type arguments: success value T and error value E. Option<T> has exactly one type argument. Generic functions can use declared type parameters such as T in parameter and return positions. Named types resolve against the program's struct, union, and enum declarations.

## AST compatibility

Untyped functions preserve the legacy function metadata [name, parameter_names]. A typed function uses:

\`\`\`text
[name, parameter_names, parameter_types, return_type, generic_parameters]
\`\`\`

Each type expression is represented as [type_name, type_arguments]. This gives the bootstrap parser a recursive representation without erasing token line and column information held by the AST node.

## Static checks in this milestone

The Reaper-written validator checks:

- parameter-name/type-count agreement and duplicate parameter names;
- duplicate or reserved generic parameter names;
- primitive names and user-declared nominal type names;
- generic arity for Result and Option;
- nested generic type expressions and references to declared generic parameters;
- explicit return constructors for the current Result and Option syntax: ok(value), err(error), some(value), and nothing;
- duplicate top-level craft names.

The conformance program is itself written in Reaper and is invoked by the existing typed-platform workflow.

## Explicit limitations

This is not a complete static type checker or a complete implementation of the language's error model. In particular, this milestone does **not** yet provide:

- payload-type inference or checking that the value inside ok, err, or some matches its declared generic argument;
- definite-return analysis across every control-flow path;
- postfix ? propagation or automatic propagation across calls;
- runtime Option values or an integrated standard-library runtime API;
- generic inference, bounds, trait constraints, monomorphization, generic structs, or generic methods;
- trait / impl declarations;
- ownership, borrowing, regions, or deterministic drop;
- production parser/typechecker integration, typed HIR/MIR/LIR, or native aggregate/function ABI lowering.

The Result/Option return check is a structural bootstrap rule over yield expressions, not proof of whole-function type safety. These limitations are intentional and remain separate acceptance gates.

## Validation

The workflow executes:

\`\`\`sh
python -m reaper selfhost/lexer.rpr
python -m reaper selfhost/program_parser.rpr
python -m reaper selfhost/typed_signature_tests.rpr
\`\`\`

The reference runtime is used only as the current execution host for Reaper source. The parser and signature validation implementation added by this milestone are .rpr programs.
