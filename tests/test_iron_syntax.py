import json
import unittest

from reaper.iron_syntax import (
    IRON_SYNTAX_OWNER,
    IRON_SYNTAX_SCHEMA,
    IRON_SYNTAX_VERSION,
    IronSyntaxError,
    decode_iron_ast,
)

CATALOG = [
    ("begin_iron", "begin iron )", "iron", ")", "boundary"),
    ("core", "() core --", "core", "--", "section"),
    ("system", "[ system ]-", "system", "]-", "section"),
    ("stop_option", "stop option ;", "option", ";", "control"),
    ("level", "] level .", "level", ".", "control"),
    ("selective", "{ selective /", "selective", "/", "control"),
    ("operation", "} operation P)-", "operation", "P)-", "control"),
    ("massive", "?? massive <>", "massive", "<>", "modifier"),
    ("start", "< start >?", "start", ">?", "boundary"),
    ("new_work", "grown new-work >/", "new-work", ">/", "modifier"),
    ("concrete", "> concrete //*", "concrete", "//*", "modifier"),
    ("utility", "## utility _", "utility", "_", "directive"),
    ("unify", "# unify TAB", "unify", "TAB", "directive"),
    ("setup_brachpass", "setup brachpass ^^", "brachpass", "^^", "directive"),
    ("hyper_tournament", "!+ hyper tournament ^", "hyper tournament", "^", "modifier"),
    ("based_rules", "CC based rules ^^^", "based rules", "^^^", "directive"),
    ("level_jump_to_run", "level jump to run *(", "jump to run", "*(", "control"),
    ("true_connective", "TRUE connective *+", "connective", "*+", "operator"),
    ("verison", "verison ///. *", "///.", "*", "metadata"),
    ("verificated", "verificated /// !!", "///", "!!", "metadata"),
]


def valid_document():
    return {
        "schema": IRON_SYNTAX_SCHEMA,
        "version": IRON_SYNTAX_VERSION,
        "canonical_owner": IRON_SYNTAX_OWNER,
        "execution_performed": False,
        "records": [
            {
                "kind": kind,
                "phrase": phrase,
                "concept": concept,
                "marker": marker,
                "family": family,
                "record_id": record_id,
                "source_offset": record_id * 100,
                "source_length": len(phrase),
                "line": record_id + 1,
                "column": 1,
            }
            for record_id, (kind, phrase, concept, marker, family) in enumerate(CATALOG)
        ],
    }


class IronSyntaxBridgeTests(unittest.TestCase):
    def test_all_twenty_canonical_records_decode(self):
        ast = decode_iron_ast(valid_document())
        self.assertEqual(len(ast.records), 20)
        self.assertEqual(ast.records[13].phrase, "setup brachpass ^^")
        self.assertEqual(ast.records[18].phrase, "verison ///. *")
        self.assertFalse(ast.execution_performed)

    def test_json_payload_is_supported(self):
        ast = decode_iron_ast(json.dumps(valid_document()))
        self.assertEqual(ast.schema, IRON_SYNTAX_SCHEMA)

    def test_runtime_execution_flag_is_rejected(self):
        payload = valid_document()
        payload["execution_performed"] = True
        with self.assertRaisesRegex(IronSyntaxError, "syntax-only"):
            decode_iron_ast(payload)

    def test_unknown_or_modified_vocabulary_is_rejected(self):
        payload = valid_document()
        payload["records"][13]["phrase"] = "setup branchpass ^^"
        with self.assertRaisesRegex(IronSyntaxError, "canonical"):
            decode_iron_ast(payload)

    def test_record_id_and_source_order_are_checked(self):
        payload = valid_document()
        payload["records"][0]["record_id"] = 20
        with self.assertRaisesRegex(IronSyntaxError, "catalogue"):
            decode_iron_ast(payload)
        payload = valid_document()
        payload["records"][1]["source_offset"] = 0
        with self.assertRaisesRegex(IronSyntaxError, "source order"):
            decode_iron_ast(payload)

    def test_unknown_fields_and_boolean_offsets_are_rejected(self):
        payload = valid_document()
        payload["records"][0]["permission"] = "device_write"
        with self.assertRaisesRegex(IronSyntaxError, "keys mismatch"):
            decode_iron_ast(payload)
        payload = valid_document()
        payload["records"][0]["source_offset"] = True
        with self.assertRaisesRegex(IronSyntaxError, "integer"):
            decode_iron_ast(payload)

    def test_unsupported_versions_empty_records_and_invalid_json_fail(self):
        payload = valid_document()
        payload["version"] = "2.0.0"
        with self.assertRaisesRegex(IronSyntaxError, "version"):
            decode_iron_ast(payload)
        payload = valid_document()
        payload["records"] = []
        with self.assertRaisesRegex(IronSyntaxError, "non-empty"):
            decode_iron_ast(payload)
        with self.assertRaisesRegex(IronSyntaxError, "JSON"):
            decode_iron_ast("{not json")


if __name__ == "__main__":
    unittest.main()
