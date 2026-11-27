from __future__ import annotations

import json
import unittest
from pathlib import Path

from reaper import Interpreter
from reaper.lexer import KEYWORD_ALIASES, tokenize


ROOT = Path(__file__).resolve().parents[1]


class MostLithosFlowTests(unittest.TestCase):
    def test_lithos_vocabulary_is_russian_first_and_not_implicit_runtime(self) -> None:
        path = ROOT / "language" / "most_lithos_vocabulary.v1.json"
        catalog = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(catalog["schema"], "most-lithos-vocabulary.v1")
        self.assertEqual(catalog["profile"], "LITHOS::FLOW")
        self.assertEqual(catalog["entry_count"], len(catalog["entries"]))
        self.assertEqual(catalog["entry_count"], 44)
        self.assertEqual(len({entry["id"] for entry in catalog["entries"]}), 44)
        self.assertEqual(len({entry["ru"] for entry in catalog["entries"]}), 44)
        self.assertTrue(all(entry["runtime_status"] == "domain_name_only" for entry in catalog["entries"]))
        self.assertTrue(all(entry["use"] == "identifier_or_user_defined_routine" for entry in catalog["entries"]))
        self.assertTrue(all(entry["ru"] and entry["meaning_ru"] for entry in catalog["entries"]))

    def test_new_russian_spellings_map_to_existing_reaper_tokens(self) -> None:
        manifest = json.loads(
            (ROOT / "language" / "most_keyword_aliases.json").read_text(encoding="utf-8")
        )
        new_entries = manifest["aliases"][-48:]
        self.assertEqual(len(new_entries), 48)
        self.assertEqual(sum(item["support"] == "runtime" for item in new_entries), 17)
        self.assertEqual(sum(item["support"] == "lexical_reserved" for item in new_entries), 31)
        for item in new_entries:
            self.assertEqual(KEYWORD_ALIASES[item["source"]], item["canonical"])
        all_new_words = [item["source"] for item in new_entries]
        tokens = tokenize(" ".join(all_new_words))
        self.assertEqual([token.kind for token in tokens[:-1]], [
            item["canonical"].upper() for item in new_entries
        ])

    def test_russian_lithos_example_executes(self) -> None:
        source = (ROOT / "examples" / "lithos_flow_ru.most").read_text(encoding="utf-8")
        output: list[str] = []
        Interpreter(output=output.append).run(source)
        self.assertEqual(output, ["MOST_LITHOS_RU_OK"])

    def test_unlisted_inflections_remain_identifiers(self) -> None:
        tokens = tokenize("швы блоки шлюзами")
        self.assertEqual([token.kind for token in tokens[:-1]], ["IDENT", "IDENT", "IDENT"])


if __name__ == "__main__":
    unittest.main()
