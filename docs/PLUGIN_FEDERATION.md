# Cross-repository plugin federation

Reaper is the executable orchestration host for the 18 shared plugin identities. The canonical offline catalog is \`federation/plugins/catalog.v1.json\`; this repository's adapter manifest is \`federation/plugins/host.v1.json\`.

## Use from the Reaper runtime

\`\`\`python
from reaper.plugins import PluginManager

host = PluginManager()
catalog = host.list_plugins()
plan = host.run("Dropaul", steps=[
    {"id": "inspect", "depends_on": []},
    {"id": "verify", "depends_on": ["inspect"]},
])
\`\`\`

The 18 names resolve case-insensitively by stable kebab-case ID or display name. Existing operations in \`reaper.products\` remain the implementation source. The C17 native-language track is not advertised as a complete plugin host.

## Federation rules

- Every repository vendors the same catalog to keep offline builds deterministic.
- \`host.v1.json\` records which runtime owns each operation; the catalog itself does not grant execution authority.
- Cross-repository calls require an explicit adapter and a compatible API version. No implicit remote dispatch or network discovery is performed.
- Descriptive capabilities are not operating-system permissions.
- Project inspection and planning services remain bounded and do not execute arbitrary repository source or silently mutate project files.

## Compatibility

Catalog schema: \`schemas/ivan-vhs.plugin-catalog.v1.schema.json\`.
Manifest schema: \`ivan-vhs.plugin.v1\` for Ventu-compatible extension metadata.
Host contract: \`ivan-vhs.plugin-host.v1\`, API version 1.

The host manifest intentionally distinguishes executable built-ins from catalogue-only metadata in other runtimes.
