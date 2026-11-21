"""NOO TAH: cross-platform Node.js integration for Reaper."""
from __future__ import annotations
import argparse, json, os, shutil, subprocess, sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Mapping, Sequence

@dataclass(frozen=True)
class Runtime:
    node: str
    npm_cli: str | None
    npx_cli: str | None

    @classmethod
    def discover(cls, explicit_node: str | None = None) -> "Runtime":
        candidate = explicit_node or os.environ.get("NOO_TAH_NODE") or shutil.which("node")
        if not candidate:
            raise RuntimeError("Node.js not found. Install Node.js LTS or set NOO_TAH_NODE.")
        path = Path(candidate).expanduser()
        node = str(path.resolve()) if path.is_file() else shutil.which(candidate)
        if not node:
            raise RuntimeError(f"Node.js executable does not exist: {candidate}")
        base = Path(node).parent
        def locate(override: str, names: list[Path]) -> str | None:
            choices = ([Path(os.environ[override]).expanduser()] if os.environ.get(override) else []) + names
            return next((str(p.resolve()) for p in choices if p.is_file()), None)
        npm = locate("NOO_TAH_NPM_CLI", [
            base/"node_modules/npm/bin/npm-cli.js",
            base.parent/"lib/node_modules/npm/bin/npm-cli.js",
            base.parent/"node_modules/npm/bin/npm-cli.js"])
        npx = locate("NOO_TAH_NPX_CLI", [
            base/"node_modules/npm/bin/npx-cli.js",
            base.parent/"lib/node_modules/npm/bin/npx-cli.js",
            base.parent/"node_modules/npm/bin/npx-cli.js"])
        return cls(node, npm, npx)

    def command(self, args: Sequence[str], *, cwd: Path | None = None,
                timeout: float | None = None, env: Mapping[str,str] | None = None,
                capture: bool = True) -> subprocess.CompletedProcess[str]:
        return subprocess.run([self.node,*map(str,args)], cwd=str(cwd) if cwd else None,
            env=dict(env) if env is not None else None, text=True, encoding="utf-8",
            errors="replace", capture_output=capture, timeout=timeout, check=False)

    def npm_command(self, args: Sequence[str], *, cwd: Path | None = None,
                    capture: bool = True) -> subprocess.CompletedProcess[str]:
        if not self.npm_cli: raise RuntimeError("npm-cli.js not found; set NOO_TAH_NPM_CLI.")
        return self.command([self.npm_cli,*args],cwd=cwd,capture=capture)

    def npx_command(self, args: Sequence[str], *, cwd: Path | None = None,
                    capture: bool = True) -> subprocess.CompletedProcess[str]:
        if not self.npx_cli: raise RuntimeError("npx-cli.js not found; set NOO_TAH_NPX_CLI.")
        return self.command([self.npx_cli,*args],cwd=cwd,capture=capture)

    def versions(self) -> dict[str,str | None]:
        def value(expr: str) -> str | None:
            result=self.command(["-p",expr])
            return result.stdout.strip() if result.returncode == 0 else None
        node=self.command(["--version"])
        if node.returncode: raise RuntimeError(node.stderr.strip() or "Node version query failed")
        npm=self.npm_command(["--version"]) if self.npm_cli else None
        return {"node":node.stdout.strip(),"npm":npm.stdout.strip() if npm and npm.returncode==0 else None,
            "v8":value("process.versions.v8"),"uv":value("process.versions.uv"),
            "platform":value("process.platform"),"architecture":value("process.arch"),
            "modules_abi":value("process.versions.modules"),"napi":value("process.versions.napi")}

    def doctor(self) -> dict[str,object]:
        probes={
          "core_modules":"for(const m of ['node:fs','node:http','node:https','node:net','node:tls','node:stream','node:buffer','node:crypto','node:path','node:os','node:events','node:worker_threads','node:child_process','node:dns','node:zlib'])require(m);console.log('ok')",
          "esm":"import('node:fs').then(()=>console.log('ok'))",
          "worker_threads":"const {Worker}=require('node:worker_threads');const w=new Worker('require(\\\"node:worker_threads\\\").parentPort.postMessage(1)',{eval:true});w.once('message',v=>console.log(v))",
          "streams":"const {Readable,Writable}=require('node:stream');Readable.from(['ok']).pipe(new Writable({write(c,e,cb){cb()}}))"
        }
        caps={}
        for name,source in probes.items():
            r=self.command(["-e",source],timeout=10)
            caps[name]={"ok":r.returncode==0,"stdout":r.stdout.strip(),"stderr":r.stderr.strip()}
        return {"runtime":asdict(self),"versions":self.versions(),"capabilities":caps}

