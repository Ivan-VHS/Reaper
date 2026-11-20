from __future__ import annotations
import json,tempfile,unittest
from pathlib import Path
from tools.validate_octa_pyramid import TOPOLOGY_PATH,validate
class OctaPyramidTests(unittest.TestCase):
 def test_complete_pairwise_mesh(self):
  r=validate();self.assertTrue(r["valid"]);self.assertEqual((r["facets"],r["directed_peer_links"],r["self_loops"]),(8,6,3))
 def bad(self,fn):
  x=json.loads(TOPOLOGY_PATH.read_text(encoding="utf-8"));fn(x)
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"o.json";p.write_text(json.dumps(x),encoding="utf-8")
   with self.assertRaises(ValueError):validate(topology_path=p)
 def test_missing_directed_link(self):self.bad(lambda x:x["peer_links"].pop())
 def test_duplicate_facet(self):self.bad(lambda x:x["facets"][0].update(id=x["facets"][1]["id"]))
 def test_executable_apex(self):self.bad(lambda x:x["apex"].update(executable=True))
 def test_missing_self_loop(self):self.bad(lambda x:x["self_loops"].pop())
 def test_wrong_transport(self):self.bad(lambda x:x["peer_links"][0].update(transport="native-ffi"))
if __name__=="__main__":unittest.main()
