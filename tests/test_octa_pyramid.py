from __future__ import annotations
import json,tempfile,unittest
from pathlib import Path
from tools.validate_octa_pyramid import TOPOLOGY_PATH,validate
class OctaPyramidTests(unittest.TestCase):
 def test_complete_pairwise_mesh(self):
  r=validate();self.assertTrue(r["valid"]);self.assertEqual((r["facets"],r["directed_peer_links"],r["self_loops"]),(8,12,4))
 def bad(self,fn):
  x=json.loads(TOPOLOGY_PATH.read_text(encoding="utf-8"));fn(x)
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"o.json";p.write_text(json.dumps(x),encoding="utf-8")
   with self.assertRaises(ValueError):validate(topology_path=p)
 def test_missing_directed_link(self):self.bad(lambda x:x["peer_links"].pop())
 def test_duplicate_facet(self):self.bad(lambda x:x["facets"][0].update(id=x["facets"][1]["id"]))
 def test_executable_apex(self):self.bad(lambda x:x["apex"].update(executable=True))
 def test_missing_self_loop(self):self.bad(lambda x:x["self_loops"].pop())
 def test_wrong_transport(self):self.bad(lambda x:x["peer_links"][0].update(transport="none"))
 def test_pack_consumer_status_cannot_be_downgraded(self):self.bad(lambda x:x["peer_links"][6].update(status="planned"))
 def test_missing_fourth_self_loop(self):self.bad(lambda x:x["self_loops"].pop())
 def test_ventusample_pack_consumer_is_implemented(self):
  r=validate();self.assertTrue(r["valid"])
  x=json.loads(TOPOLOGY_PATH.read_text(encoding="utf-8"))
  edge=next(link for link in x["peer_links"] if link["id"]=="ventusample-to-reaper")
  self.assertEqual(edge["status"],"implemented")
  self.assertTrue(x["semantics"]["reaper_pack_consumer_implemented"])
if __name__=="__main__":unittest.main()
