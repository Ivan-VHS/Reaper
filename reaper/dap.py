"""DAP bridge to REAPER's statement-boundary RuntimeDebugger."""
from __future__ import annotations
import json,sys,threading
from pathlib import Path
from .debugger import DebugSnapshot,RuntimeDebugger
from .runtime import Interpreter

class DebugSession:
 def __init__(self,output):
  self.output=output; self.seq=1; self.lock=threading.RLock(); self.condition=threading.Condition()
  self.breakpoints=set(); self.snapshot=None; self.running=False; self.terminated=False
  self.worker=None; self.debugger=None; self.program=""
 def send(self,payload):
  with self.lock:
   payload.setdefault("seq",self.seq); self.seq+=1
   body=json.dumps(payload,ensure_ascii=False,separators=(",",":")).encode("utf-8")
   self.output.write(f"Content-Length: {len(body)}\r\n\r\n".encode("ascii")+body); self.output.flush()
 def response(self,req,body=None,success=True,message=None):
  item={"type":"response","request_seq":req.get("seq",0),"command":req.get("command",""),
        "success":success,"body":body or {}}
  if message: item["message"]=message
  self.send(item)
 def event(self,name,body=None): self.send({"type":"event","event":name,"body":body or {}})
 def pause_hook(self,snapshot:DebugSnapshot):
  with self.condition:
   self.snapshot=snapshot; self.event("stopped",{"reason":"breakpoint","threadId":1,"allThreadsStopped":True})
   while self.running and not self.terminated: self.condition.wait()
   if self.terminated:
    from .debugger import DebuggerStopped
    raise DebuggerStopped()
 def handle(self,req):
  cmd=req.get("command"); args=req.get("arguments") or {}
  if cmd=="initialize":
   self.response(req,{"supportsConfigurationDoneRequest":True,"supportsConditionalBreakpoints":False,
    "supportsEvaluateForHovers":False,"supportsTerminateRequest":True,"supportsSetVariable":False,
    "supportsStepBack":False,"supportsStepInTargetsRequest":False,"supportsDelayedStackTraceLoading":False})
   self.event("initialized")
  elif cmd=="launch":
   path=Path(args.get("program","")).expanduser().resolve()
   if not path.is_file(): self.response(req,success=False,message="launch requires an existing .rpr program file")
   else: self.program=str(path); self.response(req)
  elif cmd=="setBreakpoints":
   self.breakpoints={int(x["line"]) for x in args.get("breakpoints",[]) if isinstance(x.get("line"),int) and x["line"]>0}
   self.response(req,{"breakpoints":[{"verified":True,"line":n} for n in sorted(self.breakpoints)]})
  elif cmd=="configurationDone":
   if not self.program: self.response(req,success=False,message="launch must precede configurationDone")
   else: self.response(req); self.start()
  elif cmd=="threads": self.response(req,{"threads":[{"id":1,"name":"REAPER program"}]})
  elif cmd=="stackTrace":
   s=self.snapshot; frames=[]
   if s: frames=[{"id":1,"name":s.call_stack[-1] if s.call_stack else Path(s.filename).name,
    "source":{"name":Path(s.filename).name,"path":s.filename},"line":s.line,"column":s.column}]
   self.response(req,{"stackFrames":frames,"totalFrames":len(frames)})
  elif cmd=="scopes":
   self.response(req,{"scopes":[{"name":"Locals","variablesReference":1,"expensive":False}] if self.snapshot else []})
  elif cmd=="variables":
   values=self.snapshot.variables if self.snapshot else {}
   self.response(req,{"variables":[{"name":k,"value":repr(v),"type":type(v).__name__,"variablesReference":0} for k,v in sorted(values.items())]})
  elif cmd in ("continue","next","stepIn"):
   if not self.debugger: self.response(req,success=False,message="no active debug session")
   else:
    if cmd!="continue": self.debugger.step()
    with self.condition: self.running=False; self.condition.notify_all()
    self.response(req,{"allThreadsContinued":True})
  elif cmd=="pause": self.response(req,success=False,message="pause is available only at statement boundaries")
  elif cmd in ("terminate","disconnect"):
   self.terminated=True
   with self.condition: self.running=False; self.condition.notify_all()
   self.response(req); return cmd!="disconnect"
  elif cmd=="evaluate": self.response(req,success=False,message="expression evaluation is not implemented; inspect Locals instead")
  else: self.response(req,success=False,message=f"unsupported DAP request: {cmd}")
  return True
 def start(self):
  if self.worker and self.worker.is_alive(): return
  self.terminated=False; self.running=True; self.debugger=RuntimeDebugger(self.breakpoints,self.pause_hook)
  def execute():
   try:
    source=Path(self.program).read_text(encoding="utf-8")
    Interpreter(debugger=self.debugger).run(source,self.program)
    self.event("exited",{"exitCode":0})
   except Exception as error:
    self.event("output",{"category":"stderr","output":f"REAPER debug: {error}\n"})
    self.event("exited",{"exitCode":1})
   finally: self.event("terminated")
  self.worker=threading.Thread(target=execute,name="reaper-debuggee",daemon=True); self.worker.start()

def read_message(stream):
 headers={}
 while True:
  line=stream.readline()
  if not line: return None
  if line in (b"\r\n",b"\n"): break
  key,_,value=line.decode("ascii").partition(":"); headers[key.lower()]=value.strip()
 length=int(headers.get("content-length","0"))
 if length<0 or length>16*1024*1024: raise ValueError("invalid DAP Content-Length")
 body=stream.read(length)
 return json.loads(body.decode("utf-8")) if len(body)==length else None
def serve(stdin=None,stdout=None):
 stdin,stdout=stdin or sys.stdin.buffer,stdout or sys.stdout.buffer; session=DebugSession(stdout)
 while True:
  req=read_message(stdin)
  if req is None: return 0
  if req.get("type")=="request" and not session.handle(req): return 0
if __name__=="__main__": raise SystemExit(serve())
