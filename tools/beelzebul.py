#!/usr/bin/env python3
"""Compatibility entry point for the canonical packaged Beelzebul scanner."""
from __future__ import annotations

import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from reaper.security.beelzebul import (  # noqa: E402
    PolicyError,
    format_text,
    load_policy,
    main,
    scan_repository,
)

__all__ = ["PolicyError", "format_text", "load_policy", "main", "scan_repository"]

if __name__ == "__main__":
    raise SystemExit(main())
