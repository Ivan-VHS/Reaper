"""Hash-chained local execution audit records for Reaper.

The chain is tamper-evident, not a digital signature or a trusted remote
attestation. Program output is deliberately not recorded.
"""
from __future__ import annotations
import hashlib
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ZERO_HASH = "0" * 64
_HASH_RE = re.compile(r"^[0-9a-f]{64}$")
_EVENT_RE = re.compile(r"^[a-z][a-z0-9_.-]{0,63}$")
_REQUIRED_FIELDS = {"sequence", "timestamp_utc", "event", "details", "previous_hash", "hash"}

class AuditLogError(ValueError):
    """Raised when an audit log cannot be written or fails verification."""

@dataclass(frozen=True, slots=True)
class AuditSummary:
    records: int
    last_hash: str

def _canonical_json(value: Any) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise AuditLogError(f"audit data is not canonical JSON: {error}") from error

def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise AuditLogError(f"duplicate JSON key: {key}")
        result[key] = value
    return result

def verify_audit_log(path: str | os.PathLike[str]) -> AuditSummary:
    """Verify sequence numbers, previous-hash links, and every record digest."""
    log_path = Path(path)
    if not log_path.exists():
        return AuditSummary(records=0, last_hash=ZERO_HASH)
    if not log_path.is_file():
        raise AuditLogError("audit log path is not a regular file")
    sequence = 0
    previous_hash = ZERO_HASH
    try:
        with log_path.open("r", encoding="utf-8") as stream:
            for line_number, line in enumerate(stream, start=1):
                if not line.strip():
                    raise AuditLogError(f"blank record at line {line_number}")
                try:
                    record = json.loads(line, object_pairs_hook=_unique_object)
                except (json.JSONDecodeError, AuditLogError) as error:
                    raise AuditLogError(f"invalid JSON at line {line_number}: {error}") from error
                if not isinstance(record, dict) or set(record) != _REQUIRED_FIELDS:
                    raise AuditLogError(f"unexpected record schema at line {line_number}")
                sequence += 1
                if type(record.get("sequence")) is not int or record["sequence"] != sequence:
                    raise AuditLogError(f"sequence mismatch at line {line_number}")
                if record.get("previous_hash") != previous_hash:
                    raise AuditLogError(f"broken hash link at line {line_number}")
                if not isinstance(record.get("timestamp_utc"), str) or not record["timestamp_utc"]:
                    raise AuditLogError(f"missing timestamp at line {line_number}")
                if not isinstance(record.get("event"), str) or not _EVENT_RE.fullmatch(record["event"]):
                    raise AuditLogError(f"invalid event name at line {line_number}")
                if not isinstance(record.get("details"), dict):
                    raise AuditLogError(f"details must be an object at line {line_number}")
                stored_hash = record.get("hash")
                if not isinstance(stored_hash, str) or not _HASH_RE.fullmatch(stored_hash):
                    raise AuditLogError(f"invalid record hash at line {line_number}")
                unhashed = {key: value for key, value in record.items() if key != "hash"}
                actual_hash = hashlib.sha256(_canonical_json(unhashed)).hexdigest()
                if actual_hash != stored_hash:
                    raise AuditLogError(f"record digest mismatch at line {line_number}")
                previous_hash = stored_hash
    except UnicodeDecodeError as error:
        raise AuditLogError(f"audit log is not valid UTF-8: {error}") from error
    except OSError as error:
        raise AuditLogError(f"cannot read audit log: {error}") from error
    return AuditSummary(records=sequence, last_hash=previous_hash)

class AuditLog:
    """Append-only, single-writer JSONL journal with a SHA-256 hash chain."""
    def __init__(self, path: str | os.PathLike[str]) -> None:
        self.path = Path(path)
        summary = verify_audit_log(self.path)
        self._sequence = summary.records
        self._last_hash = summary.last_hash

    def record(self, event: str, **details: Any) -> str:
        if not isinstance(event, str) or not _EVENT_RE.fullmatch(event):
            raise AuditLogError("event names must be lowercase identifiers")
        payload = {
            "sequence": self._sequence + 1,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            "event": event,
            "details": details,
            "previous_hash": self._last_hash,
        }
        digest = hashlib.sha256(_canonical_json(payload)).hexdigest()
        stored = dict(payload)
        stored["hash"] = digest
        line = _canonical_json(stored).decode("utf-8")
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8", newline="\n") as stream:
                stream.write(line + "\n")
                stream.flush()
                os.fsync(stream.fileno())
        except OSError as error:
            raise AuditLogError(f"cannot append audit record: {error}") from error
        self._sequence += 1
        self._last_hash = digest
        return digest
