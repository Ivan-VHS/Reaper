from __future__ import annotations

import unittest

from reaper.glyphs import ALPHABET, GLYPHS, GLYPH_BY_INDEX, match_glyph
from reaper.lexer import tokenize
from reaper import Interpreter, LexError, ReaperRuntimeError
from reaper.memory import MemoryArena, MemoryBuffer, MemoryView


class GlyphRegistryTests(unittest.TestCase):
    def test_registry_has_666_unique_digit_free_tokens(self) -> None:
        tokens = [item.token for item in GLYPHS]
        self.assertEqual(len(tokens), 666)
        self.assertEqual(len(set(tokens)), 666)
        self.assertEqual(set(GLYPH_BY_INDEX), set(range(1, 667)))
        for token in tokens:
            self.assertTrue(token)
            self.assertTrue(set(token) <= set(ALPHABET))
            self.assertFalse(any(char.isdigit() for char in token))

    def test_first_block_preserves_the_requested_tokens(self) -> None:
        self.assertEqual(
            [GLYPH_BY_INDEX[index].token for index in range(1, 11)],
            [";;:", "::;", ";::", ";+:", ":+;", ":+:", "[::]", "{;;}", "};;", "_::"],
        )
        self.assertTrue(all(GLYPH_BY_INDEX[index].implemented for index in range(1, 121)))
        self.assertTrue(all(not GLYPH_BY_INDEX[index].implemented for index in range(121, 667)))

    def test_longest_match_wins_over_a_shorter_prefix(self) -> None:
        self.assertEqual(match_glyph(";;:_-tail"), ";;:_-")
        self.assertEqual(match_glyph(";;: "), ";;:")

    def test_lexer_emits_one_glyph_token_with_no_numeric_id(self) -> None:
        tokens = tokenize("emit ;;:_- (buffer)")
        glyphs = [token for token in tokens if token.kind == "GLYPH"]
        self.assertEqual([token.value for token in glyphs], [";;:_-"])
        self.assertFalse(any(char.isdigit() for char in glyphs[0].value))

    def test_unregistered_glyph_sequence_is_rejected(self) -> None:
        with self.assertRaises(LexError):
            tokenize("emit ::::???")

    def capture(self, source: str) -> list[str]:
        output: list[str] = []
        Interpreter(output=output.append).run(source)
        return output

    def test_allocate_write_and_zero_copy_view(self) -> None:
        source = """\
make buffer := ;::(16)
memory_write(buffer, 0, "hello")
make view := ::;(buffer, 0, 5)
emit memory_read(view)
emit size(view)
"""
        self.assertEqual(self.capture(source), ["hello", "5"])

    def test_reserve_and_clear_keep_the_buffer_allocated(self) -> None:
        source = """\
make buffer := ;::(4)
;+:(buffer, 16)
memory_write(buffer, 0, "test")
:+;(buffer)
emit memory_capacity(buffer)
emit size(buffer)
"""
        self.assertEqual(self.capture(source), ["16", "0"])

    def test_transaction_rollback_restores_buffer_state(self) -> None:
        source = """\
make buffer := ;::(8)
memory_write(buffer, 0, "abc")
make frame := };;=;(buffer)
memory_write(buffer, 0, "xyz")
;;:[:(frame)
emit memory_read(buffer)
"""
        self.assertEqual(self.capture(source), ["abc"])

    def test_arena_enforces_limit_and_closes_allocations(self) -> None:
        source = """\
make arena := {;;}(8)
make buffer := ;::(arena, 6)
memory_write(buffer, 0, "abc")
make report := };;(arena)
emit report["released"]
emit report["allocations"]
"""
        self.assertEqual(self.capture(source), ["6", "1"])

    def test_parent_arena_caps_nested_arena_reservations(self) -> None:
        source = "make arena := {;;}(8)\\nmake child := {;;}(9, arena)"
        with self.assertRaisesRegex(ReaperRuntimeError, "parent arena memory limit"):
            self.capture(source)

    def test_memory_operations_reject_out_of_bounds_writes(self) -> None:
        with self.assertRaisesRegex(ReaperRuntimeError, "capacity"):
            self.capture("""\
make buffer := ;::(2)
memory_write(buffer, 0, "too long")
""")

    def test_reserved_extension_glyph_is_explicitly_not_implemented(self) -> None:
        glyph = GLYPH_BY_INDEX[121].token
        with self.assertRaisesRegex(ReaperRuntimeError, "reserved"):
            self.capture(f"emit {glyph}()")


if __name__ == "__main__":
    unittest.main()
