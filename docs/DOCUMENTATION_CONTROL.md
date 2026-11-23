# Documentation control

| # | Gate | Acceptance |
|---:|---|---|
| 1 | Evidence | implemented claims point to code/tests |
| 2 | Status | implemented / partial / planned / not applicable |
| 3 | Privacy | no private files, secrets or local identifiers |
| 4 | Contract | exact syntax, formats, limits and exclusions |
| 5 | Compatibility | version public changes and migration |
| 6 | Review | links, commands and numeric claims verified |

## Internal information architecture

| # | Gate | Acceptance |
|---:|---|---|
| 7 | Topic ownership | Every important page belongs to one primary topic cluster and is listed in the central map. |
| 8 | Navigation depth | Important contracts are reachable within three to four steps from the root README. |
| 9 | No orphan pages | Each important page has at least two useful incoming paths, normally the catalog and its topic hub. |
| 10 | Contextual relationships | Link language, compiler, runtime, IDE and integration pages where a real dependency or workflow exists. |
| 11 | Descriptive anchors | Anchor text identifies the destination; do not use vague labels or over-optimized repeated keywords. |
| 12 | Capability consistency | README, hub, detailed contract, source and tests agree on capability status, syntax, limits and compatibility. |
| 13 | Canonical paths | Use direct relative links within the repository and canonical HTTPS links across repositories; avoid avoidable redirects and duplicates. |
| 14 | Breadcrumbs | Topic hubs link to documentation home and the parent information map; add equivalent breadcrumbs to new deep-level pages. |
| 15 | Link density | Add links where they help the reader; avoid repetitive blocks and link-heavy paragraphs. |
| 16 | Publication propagation | Add new pages to the hub and catalog in the same change and link them from relevant existing material. |
| 17 | Link maintenance | Check changed and moved paths; periodically audit for broken or obsolete links. |
| 18 | Measurement | Track navigation only on supported published surfaces with privacy-respecting analytics; do not claim GitHub Markdown click telemetry. |
| 19 | Accessibility | Use meaningful anchor text, normal same-tab internal navigation and rendered links that remain usable on small screens. |

The [information architecture map](INFORMATION_ARCHITECTURE.md) is the navigation source for this repository. It does not override implementation evidence or promote planned features to implemented status.
