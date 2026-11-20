"""Validate OCTA-8 peer topology using only the Python standard library."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
from typing import Any
ROOT=Path(__file__).resolve().parents[1]
TOPOLOGY_PATH=ROOT/"federation"/"octa-pyramid.v1.json";SCHEMA_PATH=ROOT/"schemas"/"octa-pyramid.v1.schema.json";PROJECT_PATH=ROOT/"project-contract.json"
PROJECTS={"reaper","pytyliki","oplague"}
FACETS={"facet.identity","facet.contracts","facet.transport","facet.provenance","facet.validation","facet.privacy","facet.safety","facet.audit"}
EDGES={
("reaper","oplague","json-file","reaper.oplage-comparison.v1","artifact"),
("oplague","reaper","json-file","oplage.device-snapshot.v1","artifact"),
("reaper","pytyliki","native-ffi","pytyliki.c-abi.v1","request"),
("pytyliki","reaper","native-ffi","pytyliki.c-abi.v1","response"),
("oplague","pytyliki","native-ffi","pytyliki.c-abi.v1","request"),
("pytyliki","oplague","native-ffi","pytyliki.c-abi.v1","response")}
def _unique(pairs:list[tuple[str,Any]])->dict[str,Any]:
 d={}
 for k,v in pairs:
  if k in d:raise ValueError(f"duplicate JSON key: {k}")
  d[k]=v
 return d
def _load(p:Path)->Any:
 try:return json.loads(p.read_text(encoding="utf-8"),object_pairs_hook=_unique,parse_constant=lambda t:(_ for _ in ()).throw(ValueError(f"non-finite JSON: {t}")))
 except OSError as e:raise ValueError(f"cannot read {p}: {e}") from e
def _need(ok:bool,msg:str)->None:
 if not ok:raise ValueError(msg)
def validate(topology_path:Path=TOPOLOGY_PATH,schema_path:Path=SCHEMA_PATH,project_path:Path=PROJECT_PATH)->dict[str,Any]:
 s=_load(schema_path);_need(isinstance(s,dict) and s.get("$schema")=="https://json-schema.org/draft/2020-12/schema" and s.get("title")=="OCTA-8 Federation Pyramid v1","invalid OCTA JSON Schema declaration")
 x=_load(topology_path);_need(isinstance(x,dict) and x.get("schema")=="octa.federation-pyramid.v1" and x.get("topology_id")=="octa-8","invalid OCTA topology ID")
 sh=x.get("shape");_need(isinstance(sh,dict) and sh.get("kind")=="octagonal-pyramid" and sh.get("base_sides")==8 and sh.get("triangular_facets")==8 and sh.get("apex_vertex")=="octa-hub","invalid octagonal pyramid geometry")
 apex=x.get("apex");_need(isinstance(apex,dict) and apex.get("id")=="octa-hub" and apex.get("executable") is False and apex.get("single_point_of_failure") is False,"apex must be non-executable coordination metadata")
 fs=x.get("facets");_need(isinstance(fs,list) and len(fs)==8,"exactly eight facets are required")
 ids=[v.get("id") for v in fs if isinstance(v,dict)];_need(len(ids)==8 and len(set(ids))==8 and set(ids)==FACETS,"eight unique canonical facet IDs required")
 _need(apex.get("linked_facets")==ids and sorted(v.get("side") for v in fs)==list(range(1,9)),"apex/facet geometry is inconsistent")
 base=x.get("base_mesh");_need(isinstance(base,dict) and base.get("mode")=="horizontal-complete-directed-peer-mesh" and set(base.get("project_ids",[]))==PROJECTS and base.get("directed_peer_links")==6 and base.get("self_loops")==3,"incomplete horizontal peer base")
 links=x.get("peer_links");_need(isinstance(links,list) and len(links)==6,"exactly six directed links required")
 actual=set();link_ids=[]
 for i,v in enumerate(links):
  _need(isinstance(v,dict),f"link {i} must be an object");link_ids.append(v.get("id"))
  _need(v.get("from") in PROJECTS and v.get("to") in PROJECTS and v.get("from")!=v.get("to") and v.get("status")=="implemented",f"link {i} invalid")
  actual.add((v.get("from"),v.get("to"),v.get("transport"),v.get("interface"),v.get("flow")))
 _need(len(set(link_ids))==6 and actual==EDGES,"all six directed pair contracts must be present exactly")
 loops=x.get("self_loops");_need(isinstance(loops,list) and len(loops)==3 and {v.get("project") for v in loops if isinstance(v,dict)}==PROJECTS,"each project must have one self-loop")
 sem=x.get("semantics");_need(isinstance(sem,dict) and sem.get("complete_pairwise_product") is True and sem.get("directed_link_count_formula")=="n*(n-1)" and sem.get("hub_is_not_a_runtime_gateway") is True and sem.get("request_response_edges_are_synchronous") is True and sem.get("no_implicit_native_loading") is True and sem.get("no_driver_mutation_through_mesh") is True,"OCTA topology semantics invalid")
 manifest=_load(project_path);_need(isinstance(manifest,dict) and isinstance(manifest.get("project"),dict),"project manifest malformed")
 project=manifest["project"].get("id");_need(project in PROJECTS and project in base["project_ids"],"local project missing from mesh")
 return {"valid":True,"topology":"octa-8","project":project,"base_sides":8,"facets":8,"directed_peer_links":6,"self_loops":3,"complete_pairwise_product":True}
def main()->int:
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("--json",action="store_true");a=p.parse_args()
 try:r=validate()
 except (ValueError,TypeError,KeyError) as e:print(f"OCTA-8 INVALID: {e}",file=sys.stderr);return 1
 if a.json:print(json.dumps(r,ensure_ascii=False,sort_keys=True,indent=2))
 else:print(f"OCTA-8 valid | {r['project']} | 8 facets | 6 peer links | 3 self-loops")
 return 0
if __name__=="__main__":raise SystemExit(main())
