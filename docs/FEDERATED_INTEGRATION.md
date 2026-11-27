# Federated integration

| Peer | Format | Boundary |
|---|---|---|
| OPlague | versioned device snapshot JSON | read-only |
| Pytyliki | C ABI v1 | explicit trusted library path |

Validate schema, version, bounds and provenance. Native code is never loaded implicitly. Device/driver state is never mutated through federation.

## MAZA live foundation attachment

MAZA adds a Reaper-language attachment layer for local `.rpr` foundation wrappers:

```rpr
maza "foundations/device-audit.rpr" as device_audit
emit device_audit["status"]()
```

The attached namespace stays stable while valid source revisions are refreshed by the running reference runtime or VM. A failed refresh retains the last known-good exports. See [MAZA](MAZA.md) for syntax, lifecycle, limits and the foreground 24/7 supervisor.

MAZA does **not** replace or bypass peer contracts:

- **OPlague:** continue consuming versioned device-snapshot JSON through the read-only federation adapter. A Reaper `.rpr` wrapper may expose selected, validated snapshot data through MAZA; it must not mutate driver or device state.
- **Pytyliki:** continue using the explicit C ABI v1 bridge and trusted-library opt-in. MAZA never loads a native library by itself.
- **Other projects and languages:** add a versioned, project-owned adapter first, with bounded input, schema/version validation and an explicit trust boundary. Then expose only the adapter's safe Reaper-facing API through a local `.rpr` foundation.

A MAZA link is a live language namespace, not an OS privilege grant, a distributed code loader or a native-binary hot-swap mechanism.
