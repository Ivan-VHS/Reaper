import unittest

from reaper.semantic_graph import SemanticEdge, SemanticGraph, SemanticNode


class SemanticGraphTests(unittest.TestCase):
    def test_alias_is_not_semantic_identity(self):
        first = SemanticNode.create("literal", (), "i64", literal=42, label="answer")
        renamed = first.rename("ответ")
        self.assertEqual(first.content_id, renamed.content_id)
        self.assertTrue(renamed.verify_address())

    def test_typed_graph_and_deterministic_projection(self):
        source = SemanticNode.create("literal", (), "i64", literal=21)
        doubled = SemanticNode.create("multiply", ("i64",), "i64", literal=2)
        graph = SemanticGraph().add_node(source).add_node(doubled)
        graph = graph.connect(source.content_id, doubled.content_id, 0)
        graph.validate(require_complete=True)
        self.assertEqual(graph.to_dict(), graph.to_dict())
        self.assertEqual(len(graph.to_dict()["edges"]), 1)

    def test_type_mismatch_is_rejected(self):
        source = SemanticNode.create("literal", (), "text", literal="42")
        target = SemanticNode.create("increment", ("i64",), "i64")
        graph = SemanticGraph().add_node(source).add_node(target)
        with self.assertRaisesRegex(TypeError, "port type mismatch"):
            graph.connect(source.content_id, target.content_id, 0)

    def test_unconnected_input_is_rejected_when_requested(self):
        node = SemanticNode.create("increment", ("i64",), "i64")
        with self.assertRaisesRegex(ValueError, "unconnected input"):
            SemanticGraph().add_node(node).validate(require_complete=True)

    def test_duplicate_input_is_rejected(self):
        left = SemanticNode.create("literal", (), "i64", literal=1)
        right = SemanticNode.create("literal", (), "i64", literal=2)
        target = SemanticNode.create("add", ("i64", "i64"), "i64")
        graph = SemanticGraph().add_node(left).add_node(right).add_node(target)
        graph = graph.connect(left.content_id, target.content_id, 0)
        with self.assertRaisesRegex(ValueError, "already connected"):
            graph.connect(right.content_id, target.content_id, 0)

    def test_cycles_are_rejected(self):
        left = SemanticNode.create("left", ("i64",), "i64")
        right = SemanticNode.create("right", ("i64",), "i64")
        graph = SemanticGraph((left, right), (
            SemanticEdge(left.content_id, right.content_id, 0),
            SemanticEdge(right.content_id, left.content_id, 0),
        ))
        with self.assertRaisesRegex(ValueError, "cycle"):
            graph.validate()


    def test_string_signatures_are_not_split_into_characters(self):
        with self.assertRaisesRegex(TypeError, "input_types"):
            SemanticNode.create("consume", "i64", "unit")
        with self.assertRaisesRegex(TypeError, "effects"):
            SemanticNode.create("write", (), "unit", effects="io")

    def test_directly_constructed_graph_rejects_boolean_port_indices(self):
        source = SemanticNode.create("literal", (), "i64", literal=1)
        target = SemanticNode.create("increment", ("i64",), "i64")
        graph = SemanticGraph(
            (source, target),
            (SemanticEdge(source.content_id, target.content_id, True),),
        )
        with self.assertRaisesRegex(ValueError, "non-negative integer port"):
            graph.validate()

    def test_directly_constructed_graph_rejects_mutable_node_signatures(self):
        node = SemanticNode.create("literal", (), "i64", literal=1)
        malformed = SemanticNode(
            node.content_id, node.operation, ["i64"], node.output_type,
            node.effects, node.literal, node.label
        )
        with self.assertRaisesRegex(ValueError, "immutable signature"):
            SemanticGraph((malformed,), ()).validate()

    def test_non_finite_literal_is_rejected(self):
        with self.assertRaisesRegex(TypeError, "finite"):
            SemanticNode.create("literal", (), "f64", literal=float("nan"))


if __name__ == "__main__":
    unittest.main()
