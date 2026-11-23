# Mora integration

This directory describes how the Reaper Studio desktop application can be registered by a future native Mora launcher.

## Manifest

\`manifest.json\` uses the DuckOS Mora application manifest v1.0.0 contract. It points to the repository's existing \`reaper_desktop.py\` entry point and the Python 3 runtime.

The declaration is **opt-in and not an active OS integration**. The current Mora HTML shell does not start native processes. The manifest has \`maturity_status: specified\` and \`verification_status: not_run\`; no installer, process broker or launch permission is added by this file.

## Local launch

From the Reaper repository root, the project's documented Studio entry point is:

\`\`\`sh
python reaper_desktop.py
\`\`\`

Install and launch using the repository's own requirements and trusted build instructions. Reaper's Python language runtime and Studio remain independently usable without Mora.

## Security boundary

A native launcher must validate the manifest, resolve the script beneath the trusted installed project root, choose a known Python runtime, pass arguments without shell interpolation and ask the operator to approve the first launch. A manifest must never cause an automatic installation or execution.

Project: [Ivan-VHS/Reaper](https://github.com/Ivan-VHS/Reaper). Project author/developer: Ivan-VHS.