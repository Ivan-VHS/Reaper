#!/usr/bin/env python3
"""Validate the four-project OCTA-8 peer topology using only the Python standard library."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
TOPOLOGY_PATH=ROOT/"federation"/"octa-pyramid.v1.json"
SCHEMA_PATH=ROOT/"schemas"/"octa-pyramid.v1.schema.json"
PROJECT_PATH=ROOT/"project-contract.json"
PROJECTS={"reaper","pytyliki","oplague","ventusample"}
FACETS={"facet.identity","facet.contracts","facet.transport","facet.provenance","facet.validation","facet.privacy","facet.safety","facet.audit"}
STATUSES={"implemented","partial","planned","not_applicable"}
EDGES={
("reaper","oplague","json-file","reaper.oplage-comparison.v1","artifact","implemented"),
("oplague","reaper","json-file","oplage.device-snapshot.v1","artifact","implemented"),
("reaper","pytyliki","native-ffi","pytyliki.c-abi.v1","request","implemented"),
("pytyliki","reaper","native-ffi","pytyliki.c-abi.v1","response","implemented"),
("oplague","pytyliki","native-ffi","pytyliki.c-abi.v1","request","implemented"),
("pytyliki","oplague","native-ffi","pytyliki.c-abi.v1","response","implemented"),
("ventusample","reaper","json-file","ventusample.pack.v1","artifact","partial"),
("reaper","ventusample","json-file","ventusample.render-request.v1","artifact","planned"),
("ventusample","pytyliki","native-ffi","pytyliki.c-abi.v1","request","planned"),
("pytyliki","ventusample","native-ffi","pytyliki.c-abi.v1","response","planned"),
("ventusample","oplague","none","not-applicable.v1","none","not_applicable"),
("oplague","ventusample","none","not-applicable.v1","none","not_applicable"),
}

def _unique(pairs:list[tuple[str,Any]])->dict[str,Any]:
 result={}
 for key,value in pairs:
  if key in result: raise ValueError(f"duplicate JSON key: {key}")
  result[key]=value
 return result

def _load(path:Path)->Any:
 try:
  return json.loads(path.read_text(encoding="utf-8"),object_pairs_hook=_unique,
   parse_constant=lambda token:(_ for _ in ()).throw(ValueError(f"non-finite JSON: {token}")))
 except OSError as error: raise ValueError(f"cannot read {path}: {error}") from error

def _need(condition:bool,message:str)->None:
 if not condition: raise ValueError(message)

def validate(topology_path:Path=TOPOLOGY_PATH,schema_path:Path=SCHEMA_PATH,project_path:Path=PROJECT_PATH)->dict[str,Any]:
 schema=_load(schema_path)
 _need(isinstance(schema,dict) and schema.get("$schema")=="https://json-schema.org/draft/2020-12/schema","invalid JSON Schema draft")
 _need(schema.get("title")=="OCTA-8 Four-Project Federation Pyramid v1","unexpected OCTA schema title")
 topology=_load(topology_path)
 _need(isinstance(topology,dict) and topology.get("schema")=="octa.federation-pyramid.v1" and topology.get("topology_id")=="octa-8","invalid topology ID")
 shape=topology.get("shape")
 _need(isinstance(shape,dict) and shape.get("kind")=="octagonal-pyramid" and shape.get("base_sides")==8 and shape.get("triangular_facets")==8 and shape.get("apex_vertex")=="octa-hub","invalid octagonal pyramid geometry")
 apex=topology.get("apex")
 _need(isinstance(apex,dict) and apex.get("id")=="octa-hub" and apex.get("executable") is False and apex.get("single_point_of_failure") is False,"apex must remain non-executable coordination metadata")
 facets=topology.get("facets")
 _need(isinstance(facets,list) and len(facets)==8,"exactly eight facets are required")
 facet_ids=[item.get("id") for item in facets if isinstance(item,dict)]
 _need(len(facet_ids)==8 and len(set(facet_ids))==8 and set(facet_ids)==FACETS,"eight unique canonical facet IDs are required")
 _need(apex.get("linked_facets")==facet_ids and sorted(item.get("side") for item in facets)==list(range(1,9)),"apex/facet geometry is inconsistent")
 base=topology.get("base_mesh")
 _need(isinstance(base,dict) and base.get("mode")=="horizontal-complete-directed-peer-mesh","invalid peer mesh mode")
 _need(base.get("project_ids")==["reaper","pytyliki","oplague","ventusample"],"four-project peer list is not canonical")
 _need(base.get("directed_peer_links")==12 and base.get("self_loops")==4,"four-project mesh counts must be 12 links and four self-loops")
 links=topology.get("peer_links")
 _need(isinstance(links,list) and len(links)==12,"exactly twelve directed peer links are required")
 actual=set();link_ids=[]
 for index,item in enumerate(links):
  _need(isinstance(item,dict),f"peer link {index} must be an object")
  link_ids.append(item.get("id"))
  _need(item.get("from") in PROJECTS and item.get("to") in PROJECTS and item.get("from")!=item.get("to"),f"peer link {index} has invalid endpoints")
  _need(item.get("status") in STATUSES,f"peer link {index} has invalid status")
  actual.add((item.get("from"),item.get("to"),item.get("transport"),item.get("interface"),item.get("flow"),item.get("status")))
 _need(len(set(link_ids))==12 and actual==EDGES,"the 12 directed peer contracts or their statuses differ from the verified map")
 loops=topology.get("self_loops")
 _need(isinstance(loops,list) and len(loops)==4 and {item.get("project") for item in loops if isinstance(item,dict)}==PROJECTS,"each project must have one independent self-loop")
 semantics=topology.get("semantics")
 _need(isinstance(semantics,dict) and semantics.get("complete_pairwise_product") is True and semantics.get("directed_link_count_formula")=="n*(n-1)" and semantics.get("hub_is_not_a_runtime_gateway") is True and semantics.get("request_response_edges_are_synchronous") is True and semantics.get("no_implicit_native_loading") is True and semantics.get("no_driver_mutation_through_mesh") is True and semantics.get("producer_export_does_not_imply_consumer_integration") is True,"OCTA-8 semantics are invalid")
 manifest=_load(project_path)
 _need(isinstance(manifest,dict) and isinstance(manifest.get("project"),dict),"project manifest is malformed")
 project=manifest["project"].get("id")
 _need(project in PROJECTS and project in base["project_ids"],"local project is missing from the four-peer mesh")
 return {"valid":True,"topology":"octa-8","project":project,"base_sides":8,"facets":8,"directed_peer_links":12,"self_loops":4,"complete_pairwise_product":True}

def main()->int:
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--json",action="store_true");args=parser.parse_args()
 try: result=validate()
 except (ValueError,TypeError,KeyError) as error:
  print(f"OCTA-8 INVALID: {error}",file=sys.stderr);return 1
 if args.json: print(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2))
 else: print(f"OCTA-8 valid | {result['project']} | 8 facets | 12 directed links | 4 self-loops")
 return 0

if __name__=="__main__": raise SystemExit(main())
