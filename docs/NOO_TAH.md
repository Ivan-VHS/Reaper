# NOO TAH — Node.js runtime and ecosystem for Reaper

NOO TAH is Reaper's cross-platform Node.js integration. JavaScript semantics and
system behavior are supplied by the official Node.js distribution, not by a
partial Python imitation.

## Architecture

```text
Reaper Studio / CLI -> NOO TAH project + process manager
  -> Node discovery, npm/npx, diagnostics, inspector
  -> Official Node.js
       V8: parsing, JIT tiers, heap and garbage collection
       Node C/C++ bindings and core modules
       libuv: event loop, async I/O, OS pollers, worker pool
       Worker Threads: isolated V8 isolates
       N-API / node-gyp: native addon compatibility
  -> Windows IOCP | Linux epoll | macOS kqueue
```

## Compatibility surfaces

| Area | Provider |
|---|---|
| Language engine | V8, JIT, heap, garbage collection |
| Event loop and async I/O | libuv phases, timers, poll/check/close, OS pollers and thread pool |
| Core modules | fs, http, https, net, tls, dns, stream, buffer, crypto, path, os, events, zlib, timers, readline |
| Concurrency | worker_threads, child_process, cluster and libuv worker pool |
| Data pipelines | Readable, Writable, Duplex, Transform, pipeline and backpressure |
| Modules | CommonJS, ESM, exports/imports maps, dynamic import |
| Packages | npm, npx, package.json, lockfiles, lifecycle scripts |
| Native extensions | N-API, node-gyp and supported platform ABI |
| Diagnostics | Inspector / Chrome DevTools Protocol, profiling and heap snapshots |
| Networking | HTTP/1, HTTP/2, HTTPS, TCP, TLS, UDP, DNS; WebSocket through ecosystem packages |
| System | filesystem, process, environment, signals, paths and OS metadata |

These features come from the selected upstream Node binary. NOO TAH does not
claim a separately reimplemented engine or ABI.

## CLI

```sh
reaper-noo-tah version
reaper-noo-tah doctor
reaper-noo-tah run app.mjs -- --port 3000
reaper-noo-tah check app.js
reaper-noo-tah eval "console.log(process.versions)"
reaper-noo-tah repl
reaper-noo-tah npm run build
reaper-noo-tah npx eslint .
reaper-noo-tah install
reaper-noo-tah install --ci
reaper-noo-tah inspect server.mjs --port 9229
reaper-noo-tah project
```

Environment: NOO_TAH_NODE, NOO_TAH_NPM_CLI, NOO_TAH_NPX_CLI.
The npm JavaScript CLI is launched through Node instead of Windows batch shims.

## Project semantics

A Node project contains package.json. `.mjs` means ESM, `.cjs` means
CommonJS, and package.json `type` controls `.js`. Module resolution,
conditional exports, top-level await and dynamic import are delegated to Node.
Package installation and npm lifecycle scripts execute third-party code.

## Studio integration contract

Detect .js/.mjs/.cjs and package.json; launch Node as a managed child process;
stream stdout/stderr; expose stop/restart; preserve cwd and environment; surface
exit codes and diagnostics; attach the inspector protocol. CLI support alone
does not mean Studio integration is complete.

## Conformance gates

Test ESM/CJS, built-ins, module resolution, streams/backpressure, event-loop
ordering, timers/promises, async filesystem and network I/O, workers, child
processes, HTTP/TLS/TCP/UDP/DNS, npm lockfile reproducibility, N-API addons,
and process signals on Windows, Linux and macOS. Pin LTS versions and verify
signed checksums before managed installation. Report Node, V8, libuv, platform,
architecture, modules ABI and N-API versions.

An independent implementation of V8, libuv, bindings and npm is a separate
runtime-scale project. NOO TAH achieves compatibility by embedding/managing the
upstream Node runtime; certification is gated on the cross-platform test matrix.
