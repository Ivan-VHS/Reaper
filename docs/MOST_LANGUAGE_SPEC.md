# МОСТ — exact Russian keyword aliases

**Normative parent contract:** [Reaper Language Canon v1](LANGUAGE_CANON.md)  
**Machine registry:** [`language/most_keyword_aliases.json`](../language/most_keyword_aliases.json)

МОСТ is a lexical spelling profile for Reaper, not a second language. It maps exact Russian spellings to existing canonical Reaper keyword spellings. After alias normalization, parsing, AST shape, type rules, IR and runtime behavior MUST be identical to the corresponding canonical Reaper source.

| Layer | Count | Status |
|---|---:|---|
| Runtime aliases | 21 | Executable in the reference-runtime subset |
| Additional aliases | 33 | Lexically reserved |
| Total exact aliases | 54 | No stemming, morphology or synonym inference |

Examples: `пусть → make`, `функция → craft`, `вернуть → yield`, `вывести → emit`, `если → when`, `иначе → otherwise`, `для → each`, `пока → while`.

Reserved aliases do not imply grammar, type-checker, VM or native-backend support. A reserved alias MUST NOT be presented as executable until its canonical spelling is implemented and covered by the same conformance suite.

МОСТ cannot add operators, alter evaluation order, change capabilities or introduce a separate runtime. See [MOST implementation status](MOST_IMPLEMENTATION_STATUS.md) for the evidence-backed support count.
