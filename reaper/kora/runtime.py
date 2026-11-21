"""Kora standard library: 66 utility functions, standard-library-only."""
from __future__ import annotations
import asyncio, heapq, builtins as _builtins, json as _json, math, os, random, re, tempfile, threading, time as _time, unicodedata, textwrap, sys as _sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Mapping
from dataclasses import dataclass
class KoraError(ValueError): pass
@dataclass(frozen=True)
class Ok: value: object
@dataclass(frozen=True)
class Err: error: Exception
# ZDORO (11)
def clamp(x,lo,hi):
 if lo>hi: raise KoraError("min must not exceed max")
 return max(lo,min(hi,x))
def lerp(a,b,t): return a+(b-a)*t
def map_range(x,imin,imax,omin,omax):
 if imin==imax: raise KoraError("input range must not have zero width")
 return omin+(x-imin)*(omax-omin)/(imax-imin)
def round_to(x,decimals): return round(x,decimals)
def approx_eq(a,b,eps):
 if eps<0: raise KoraError("eps must be non-negative")
 return math.isclose(a,b,rel_tol=0,abs_tol=eps)
def sign(x): return (x>0)-(x<0)
def gcd(a,b):
 if not isinstance(a,int) or not isinstance(b,int): raise KoraError("integer arguments required")
 return math.gcd(a,b)
def lcm(a,b):
 if not isinstance(a,int) or not isinstance(b,int): raise KoraError("integer arguments required")
 return math.lcm(a,b)
def is_prime(n):
 if not isinstance(n,int) or isinstance(n,bool): raise KoraError("integer required")
 if n<2:return False
 if n%2==0:return n==2
 d=3
 while d*d<=n:
  if n%d==0:return False
  d+=2
 return True
def rand_int(lo,hi):
 if lo>hi:raise KoraError("min must not exceed max")
 return random.randint(lo,hi)
def rand_normal(mean,std):
 if std<0:raise KoraError("std must be non-negative")
 return random.gauss(mean,std)
