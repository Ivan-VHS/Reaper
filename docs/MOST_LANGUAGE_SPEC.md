# МОСТ — exact Russian keyword aliases

МОСТ is a lexical spelling profile for Reaper, not a second language. Alias normalization must produce the same token stream, AST and runtime behavior.

| Layer | Count | Status |
|---|---:|---|
| Runtime aliases | 21 | executable in reference subset |
| Additional aliases | 33 | lexically reserved |
| Total exact aliases | 54 | no stemming or synonym inference |

Examples: `пусть → make`, `функция → craft`, `вернуть → yield`, `вывести → emit`, `если → when`, `иначе → otherwise`, `для → each`, `пока → while`.

Reserved words do not imply grammar/runtime support. See [MOST implementation ledger](MOST_IMPLEMENTATION_STATUS.md).
