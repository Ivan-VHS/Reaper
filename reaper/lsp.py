"""Dependency-free Language Server Protocol support for REAPER/MOST."""
from __future__ import annotations
import json, re, sys
from urllib.parse import unquote, urlparse
from .errors import ReaperError
from .lexer import KEYWORDS, KEYWORD_ALIASES
from .parser import parse

BUILTINS = ("text","number","length","range","map","keep","fold","sum","min","max","sort","reverse","unique","join","split")
KEYWORD_DOCS = {
 "make":"Declare an immutable binding: make name := expression.",
 "vary":"Declare a mutable binding: vary name := expression.",
 "change":"Reassign a mutable binding: change name := expression.",
 "craft":"Declare a function: craft name(parameters) { ... }.",
 "yield":"Return a value from a function.","emit":"Write a value to program output.",
 "when":"Conditional statement; optionally followed by otherwise.",
 "each":"Iterate: each item in values { ... }.","loop":"Loop while a condition is true.",
 "~>":"REAPER left-to-right flow operator; passes the left value as the first argument."
}
WORDS=sorted(set(KEYWORDS)|set(KEYWORD_ALIASES)|set(BUILTINS)|{"~>","::","true","false","nothing"})
def pos(line,col): return {"line":max(0,line-1),"character":max(0,col-1)}
def uri_path(uri):
 p=urlparse(uri); return unquote(p.path) if p.scheme=="file" else uri
def diagnostics(source,filename):
 try: parse(source,filename); return []
 except (ReaperError,ValueError) as error:
  m=re.search(r":(\d+):(\d+):\s*(.*)$",str(error))
  line,col,msg=(int(m.group(1)),int(m.group(2)),m.group(3)) if m else (1,1,str(error))
  return [{"range":{"start":pos(line,col),"end":pos(line,col+1)},"severity":1,
   "source":"reaper","code":type(error).__name__,"message":msg}]