def report(result: subprocess.CompletedProcess[str]) -> int:
    if result.stdout: print(result.stdout,end="" if result.stdout.endswith("\n") else "\n")
    if result.stderr: print(result.stderr,file=sys.stderr,end="" if result.stderr.endswith("\n") else "\n")
    return result.returncode

def build_parser() -> argparse.ArgumentParser:
    p=argparse.ArgumentParser(prog="reaper-noo-tah",description="Node.js runtime and ecosystem for Reaper")
    p.add_argument("--node",help="Explicit Node.js executable")
    s=p.add_subparsers(dest="action",required=True)
    s.add_parser("version"); s.add_parser("doctor")
    x=s.add_parser("run"); x.add_argument("file"); x.add_argument("args",nargs=argparse.REMAINDER)
    x=s.add_parser("check"); x.add_argument("file")
    x=s.add_parser("eval"); x.add_argument("source")
    x=s.add_parser("repl"); x.add_argument("args",nargs=argparse.REMAINDER)
    x=s.add_parser("npm"); x.add_argument("args",nargs=argparse.REMAINDER)
    x=s.add_parser("npx"); x.add_argument("args",nargs=argparse.REMAINDER)
    x=s.add_parser("install"); x.add_argument("--cwd",default="."); x.add_argument("--ci",action="store_true")
    x=s.add_parser("inspect"); x.add_argument("file"); x.add_argument("--host",default="127.0.0.1"); x.add_argument("--port",default="9229"); x.add_argument("--brk",action="store_true"); x.add_argument("args",nargs=argparse.REMAINDER)
    x=s.add_parser("project"); x.add_argument("--cwd",default=".")
    return p

def main(argv: Sequence[str] | None = None) -> int:
    p=build_parser(); a=p.parse_args(argv)
    try:
        rt=Runtime.discover(a.node)
        if a.action=="version": print(json.dumps(rt.versions(),indent=2)); return 0
        if a.action=="doctor":
            result=rt.doctor(); print(json.dumps(result,indent=2))
            return 0 if all(v["ok"] for v in result["capabilities"].values()) else 1
        if a.action=="run": return report(rt.command([a.file,*a.args],capture=False))
        if a.action=="check": return report(rt.command(["--check",a.file],capture=False))
        if a.action=="eval": return report(rt.command(["-e",a.source],capture=False))
        if a.action=="repl": return report(rt.command(a.args,capture=False))
        if a.action=="npm": return report(rt.npm_command(a.args or ["--help"],capture=False))
        if a.action=="npx": return report(rt.npx_command(a.args,capture=False))
        if a.action=="install": return report(rt.npm_command(["ci"] if a.ci else ["install"],cwd=Path(a.cwd).resolve(),capture=False))
        if a.action=="inspect":
            flag="--inspect-brk" if a.brk else "--inspect"
            return report(rt.command([f"{flag}={a.host}:{a.port}",a.file,*a.args],capture=False))
        if a.action=="project":
            root=Path(a.cwd).resolve(); file=root/"package.json"
            if not file.is_file(): raise RuntimeError(f"No package.json found in {root}")
            d=json.loads(file.read_text(encoding="utf-8"))
            print(json.dumps({"root":str(root),"name":d.get("name"),"version":d.get("version"),
              "type":d.get("type","commonjs"),"main":d.get("main"),"scripts":d.get("scripts",{}),
              "dependencies":len(d.get("dependencies",{})),"devDependencies":len(d.get("devDependencies",{})),
              "lockfiles":[n for n in ("package-lock.json","npm-shrinkwrap.json","yarn.lock","pnpm-lock.yaml") if (root/n).exists()]},indent=2))
            return 0
    except (RuntimeError,OSError,ValueError,subprocess.TimeoutExpired) as e:
        print(f"NOO TAH: {e}",file=sys.stderr); return 2
    p.error("unsupported action"); return 2

if __name__=="__main__": raise SystemExit(main())
