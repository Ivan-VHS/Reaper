# LSP semantic tokens

The stdio language server now advertises `textDocument/semanticTokens/full` and returns standard delta-encoded semantic tokens.

The current lexical categories cover keywords, built-ins, user identifiers, function/variable declarations, comments, strings, numeric literals and operators. Position and token lengths are encoded in UTF-16 code units, matching the LSP coordinate contract. Declaration tokens carry the `declaration` modifier.

This is lexical highlighting, not a type checker or semantic compiler pass. The language service only analyzes explicitly opened documents; it does not crawl the disk or execute source while producing tokens. Unsupported or unknown documents return the normal invalid-params response.

## Catalog links

This adopts the language-server/editor integration patterns represented by clangd, gopls, TypeScript Language Server, lua-language-server and the LSP specification (catalog items 323–360). No third-party server code is copied into Reaper.
