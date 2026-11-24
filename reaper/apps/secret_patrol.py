"""Scan supplied text snapshots for likely credentials and redact evidence snippets."""
from __future__ import annotations

import re
from typing import Any

from .common import require_array, require_object, require_text

_PATTERNS = (
    ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "high"),
    ("private_key_marker", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |PGP )?PRIVATE KEY-----"), "critical"),
    ("github_token", re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"), "high"),
    ("credential_assignment", re.compile(
        r"(?i)\b(password|passwd|secret|token|api[_-]?key)\b\s*[:=]\s*(['\"]?)([^\s,'\";]+)"
    ), "high"),
)


def _redact(line: str) -> str:
    rendered = line
    rendered = re.sub(r"\bAKIA[0-9A-Z]{16}\b", "AKIA[REDACTED]", rendered)
    rendered = re.sub(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b", "[REDACTED_TOKEN]", rendered)
    rendered = re.sub(
        r"(?i)\b(password|passwd|secret|token|api[_-]?key)\b(\s*[:=]\s*)(['\"]?)([^\s,'\";]+)",
        lambda match: match.group(1) + match.group(2) + match.group(3) + "[REDACTED]",
        rendered,
    )
    if "PRIVATE KEY-----" in rendered:
        return "[PRIVATE KEY MATERIAL REDACTED]"
    return rendered[:240]


def run(payload: dict[str, Any]) -> dict[str, Any]:
    files = require_array(payload, "files")
    findings: list[dict[str, Any]] = []
    for file_index, item in enumerate(files):
        file = require_object(item, f"files[{file_index}]")
        path = require_text(file.get("path"), f"files[{file_index}].path")
        content = require_text(file.get("content"), f"files[{file_index}].content", allow_empty=True)
        for line_number, line in enumerate(content.splitlines(), start=1):
            for name, pattern, severity in _PATTERNS:
                if pattern.search(line):
                    findings.append({
                        "path": path,
                        "line": line_number,
                        "kind": name,
                        "severity": severity,
                        "snippet": _redact(line),
                    })
    return {
        "findings": findings,
        "files_scanned": len(files),
        "finding_count": len(findings),
        "scan_scope": "caller_supplied_text_only",
    }
