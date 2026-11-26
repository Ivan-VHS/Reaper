# MAZA — live foundation federation

MAZA is a language-level mechanism for attaching another Reaper foundation to a running Reaper process and keeping its exported interface live. It is intended for long-running applications that need to evolve shared capabilities without restarting the host on every compatible source update.

## Source syntax

```rpr
maza "foundations/telemetry.rpr" as telemetry

emit telemetry["schema_version"]
emit telemetry["snapshot"]()
emit maza_status("telemetry")["state"]
```

The exact Russian alias is also accepted:

```rpr
маза "foundations/telemetry.rpr" как telemetry
```

A MAZA declaration requires a quoted local `.rpr` path and an explicit namespace alias. The path is resolved relative to the importing source file. The target module exports names in the same way as ordinary Reaper modules:

```rpr
export make schema_version := "telemetry.v1"

craft snapshot() {
    yield "ready"
}
export snapshot
```

The namespace is a stable object. Refreshing a foundation updates that object in place, so consumers holding the namespace continue to observe the current exports.

## Lifetime and refresh

An attachment remains active for the lifetime of its `Interpreter`. The reference runtime checks due attachments at execution safe points; the default polling interval is 1,000 ms. A host that is idle between requests can use the foreground supervisor:

```sh
reaper --engine vm --maza-supervise application.rpr
```

The supervisor stays in the foreground, polls at the configured interval, and stops on Ctrl+C or process termination. It does not daemonize itself, survive a stopped process, or install an operating-system service. Production 24/7 deployment should run this foreground process under the target operating system's service manager and let that manager own restart policy, process identity, logs and shutdown.

When a changed source is valid, MAZA refreshes the export set and increments its revision. When parsing or execution fails, the last known-good namespace is retained and the link is marked `degraded`; the next poll can retry. The source is fingerprinted before and after loading to detect concurrent edits.

## Runtime operations

- `maza_links()` returns status records for all active links.
- `maza_status("alias")` returns one link's state, revision, source digest, interval and timestamps.
- `maza_refresh("alias")` requests an immediate refresh and returns the resulting status.
- `maza_detach("alias")` detaches a namespace.

The default limits are 128 live links, 2 MiB per foundation source (inherited from the module loader), and a 50–60,000 ms polling interval. Existing execution-step, call-depth, memory and collection limits remain in force.

## Trust and compatibility boundaries

MAZA is deliberately local-first:

- It accepts local `.rpr` files only. It does not fetch network or URL sources.
- It refuses symbolic-link source files.
- It does not load native libraries or binaries implicitly. Native FFI remains an explicit trusted-path capability.
- It does not grant a foundation privileged operating-system, device or driver access merely because it is attached.
- Reaper's ordinary module cycle checks, source limits and runtime quotas remain active.

Other project foundations and other languages join through explicit, versioned adapters and contracts; they are not treated as arbitrary executable `.rpr` text. Existing federation boundaries such as OPlague's read-only JSON snapshot and Pytyliki's explicit C ABI remain separate and retain their own validation and trust requirements.

## Implementation status

| Surface | Status |
|---|---|
| Lexer and parser | Implemented in the reference language frontend |
| Tree-walk runtime | Implemented |
| Canonical IR and VM | Implemented for the reference VM |
| Dependency graph scan | MAZA edges are included |
| Static type analysis | Namespace and built-in operation metadata included |
| Language service | Keyword and built-in completion metadata included |
| Native C17 AOT | Not supported; compilation fails explicitly for MAZA |
| Other-language / external foundations | Require explicit adapters and contracts |

The Python reference runtime is currently the execution host for both tree-walk and VM modes. MAZA support must not be confused with native C17 compiler parity.