class LanguageService:
 def __init__(self): self.documents={}; self.shutdown_requested=False
 def handle(self,method,params=None):
  p=params or {}; notes=[]
  if method=="initialize":
   return ({"capabilities":{"textDocumentSync":{"openClose":True,"change":1},
    "completionProvider":{"triggerCharacters":[".","~",":"]},"hoverProvider":True,
    "definitionProvider":True,"referencesProvider":True,"renameProvider":True,
    "documentSymbolProvider":True},"serverInfo":{"name":"reaper-language-server","version":"0.1.0"}},notes)
  if method=="shutdown": self.shutdown_requested=True; return None,notes
  if method=="textDocument/didOpen":
   d=p.get("textDocument",{}); uri=d.get("uri","")
   self.documents[uri]={"text":d.get("text",""),"version":d.get("version",0)}
   notes.append(self.publish(uri)); return None,notes
  if method=="textDocument/didChange":
   d=p.get("textDocument",{}); uri=d.get("uri",""); changes=p.get("contentChanges",[])
   if uri in self.documents and changes:
    self.documents[uri]["text"]=changes[-1].get("text",self.documents[uri]["text"])
    self.documents[uri]["version"]=d.get("version",self.documents[uri]["version"])
    notes.append(self.publish(uri))
   return None,notes
  if method=="textDocument/didClose":
   uri=p.get("textDocument",{}).get("uri",""); self.documents.pop(uri,None)
   notes.append({"method":"textDocument/publishDiagnostics","params":{"uri":uri,"diagnostics":[]}})
   return None,notes
  if method=="textDocument/completion":
   prefix=self.word_at(p)
   return ([{"label":w,"kind":14,"detail":"REAPER/MOST keyword or built-in"} for w in WORDS if w.startswith(prefix)],notes)
  if method=="textDocument/hover":
   word=self.word_at(p); detail=KEYWORD_DOCS.get(word) or (f"REAPER built-in {word}." if word in BUILTINS else None)
   return ({"contents":{"kind":"markdown","value":detail}} if detail else None),notes
  if method=="textDocument/documentSymbol":
   uri=p.get("textDocument",{}).get("uri","")
   return self.symbols(self.documents.get(uri,{}).get("text","")),notes
  if method in ("textDocument/definition","textDocument/references","textDocument/rename"):
   uri=p.get("textDocument",{}).get("uri",""); src=self.documents.get(uri,{}).get("text","")
   word=self.word_at(p); locations=self.locations(uri,src,word)
   if method=="textDocument/definition":
    declaration=re.compile(r"^\\s*(?:make|vary|craft)\\s+"+re.escape(word)+r"\\b")
    declared=[item for item in locations if declaration.search(src.splitlines()[item["range"]["start"]["line"]])]
    return (declared[:1] or None),notes
   if method=="textDocument/rename":
    new=p.get("newName","")
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*",new): return None,notes
    edits=[{"range":x["range"],"newText":new} for x in locations]
    return ({"changes":{uri:edits}} if edits else None),notes
   return locations,notes
  return None,notes
 def publish(self,uri):
  d=self.documents[uri]
  return {"method":"textDocument/publishDiagnostics","params":{"uri":uri,"version":d["version"],"diagnostics":diagnostics(d["text"],uri_path(uri))}}
 def word_at(self,p):
  uri=p.get("textDocument",{}).get("uri",""); src=self.documents.get(uri,{}).get("text","")
  row=p.get("position",{}).get("line",0); col=p.get("position",{}).get("character",0); lines=src.splitlines()
  if row>=len(lines): return ""
  line=lines[row]
  for match in re.finditer(r"[\wА-Яа-яЁё]+|~>|::",line):
   if match.start()<=col<=match.end(): return match.group(0)
  previous=[m for m in re.finditer(r"[\wА-Яа-яЁё]+|~>|::",line) if m.end()<=col]
  return previous[-1].group(0) if previous else ""
 def locations(self,uri,src,word):
  if not word: return []
  out=[]
  for row,line in enumerate(src.splitlines()):
   for m in re.finditer(r"(?<![\w])"+re.escape(word)+r"(?![\w])",line):
    out.append({"uri":uri,"range":{"start":{"line":row,"character":m.start()},"end":{"line":row,"character":m.end()}}})
  return out
 def symbols(self,src):
  out=[]
  for row,line in enumerate(src.splitlines()):
   m=re.match(r"\s*(make|vary|craft)\s+([A-Za-z_][A-Za-z0-9_]*)",line)
   if m:
    name=m.group(2); start=m.start(2)
    out.append({"name":name,"kind":12 if m.group(1)=="craft" else 13,
     "range":{"start":{"line":row,"character":m.start()},"end":{"line":row,"character":len(line)}},
     "selectionRange":{"start":{"line":row,"character":start},"end":{"line":row,"character":start+len(name)}}})
  return out

def read_message(stream):
 headers={}
 while True:
  line=stream.readline()
  if not line: return None
  if line in (b"\r\n",b"\n"): break
  key,_,value=line.decode("ascii").partition(":"); headers[key.lower()]=value.strip()
 length=int(headers.get("content-length","0"))
 if length<0 or length>16*1024*1024: raise ValueError("invalid LSP Content-Length")
 body=stream.read(length)
 return json.loads(body.decode("utf-8")) if len(body)==length else None
def write_message(stream,payload):
 body=json.dumps(payload,ensure_ascii=False,separators=(",",":")).encode("utf-8")
 stream.write(f"Content-Length: {len(body)}\r\n\r\n".encode("ascii")+body); stream.flush()
def serve(stdin=None,stdout=None):
 stdin,stdout=stdin or sys.stdin.buffer,stdout or sys.stdout.buffer; service=LanguageService()
 while True:
  msg=read_message(stdin)
  if msg is None: return 0
  method=msg.get("method",""); result,notes=service.handle(method,msg.get("params"))
  for note in notes: write_message(stdout,{"jsonrpc":"2.0",**note})
  if "id" in msg: write_message(stdout,{"jsonrpc":"2.0","id":msg["id"],"result":result})
  if method=="exit": return 0
if __name__=="__main__": raise SystemExit(serve())
