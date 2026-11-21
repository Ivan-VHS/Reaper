"""Manifest-backed Kora plugin registry."""
import json
from dataclasses import dataclass
from importlib.resources import files
from . import runtime
@dataclass(frozen=True)
class Plugin:
 id:str
 name:str
 domain:str
 functions:tuple[str,...]
class KoraPluginManager:
 def __init__(self):
  data=json.loads(files(__package__).joinpath("manifest.json").read_text(encoding="utf-8"))
  if data.get("schema")!="reaper.kora.plugin-manifest.v1":raise ValueError("unsupported Kora manifest")
  self.plugins={p["id"]:Plugin(p["id"],p["name"],p["domain"],tuple(p["functions"])) for p in data["plugins"]}
  self.enabled=set(self.plugins)
 def list_plugins(self):
  return [{"id":p.id,"name":p.name,"domain":p.domain,"function_count":len(p.functions),"enabled":p.id in self.enabled} for p in self.plugins.values()]
 def set_enabled(self,plugin_id,enabled):
  if plugin_id not in self.plugins:raise KeyError(plugin_id)
  (self.enabled.add if enabled else self.enabled.discard)(plugin_id)
  return bool(enabled)
 def call(self,qualified_name,*args,**kwargs):
  owner=next((p for p in self.plugins.values() if qualified_name in p.functions),None)
  if owner is None:raise ValueError("unknown Kora function: "+str(qualified_name))
  if owner.id not in self.enabled:raise RuntimeError("Kora plugin disabled: "+owner.name)
  module,function=qualified_name.split(".",1)
  return runtime.call(module,function,*args,**kwargs)
