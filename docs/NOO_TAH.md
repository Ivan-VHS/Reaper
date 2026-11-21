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
reaper-noo-tah inspect --port 9229 server.mjs
reaper-noo-tah project
```

Environment: NOO_TAH_NODE, NOO_TAH_NPM_CLI, NOO_TAH_NPX_CLI.
The npm JavaScript CLI is launched through Node instead of Windows batch shims.

## Project semantics

A Node project contains package.json. `.mjs` means ESM, `.cjs` means
CommonJS, and package.json `type` controls `.js`. Module resolution,
conditional exports, top-level await and dynamic import are delegated to Node.
Package installation and npm lifecycle scripts execute third-party code.

## Reaper Studio integration

Studio recognizes .js/.mjs/.cjs in the project tree and file dialogs. It provides
JS Run, JS Check, JS Debug (Node Inspector), JS Stop, npm command execution and
runtime diagnostics. Managed child-process output is streamed into the IDE,
the project/script directory is used as cwd, unsaved editor buffers are saved
before execution, and exit codes are reported.

JS Debug launches Node with `--inspect-brk` and prints the attach endpoint for
Chrome DevTools (`chrome://inspect`). The Inspector protocol is real Node
functionality, but translating Inspector breakpoints, scopes, call frames and
variable handles into Reaper's native DAP debugger panes remains a separate
integration milestone. JavaScript syntax coloring is currently the shared
lightweight editor highlighter, not a complete TypeScript/JavaScript LSP.

## Conformance suite

Run `node --test tests/noo_tah/conformance.test.mjs`. The suite exercises
runtime metadata, ESM and CommonJS, binary filesystem I/O, crypto, bounded
stream pipelines/backpressure, loopback HTTP and TCP, worker_threads,
child_process exit propagation, localhost DNS and event-loop microtask ordering.
The GitHub Actions matrix runs it on Node 22 and 24 across Windows, Linux and
macOS. It uses only Node built-ins and loopback networking; it does not depend
on third-party packages or public network access.

## Remaining conformance gates

Add version-pinned coverage for TLS certificates and HTTPS, UDP, cluster,
N-API native addon compilation, npm lockfile reproducibility, lifecycle-script
policy, process signals and platform-specific filesystem semantics. Managed
Node provisioning must verify signed checksums and support rollback. Report Node,
V8, libuv, platform, architecture, modules ABI and N-API versions.

An independent implementation of V8, libuv, bindings and npm is a separate
runtime-scale project. NOO TAH achieves compatibility by embedding/managing the
upstream Node runtime; certification is gated on the cross-platform test matrix.
