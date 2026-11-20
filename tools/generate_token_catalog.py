#!/usr/bin/env python3
"""Regenerate the packaged JSON and native C table from the canonical catalogue."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "language" / "token_catalog.json"

def render_c(data: dict) -> str:
    rows = []
    for item in data["tokens"]:
        values = (f'{item["ordinal"]}u', item["lexeme"], item["group"],
                  item["category"], item["name"], item["description"])
        encoded = (values[0], *(json.dumps(v, ensure_ascii=False) for v in values[1:]))
        rows.append("    {" + ", ".join(encoded) + "}")
    return '''#include "reaper/token_catalog.h"
#include <string.h>

static const ReaperCatalogEntry CATALOG[] = {
''' + ",\n".join(rows) + '''
};

size_t reaper_token_catalog_count(void) { return sizeof CATALOG / sizeof CATALOG[0]; }
const ReaperCatalogEntry *reaper_token_catalog_at(size_t index) {
    return index < reaper_token_catalog_count() ? &CATALOG[index] : NULL;
}
const ReaperCatalogEntry *reaper_token_catalog_lookup(const char *lexeme) {
    if (lexeme == NULL) return NULL;
    for (size_t i = 0; i < reaper_token_catalog_count(); ++i)
        if (strcmp(CATALOG[i].lexeme, lexeme) == 0) return &CATALOG[i];
    return NULL;
}
int reaper_token_catalog_validate(void) {
    static const char alphabet[] = ":;[{]}+=_-*";
    if (reaper_token_catalog_count() != 666u) return 0;
    for (size_t i = 0; i < reaper_token_catalog_count(); ++i) {
        const char *token = CATALOG[i].lexeme;
        if (token == NULL || strlen(token) != 3u || CATALOG[i].ordinal != i + 1u) return 0;
        for (size_t j = 0; j < 3u; ++j)
            if (strchr(alphabet, token[j]) == NULL) return 0;
        for (size_t k = i + 1u; k < reaper_token_catalog_count(); ++k)
            if (strcmp(token, CATALOG[k].lexeme) == 0) return 0;
    }
    return 1;
}
'''

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    expected = {
        ROOT / "reaper" / "token_catalog.json": json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        ROOT / "src" / "token_catalog.c": render_c(data),
    }
    stale = []
    for path, content in expected.items():
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                stale.append(str(path.relative_to(ROOT)))
        else:
            path.write_text(content, encoding="utf-8")
    if stale:
        print("Generated files are stale: " + ", ".join(stale))
        return 1
    print("Token catalogue generated files are up to date.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
