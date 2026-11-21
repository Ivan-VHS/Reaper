"""Small stdio JSON-RPC LSP bridge for Reaper Studio."""
from __future__ import annotations
import json, re, sys
from .language_service import LanguageService

class LspServer:
    def __init__(self):
        self.service = LanguageService()
    def dispatch(self, message):
        method, params, request_id = message.get("method"), message.get("params") or {}, message.get("id")
        result = None
        if method == "initialize":
            result = {"capabilities":{"textDocumentSync":{"openClose":True,"change":2},
                "completionProvider":{"triggerCharacters":[".",":"]},
                "definitionProvider":True,"referencesProvider":True,
                "renameProvider":True,"documentSymbolProvider":True},
                "serverInfo":{"name":"reaper-language-server","version":"0.1"}}
        elif method == "textDocument/didOpen":
            doc=params["textDocument"]; self.service.open(doc["uri"],doc["text"],doc.get("version",1)); return None
        elif method == "textDocument/didChange":
            doc=params["textDocument"]; self.service.change(doc["uri"],doc["version"],params["contentChanges"]); return None
        elif method == "textDocument/didClose":
            self.service.close(params["textDocument"]["uri"]); return None
        elif method == "textDocument/completion":
            uri=params["textDocument"]["uri"]; pos=params["position"]
            line=self.service._docs[uri].text.splitlines()[pos["line"]]
            prefix=re.search(r"[\w]*$",line[:pos["character"]]).group()
            result={"isIncomplete":False,"items":self.service.completion(uri,prefix)}
        elif method in {"textDocument/definition","textDocument/references","textDocument/rename"}:
            uri=params["textDocument"]["uri"]; pos=params["position"]
            line=self.service._docs[uri].text.splitlines()[pos["line"]]
            word=next((m.group() for m in re.finditer(r"\w+",line) if m.start()<=pos["character"]<=m.end()),"")
            if method.endswith("definition"):
                target=self.service.definition(uri,word)
                result=({"uri":uri,"range":_lsp_range(target.span)} if target else None)
            elif method.endswith("references"):
                result=[{"uri":uri,"range":_lsp_range(s)} for s in self.service.references(uri,word)]
            else:
                edits=self.service.rename(uri,word,params["newName"])
                result={"changes":{uri:[{"range":_lsp_range(s),"newText":t} for s,t in edits]}}
        elif method == "textDocument/documentSymbol":
            uri=params["textDocument"]["uri"]; a=self.service.result(uri) or self.service.analyze(uri)
            result=[{"name":s.name,"kind":12 if s.kind=="function" else 13,
                     "range":_lsp_range(s.span),"selectionRange":_lsp_range(s.span)} for s in a.symbols]
        elif method in {"initialized","$/cancelRequest","exit"}: return None
        elif method == "shutdown": self.service.shutdown(); return {"jsonrpc":"2.0","id":request_id,"result":None}
        elif request_id is not None:
            return {"jsonrpc":"2.0","id":request_id,"error":{"code":-32601,"message":"Method not found: "+str(method)}}
        return {"jsonrpc":"2.0","id":request_id,"result":result} if request_id is not None else None

def _lsp_range(span):
    return {"start":{"line":span.line,"character":span.start},
            "end":{"line":span.line,"character":span.end}}

def serve():
    server=LspServer(); reader,writer=sys.stdin.buffer,sys.stdout.buffer
    while True:
        header=reader.readline()
        if not header: break
        if not header.lower().startswith(b"content-length:"): continue
        length=int(header.split(b":",1)[1].strip())
        while reader.readline() not in (b"\r\n",b"\n",b""): pass
        message=json.loads(reader.read(length)); response=server.dispatch(message)
        if response is not None:
            body=json.dumps(response,separators=(",",":")).encode()
            writer.write(f"Content-Length: {len(body)}\r\n\r\n".encode()+body); writer.flush()
        if message.get("method")=="exit": break

if __name__ == "__main__": serve()