# DILLY (11)
def slugify(s):return re.sub(r"[^a-z0-9]+","-",unicodedata.normalize("NFKD",_builtins.str(s)).encode("ascii","ignore").decode().lower()).strip("-")
def pad_both(s,n,fill=" "):
 s,fill=_builtins.str(s),_builtins.str(fill)
 if not fill:raise KoraError("fill must not be empty")
 m=max(0,n-len(s));l=m//2;r=m-l
 return (fill*((l+len(fill)-1)//len(fill)))[:l]+s+(fill*((r+len(fill)-1)//len(fill)))[:r]
def truncate(s,n,suffix="..."):
 s=_builtins.str(s)
 if n<0:raise KoraError("max_len must be non-negative")
 return s if len(s)<=n else suffix[:n] if len(suffix)>=n else s[:n-len(suffix)]+suffix
def between(s,left,right):
 s=_builtins.str(s);i=s.find(left)
 if i<0:return ""
 i+=len(left);j=s.find(right,i)
 return "" if j<0 else s[i:j]
def count_sub(s,sub):
 if not sub:raise KoraError("sub must not be empty")
 return _builtins.str(s).count(_builtins.str(sub))
def words(s):return re.findall(r"[^\W_]+(?:['’][^\W_]+)?",_builtins.str(s),re.UNICODE)
def to_camel(s):
 p=re.findall(r"[A-Za-z0-9]+",_builtins.str(s))
 return (p[0].lower() if p else "")+"".join(x[:1].upper()+x[1:] for x in p[1:])
def to_snake(s):
 s=re.sub(r"([a-z0-9])([A-Z])",r"\1_\2",_builtins.str(s));s=re.sub(r"([A-Z])([A-Z][a-z])",r"\1_\2",s)
 return re.sub(r"[^A-Za-z0-9]+","_",s).strip("_").lower()
def levenshtein(a,b):
 a,b=_builtins.str(a),_builtins.str(b)
 if len(a)<len(b):a,b=b,a
 row=list(range(len(b)+1))
 for i,x in enumerate(a,1):
  nxt=[i]
  for j,y in enumerate(b,1):nxt.append(min(nxt[-1]+1,row[j]+1,row[j-1]+(x!=y)))
  row=nxt
 return row[-1]
def template(tpl,values):return re.sub(r"\{\{\s*([^{}]+?)\s*\}\}",lambda m:_builtins.str(values.get(m.group(1).strip(),m.group(0))),_builtins.str(tpl))
def wrap(s,width):
 if width<1:raise KoraError("width must be positive")
 return "\n".join(textwrap.wrap(_builtins.str(s),width,break_long_words=False))
# BAPLAP (11)
def chunk(xs,n):
 if n<1:raise KoraError("size must be positive")
 return [list(xs[i:i+n]) for i in range(0,len(xs),n)]
def window(xs,n):
 if n<1:raise KoraError("size must be positive")
 return [list(xs[i:i+n]) for i in range(max(0,len(xs)-n+1))]
def compact(xs):return [x for x in xs if x is not None and x!=""]
def dedup_by(list,key_fn):
 seen=_builtins.set();out=[]
 for x in list:
  k=key_fn(x)
  if k not in seen:seen.add(k);out.append(x)
 return out
def group_by(xs,key_fn):
 out=defaultdict(list)
 for x in xs:out[key_fn(x)].append(x)
 return dict(out)
def partition(xs,pred_fn):
 a,b=[],[]
 for x in xs:(a if pred_fn(x) else b).append(x)
 return a,b
def zip_with(a,b,fn):return [fn(x,y) for x,y in zip(a,b)]
def flatten_depth(xs,depth):
 if depth<0:raise KoraError("depth must be non-negative")
 out=list(xs)
 for _ in range(depth):out=[y for x in out for y in (x if isinstance(x,(_builtins.list,tuple)) else [x])]
 return out
def sample(xs,k):
 if k<0 or k>len(xs):raise KoraError("k outside list bounds")
 return random.sample(list(xs),k)
def rotate(xs,shift):
 xs=list(xs)
 if not xs:return xs
 n=shift%len(xs)
 return xs[-n:]+xs[:-n] if n else xs
def binary_search(xs,target):
 lo,hi=0,len(xs)
 while lo<hi:
  m=(lo+hi)//2
  if xs[m]<target:lo=m+1
  else:hi=m
 return lo if lo<len(xs) and xs[lo]==target else -1
# KALI (11)
def get_path(obj,path,default_val=None):
 cur=obj
 for key in _builtins.str(path).split("."):
  if isinstance(cur,Mapping) and key in cur:cur=cur[key]
  elif isinstance(cur,(list,tuple)) and key.isdigit() and int(key)<len(cur):cur=cur[int(key)]
  else:return default_val
 return cur
def set_path(obj,path,value):
 out=dict(obj);cur=out;parts=_builtins.str(path).split(".")
 for key in parts[:-1]:
  child=cur.get(key,{});child=dict(child) if isinstance(child,dict) else {};cur[key]=child;cur=child
 cur[parts[-1]]=value
 return out
def pick(obj,keys):return {k:obj[k] for k in keys if k in obj}
def omit(obj,keys):
 keys=_builtins.set(keys);return {k:v for k,v in obj.items() if k not in keys}
def deep_merge(base,override):
 out=dict(base)
 for k,v in override.items():out[k]=deep_merge(out[k],v) if isinstance(out.get(k),dict) and isinstance(v,dict) else v
 return out
def invert(obj):
 out={}
 for k,v in obj.items():
  if v in out:raise KoraError(f"duplicate value: {v!r}")
  out[v]=k
 return out
def filter_entries(obj,pred_fn):return {k:v for k,v in obj.items() if pred_fn(k,v)}
def set_union(a,b):return _builtins.set(a)|_builtins.set(b)
def set_intersect(a,b):return _builtins.set(a)&_builtins.set(b)
def set_diff(a,b):return _builtins.set(a)-_builtins.set(b)
def heap_push_pop(heap_ref,item,cmp_fn=None):
 if cmp_fn is None:return heapq.heappushpop(heap_ref,item)
 heap_ref.append(item);i=len(heap_ref)-1
 while i:
  p=(i-1)//2
  if cmp_fn(heap_ref[i],heap_ref[p])>=0:break
  heap_ref[i],heap_ref[p]=heap_ref[p],heap_ref[i];i=p
 root=heap_ref[0];last=heap_ref.pop()
 if heap_ref:
  heap_ref[0]=last;i=0
  while True:
   l=2*i+1;r=l+1;b=i
   if l<len(heap_ref) and cmp_fn(heap_ref[l],heap_ref[b])<0:b=l
   if r<len(heap_ref) and cmp_fn(heap_ref[r],heap_ref[b])<0:b=r
   if b==i:break
   heap_ref[i],heap_ref[b]=heap_ref[b],heap_ref[i];i=b
 return root
# PYEMONT (11)
def pipe(value,fns):
 for f in fns:value=f(value)
 return value
def compose(fns):
 fs=list(fns)
 def apply(value):
  for f in reversed(fs):value=f(value)
  return value
 return apply
def memoize(fn,ttl_ms):
 cache={};lock=threading.RLock()
 def call(*a,**kw):
  key=(a,tuple(sorted(kw.items())));now=_time.monotonic()*1000
  with lock:
   if key in cache and (ttl_ms is None or now-cache[key][0]<ttl_ms):return cache[key][1]
  value=fn(*a,**kw)
  with lock:cache[key]=(now,value)
  return value
 call.cache_clear=cache.clear
 return call
def once(fn):
 lock=threading.Lock();state={}
 def call(*a,**kw):
  with lock:
   if "value" not in state:state["value"]=fn(*a,**kw)
   return state["value"]
 return call
def debounce(fn,wait_ms):
 lock=threading.Lock();state={"timer":None}
 def call(*a,**kw):
  def run():fn(*a,**kw)
  with lock:
   if state["timer"]:state["timer"].cancel()
   state["timer"]=threading.Timer(max(0,wait_ms)/1000,run);state["timer"].daemon=True;state["timer"].start()
 call.cancel=lambda:state["timer"].cancel() if state["timer"] else None
 return call
def throttle(fn,interval_ms):
 lock=threading.Lock();state={"last":-float("inf")}
 def call(*a,**kw):
  now=_time.monotonic()*1000
  with lock:
   if now-state["last"]<interval_ms:return None
   state["last"]=now
  return fn(*a,**kw)
 return call
def try_run(fn,*a,**kw):
 try:return Ok(fn(*a,**kw))
 except Exception as e:return Err(e)
def retry(fn,attempts,backoff_ms,*a,**kw):
 if attempts<1:raise KoraError("attempts must be >= 1")
 for i in range(attempts):
  try:return fn(*a,**kw)
  except Exception:
   if i==attempts-1:raise
   _time.sleep(max(0,backoff_ms)*2**i/1000)
def ensure(cond,message):
 if not cond:raise KoraError(_builtins.str(message))
 return cond
async def all_settled(tasks):
 async def one(task):
  try:return {"status":"fulfilled","value":await task}
  except Exception as e:return {"status":"rejected","reason":e}
 return await asyncio.gather(*(one(t) for t in tasks))
async def race_timeout(task,timeout_ms):return await asyncio.wait_for(task,max(0,timeout_ms)/1000)
# LIUR (6)
def read_text(path,encoding="utf-8"):return Path(path).read_text(encoding=encoding)
def write_atomic(path,content):
 target=Path(path);target.parent.mkdir(parents=True,exist_ok=True);fd,tmp=tempfile.mkstemp(prefix="."+target.name+".",dir=target.parent)
 try:
  with os.fdopen(fd,"w",encoding="utf-8",newline="") as f:f.write(_builtins.str(content));f.flush();os.fsync(f.fileno())
  os.replace(tmp,target)
 except BaseException:
  try:os.unlink(tmp)
  except OSError:pass
  raise
 return _builtins.str(target)
class DirectoryWatcher:
 def __init__(self,path,on_event,interval=.25):
  self.path=Path(path);self.callback=on_event;self.interval=interval;self.stopped=threading.Event()
  if not self.path.is_dir():raise KoraError(f"directory not found: {path}")
  self.snapshot=self.scan();self.thread=threading.Thread(target=self.run,daemon=True);self.thread.start()
 def scan(self):return {p.name:(p.stat().st_mtime_ns,p.stat().st_size) for p in self.path.iterdir()}
 def run(self):
  while not self.stopped.wait(self.interval):
   try:
    now=self.scan()
    for n in now.keys()-self.snapshot.keys():self.callback({"event":"created","path":_builtins.str(self.path/n)})
    for n in self.snapshot.keys()-now.keys():self.callback({"event":"deleted","path":_builtins.str(self.path/n)})
    for n in now.keys()&self.snapshot.keys():
     if now[n]!=self.snapshot[n]:self.callback({"event":"modified","path":_builtins.str(self.path/n)})
    self.snapshot=now
   except Exception as e:self.callback({"event":"error","error":e})
 def close(self):self.stopped.set();self.thread.join(timeout=max(1,self.interval*4))
def watch_dir(path,on_event):return DirectoryWatcher(path,on_event)
def env_get(name,default_val=None):return os.environ.get(name,default_val)
def args():return list(_sys.argv[1:])
def type_of(v):
 if v is None:return "null"
 if isinstance(v,bool):return "boolean"
 if isinstance(v,int):return "integer"
 if isinstance(v,float):return "number"
 if isinstance(v,_builtins.str):return "string"
 if isinstance(v,list):return "array"
 if isinstance(v,dict):return "object"
 if callable(v):return "function"
 return type(v).__name__
# SRETUO (5)
def parse_safe(raw):
 try:return Ok(_json.loads(raw))
 except (ValueError,TypeError) as e:return Err(e)
def stringify_pretty(value,indent=2):return _json.dumps(value,ensure_ascii=False,indent=indent,allow_nan=False)
def now_ms():return int(_time.time()*1000)
def format_iso(ms,tz="UTC"):
 from zoneinfo import ZoneInfo
 return datetime.fromtimestamp(ms/1000,tz=timezone.utc if tz in ("UTC","Z") else ZoneInfo(tz)).isoformat()
async def sleep(ms):await asyncio.sleep(max(0,ms)/1000)
num=SimpleNamespace(clamp=clamp,lerp=lerp,map_range=map_range,round_to=round_to,approx_eq=approx_eq,sign=sign,gcd=gcd,lcm=lcm,is_prime=is_prime,rand_int=rand_int,rand_normal=rand_normal)
str=SimpleNamespace(slugify=slugify,pad_both=pad_both,truncate=truncate,between=between,count_sub=count_sub,words=words,to_camel=to_camel,to_snake=to_snake,levenshtein=levenshtein,template=template,wrap=wrap)
arr=SimpleNamespace(chunk=chunk,window=window,compact=compact,dedup_by=dedup_by,group_by=group_by,partition=partition,zip_with=zip_with,flatten_depth=flatten_depth,sample=sample,rotate=rotate,binary_search=binary_search)
map=SimpleNamespace(get_path=get_path,set_path=set_path,pick=pick,omit=omit,deep_merge=deep_merge,invert=invert,filter_entries=filter_entries)
set=SimpleNamespace(union=set_union,intersect=set_intersect,diff=set_diff);heap=SimpleNamespace(push_pop=heap_push_pop)
fn=SimpleNamespace(pipe=pipe,compose=compose,memoize=memoize,once=once,debounce=debounce,throttle=throttle)
err=SimpleNamespace(try_run=try_run,retry=retry,ensure=ensure);async_=SimpleNamespace(all_settled=all_settled,race_timeout=race_timeout)
io=SimpleNamespace(read_text=read_text,write_atomic=write_atomic,watch_dir=watch_dir)
json=SimpleNamespace(parse_safe=parse_safe,stringify_pretty=stringify_pretty)
time=SimpleNamespace(now_ms=now_ms,format_iso=format_iso,sleep=sleep)
sys=SimpleNamespace(env_get=env_get,args=args);meta=SimpleNamespace(type_of=type_of)
API={"num":num,"str":str,"arr":arr,"map":map,"set":set,"heap":heap,"fn":fn,"err":err,"async":async_,"io":io,"json":json,"time":time,"sys":sys,"meta":meta}
def call(module,function,*args,**kwargs):
 try:func=getattr(API[module],function)
 except (KeyError,AttributeError) as e:raise KoraError(f"unknown Kora function: {module}.{function}") from e
 return func(*args,**kwargs)
FUNCTION_COUNT=66
