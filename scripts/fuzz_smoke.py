#!/usr/bin/env python3
"""Deterministic bounded fuzz-smoke corpus for Reaper's real lexer and parser."""
from __future__ import annotations

import random
import string

from reaper.errors import LexError, ParseError
from reaper.lexer import tokenize
from reaper.parser import parse

def main() -> int:
    rng = random.Random(0x5AFE2026)
    alphabet = string.ascii_letters + string.digits + "_{}()[],:=+-*/%<>!#\" \n\t" + "абвгдежз"
    corpus = [
        "",
        "make value := 1\nemit value",
        'emit "unterminated',
        "when true { emit 1 }",
        "make x := " + "(" * 24 + "1" + ")" * 24,
        "craft f(a,b) { yield a + b }\nemit f(1,2)",
        "import " + '"' + ("x" * 512) + '"' ,
        "@" * 128,
    ]
    for _ in range(512):
        size = rng.randrange(0, 2049)
        corpus.append("".join(rng.choice(alphabet) for _ in range(size)))

    parsed = 0
    rejected = 0
    for source in corpus:
        try:
            tokens = tokenize(source, "<fuzz-smoke>")
            if len(tokens) > 4096:
                raise AssertionError("lexer exceeded the 4096-token fuzz bound")
            parse(source, "<fuzz-smoke>")
            parsed += 1
        except (LexError, ParseError):
            rejected += 1
    if parsed + rejected != len(corpus):
        raise AssertionError("fuzz corpus accounting mismatch")
    print(f"Reaper parser fuzz-smoke: PASS ({len(corpus)} inputs; {parsed} parsed; {rejected} rejected safely)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
