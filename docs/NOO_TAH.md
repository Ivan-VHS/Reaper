# NOO TAH — Node.js compatibility system

NOO TAH is Reaper's managed integration layer for the Node.js runtime and its
tooling. Its compatibility target is the official Node.js distribution, not a
partial JavaScript interpreter implemented inside Reaper.

## Runtime contract

| Surface | Provider | Contract |
|---|---|---|
| JavaScript language | V8 via Node.js | ECMAScript supported by selected Node release |
| Event loop and async I/O | libuv via Node.js | Native Node scheduling and I/O behavior |
| Core modules | Node.js | \`node:*\` modules and documented Node APIs |
| Modules | Node.js | CommonJS, ESM, package exports and resolution |
| Packages | npm | package.json, lockfiles, npm install / ci |
| Native extensions | Node.js toolchain | ABI and platform constraints of selected Node version |
| Debugging | Node inspector | Chrome DevTools Protocol endpoint |
| Reaper integration | NOO TAH | Discovery, CLI, project launch, diagnostics and future Studio adapter |

## Commands

\`\`\`sh
reaper-noo-tah version
reaper-noo-tah run app.mjs
reaper-noo-tah check app.js
reaper-noo-tah inspect app.mjs
reaper-noo-tah npm run build
reaper-noo-tah install
reaper-noo-tah install --ci
\`\`\`

Install an official Node.js LTS distribution and npm. NOO TAH discovers
\`node\` and \`npm\` on PATH; \`NOO_TAH_NODE\` and \`NOO_TAH_NPM\` override
discovery. An explicit executable can also be supplied with \`--node\`.

## Compatibility policy

1. Delegate JavaScript semantics and Node APIs to the upstream Node runtime.
2. Do not silently translate JavaScript into Reaper syntax.
3. Preserve Node exit codes, stdout, stderr, working directory and argument order.
4. Never invoke commands through a shell; pass arguments as an argv array.
5. Keep Node version selection explicit and reproducible in project metadata.
6. Treat npm lifecycle scripts and third-party packages as executable, untrusted code.
7. Run package installation only when explicitly requested by the developer.
8. Record the Node version, platform, architecture and lockfile in build diagnostics.

## Project integration roadmap

- **Bridge (this release):** runtime discovery, version reporting, run, syntax
  check, npm forwarding, dependency installation and inspector launch.
- **Studio:** JavaScript project detection, run configurations, diagnostics,
  process lifecycle, terminal output and inspector protocol adapter.
- **Conformance:** version-pinned Node test corpus covering ESM/CJS, built-ins,
  streams, buffers, timers, workers, child processes, filesystem, networking,
  errors and package resolution.
- **Distribution:** signed, platform-specific Node runtime provisioning with
  checksums, update channel, rollback and license notices.

## What “full compatibility” means

NOO TAH can provide Node.js behavior by executing the official Node.js runtime.
A standalone Reaper-owned reimplementation of V8, libuv, Node's native bindings,
the full core-module surface and npm is a separate multi-year runtime project.
The bridge is therefore the compatibility foundation, not a claim that every
Studio workflow or every Node release has already been certified.
