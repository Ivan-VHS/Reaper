from __future__ import annotations
import unittest
from reaper.systems_languages import load_matrix, select_languages, validate_matrix

class SystemsLanguageMatrixTests(unittest.TestCase):
    def test_catalogue_has_66_ordered_positions(self):
        data=load_matrix()
        self.assertEqual(validate_matrix(data),66)
        self.assertEqual([x["index"] for x in data["languages"]],list(range(1,67)))
    def test_duplicate_source_entries_are_explicit_aliases(self):
        data=load_matrix()
        aliases={x["name"]:x["alias_of"] for x in data["languages"] if x.get("alias_of")}
        self.assertEqual(aliases["Clay (generic programming model)"],"lang-22")
        self.assertEqual(aliases["Nimrod (early Nim)"],"lang-18")
    def test_reaper_profile_ranks_memory_and_verification_features(self):
        results=select_languages(load_matrix(),profile="reaper")
        self.assertTrue(results)
        self.assertGreaterEqual(results[0]["profile_score"],results[-1]["profile_score"])
        names={x["name"] for x in results}
        self.assertIn("Austral",names); self.assertIn("ATS",names)
    def test_toolchain_probe_is_injectable_and_path_only(self):
        which=lambda command:f"/mock/bin/{command}" if command in {"odin","nim"} else None
        results=select_languages(load_matrix(),profile="pytyliki",available_only=True,which=which)
        self.assertTrue(results)
        self.assertTrue(all(x["toolchain_state"]=="available" for x in results))
        self.assertIn("Odin",{x["name"] for x in results})
    def test_bad_count_and_unknown_alias_are_rejected(self):
        data=load_matrix(); broken=dict(data); broken["languages"]=data["languages"][:-1]
        with self.assertRaisesRegex(ValueError,"exactly 66"): validate_matrix(broken)
        broken=dict(data); broken["languages"]=[dict(x) for x in data["languages"]]
        broken["languages"][-1]["alias_of"]="missing"
        with self.assertRaisesRegex(ValueError,"unknown id"): validate_matrix(broken)

if __name__=="__main__": unittest.main()
