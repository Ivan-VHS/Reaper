"""Validate localized build artifact metadata without claiming a MOST compiler backend."""
from __future__ import annotations

import re
from typing import Any

from .common import ApplicationInputError, require_integer, require_object, require_text

_SHA256 = re.compile(r"^[0-9a-fA-F]{64}$")


def run(payload: dict[str, Any]) -> dict[str, Any]:
    artifact = require_object(payload.get("artifact"), "artifact")
    name = require_text(artifact.get("name"), "artifact.name")
    size = require_integer(artifact.get("size_bytes"), "artifact.size_bytes", minimum=1)
    checksum = require_text(artifact.get("sha256"), "artifact.sha256")
    if not _SHA256.fullmatch(checksum):
        raise ApplicationInputError("artifact.sha256 must contain exactly 64 hexadecimal characters")
    locale = payload.get("locale", "ru-RU")
    if not isinstance(locale, str) or not locale.strip() or len(locale) > 32:
        raise ApplicationInputError("locale must be a non-empty locale tag of at most 32 characters")
    return {
        "artifact": {"name": name, "size_bytes": size, "sha256": checksum.lower()},
        "status": "ready_for_release_review",
        "locale": locale,
        "checks": {"non_empty": True, "sha256_format": True},
        "compiler_invoked": False,
        "note": "This is an artifact preflight check; it does not compile MOST source.",
    }
