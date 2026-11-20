import unittest

from reaper.qcs import AstNode, QcsError, lex, parse, validate


SOURCE = """[@ domain:irq(vector: 32), budget:120ns, state:! @]
func timerTick(counter: UInt64?) {
    guard let current = counter else { return }
    let next = current &+ 1
    next send IRQQueue.enqueue()
}
[@ end @]
"""


class QcsFrontendTests(unittest.TestCase):
    def test_lexer_emits_frame_and_flow_tokens(self) -> None:
        tokens = lex(SOURCE)
        values = [token.value for token in tokens]
        self.assertIn("[@", values)
        self.assertIn("@]", values)
        self.assertIn("send", values)
        self.assertTrue(any(token.kind == "DURATION" and token.value == "120ns" for token in tokens))

    def test_parser_builds_frame_function_and_flow_ast(self) -> None:
        module = parse(SOURCE)
        self.assertEqual(module.kind, "Module")
        frame = module.fields["declarations"][0]
        self.assertEqual(frame.kind, "Frame")
        self.assertEqual(frame.fields["domain"].fields["callee"].fields["name"], "irq")
        function = frame.fields["body"][0]
        self.assertEqual(function.kind, "Function")
        statements = function.fields["body"].fields["statements"]
        flow = statements[-1].fields["expression"]
        self.assertIsInstance(flow, AstNode)
        self.assertEqual(flow.kind, "Flow")
        self.assertEqual(flow.fields["operator"], "send")

    def test_registered_domain_validates(self) -> None:
        self.assertEqual(validate(parse(SOURCE)), [])

    def test_unknown_domain_is_reported(self) -> None:
        source = """[@ domain:madeUp, state:? @]
func f() {}
[@ end @]"""
        self.assertTrue(any("unknown QCS domain" in item for item in validate(parse(source))))

    def test_forbidden_angle_bar_and_tilde_characters(self) -> None:
        for char in ("<", ">", "|", "~"):
            with self.subTest(char=char), self.assertRaises(QcsError):
                lex(f"let x = a {char} b")

    def test_unterminated_frame_fails(self) -> None:
        with self.assertRaisesRegex(QcsError, "unterminated frame"):
            parse("""[@ domain:mmio @]
func f() {}""")

    def test_missing_domain_fails(self) -> None:
        with self.assertRaisesRegex(QcsError, "requires domain"):
            parse("""[@ state:! @]
[@ end @]""")

    def test_duplicate_attribute_fails(self) -> None:
        with self.assertRaisesRegex(QcsError, "duplicate frame attribute"):
            parse("""[@ domain:mmio, domain:dma @]
[@ end @]""")

    def test_optional_generic_type(self) -> None:
        module = parse("func read() returns RingBuf(Int16)? { return nil }")
        fn = module.fields["declarations"][0]
        self.assertTrue(fn.fields["return_type"].fields["optional"])
        self.assertEqual(fn.fields["return_type"].fields["name"], "RingBuf")


if __name__ == "__main__":
    unittest.main()
