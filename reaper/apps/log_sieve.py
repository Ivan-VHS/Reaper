"""Parse delimited service logs and aggregate HTTP 5xx responses."""
from __future__ import annotations

from collections import Counter
from typing import Any

from .common import require_array, require_text


def run(payload: dict[str, Any]) -> dict[str, Any]:
    lines = require_array(payload, "lines")
    separator = require_text(payload.get("separator", " | "), "separator")
    parsed: list[dict[str, Any]] = []
    malformed: list[dict[str, Any]] = []
    for index, raw in enumerate(lines):
        try:
            line = require_text(raw, f"lines[{index}]", allow_empty=True)
            fields = [part.strip() for part in line.split(separator)]
            if len(fields) != 4:
                raise ValueError("malformed_log_line")
            timestamp, service, raw_code, message = fields
            if not service or not timestamp or not raw_code.isdecimal():
                raise ValueError("malformed_log_line")
            code = int(raw_code)
            if not 100 <= code <= 599:
                raise ValueError("status_code_out_of_range")
            parsed.append({"timestamp": timestamp, "service": service, "code": code, "message": message})
        except (TypeError, ValueError) as error:
            malformed.append({"index": index, "reason": str(error)})

    counts = Counter(item["service"] for item in parsed if item["code"] >= 500)
    groups = [{"service": service, "count": count}
              for service, count in sorted(counts.items(), key=lambda pair: (-pair[1], pair[0]))]
    errors = [item for item in parsed if item["code"] >= 500]
    return {
        "parsed": parsed,
        "server_errors": errors,
        "by_service": groups,
        "malformed": malformed,
        "counts": {"received": len(lines), "parsed": len(parsed), "server_errors": len(errors), "malformed": len(malformed)},
    }
