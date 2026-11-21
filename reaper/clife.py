"""CLife checkpointing and bounded recovery for Reaper projects.

Snapshots preserve caller-supplied project bytes. They are never executed on restore.
"""
from __future__ import annotations
import argparse, base64, hashlib, json, math, os, tempfile
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

SCHEMA = "clife.checkpoint.v1"
MAX_PAYLOAD_BYTES = 64 * 1024 * 1024

class ClifeError(ValueError):
    """Invalid checkpoint, recovery state, or CLife argument."""

class FaultType(str, Enum):
    STORAGE_IO = "storage_io"
    ARTIFACT_INTEGRITY = "artifact_integrity"
    RESOURCE_PRESSURE = "resource_pressure"
    EXECUTION_INTERRUPTION = "execution_interruption"

class AwakeningBranch(str, Enum):
    NORMAL_RESUME = "normal_resume"
    VERIFIED_RESTORE = "verified_restore"
    PARTIAL_HOLD = "partial_hold"
    EMERGENCY_SAFE_STOP = "emergency_safe_stop"

def _validate_identity(project_id: Any, generation: Any) -> None:
    if not isinstance(project_id, str) or not project_id.strip() or len(project_id) > 128:
        raise ClifeError("project_id must be non-empty text of at most 128 characters")
    if isinstance(generation, bool) or not isinstance(generation, int) or generation < 0:
        raise ClifeError("generation must be a non-negative integer")

@dataclass(frozen=True, slots=True)
class Snapshot:
    project_id: str
    generation: int
    payload: bytes
    checksum_sha256: str
    schema: str = SCHEMA

    @classmethod
    def capture(cls, project_id: str, generation: int, payload: bytes) -> "Snapshot":
        _validate_identity(project_id, generation)
        if not isinstance(payload, bytes) or len(payload) > MAX_PAYLOAD_BYTES:
            raise ClifeError("payload must be bytes within the 64 MiB limit")
        return cls(project_id, generation, payload, hashlib.sha256(payload).hexdigest())

    def verify(self) -> bool:
        try:
            _validate_identity(self.project_id, self.generation)
            return self.schema == SCHEMA and isinstance(self.payload, bytes) and len(self.payload) <= MAX_PAYLOAD_BYTES and self.checksum_sha256 == hashlib.sha256(self.payload).hexdigest()
        except (ClifeError, TypeError):
            return False

    def to_dict(self) -> dict[str, Any]:
        if not self.verify():
            raise ClifeError("refusing to serialize an invalid checkpoint")
        return {"schema": self.schema, "project_id": self.project_id, "generation": self.generation,
                "payload_encoding": "base64", "payload": base64.b64encode(self.payload).decode("ascii"),
                "checksum_algorithm": "sha256", "checksum": self.checksum_sha256}

    @classmethod
    def from_dict(cls, value: Any) -> "Snapshot":
        if not isinstance(value, dict) or value.get("schema") != SCHEMA:
            raise ClifeError("unsupported checkpoint schema")
        if value.get("payload_encoding") != "base64" or value.get("checksum_algorithm") != "sha256":
            raise ClifeError("unsupported checkpoint encoding or checksum")
        encoded, checksum = value.get("payload"), value.get("checksum")
        if not isinstance(encoded, str) or len(encoded) > ((MAX_PAYLOAD_BYTES + 2) // 3) * 4:
            raise ClifeError("invalid or oversized checkpoint payload")
        if not isinstance(checksum, str) or len(checksum) != 64:
            raise ClifeError("invalid SHA-256 field")
        try:
            payload = base64.b64decode(encoded, validate=True)
        except (ValueError, base64.binascii.Error) as exc:
            raise ClifeError("invalid base64 checkpoint payload") from exc
        result = cls(value.get("project_id"), value.get("generation"), payload, checksum, value["schema"])
        if not result.verify():
            raise ClifeError("checkpoint checksum or metadata verification failed")
        return result

def save_snapshot(snapshot: Snapshot, path: str | Path) -> Path:
    target = Path(path)
    if not snapshot.verify():
        raise ClifeError("refusing to save an unverified checkpoint")
    target.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(snapshot.to_dict(), sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    if len(data) > MAX_PAYLOAD_BYTES * 2:
        raise ClifeError("serialized checkpoint exceeds the size limit")
    temp_name = None
    try:
        with tempfile.NamedTemporaryFile("wb", dir=target.parent, prefix=f".{target.name}.", suffix=".tmp", delete=False) as stream:
            temp_name = stream.name
            stream.write(data); stream.flush(); os.fsync(stream.fileno())
        os.replace(temp_name, target)
    except OSError as exc:
        if temp_name:
            try: os.unlink(temp_name)
            except OSError: pass
        raise ClifeError(f"atomic checkpoint write failed: {exc}") from exc
    return target

def load_snapshot(path: str | Path) -> Snapshot:
    source = Path(path)
    try:
        if source.stat().st_size > MAX_PAYLOAD_BYTES * 2:
            raise ClifeError("checkpoint file exceeds the size limit")
        value = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ClifeError(f"cannot read checkpoint: {exc}") from exc
    return Snapshot.from_dict(value)

def restore_snapshot(snapshot: Snapshot, expected_project_id: str) -> bytes:
    if not snapshot.verify():
        raise ClifeError("checkpoint verification failed")
    if snapshot.project_id != expected_project_id:
        raise ClifeError("checkpoint belongs to a different project")
    return bytes(snapshot.payload)

@dataclass(slots=True)
class RuntimeState:
    project_id: str
    generation: int = 0
    artifact_integrity: float = 1.0
    resource_health: float = 1.0
    execution_health: float = 1.0
    recovery_locked: bool = False

@dataclass(slots=True)
class FaultEvent:
    fault_type: FaultType
    severity: float
    mitigated: bool = False

def _unit(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0.0 <= value <= 1.0:
        raise ClifeError(f"{name} must be finite and between 0 and 1")
    return float(value)

def branch_awakening(state: RuntimeState, snapshot: Snapshot | None, external_threat: float = 0.0) -> AwakeningBranch:
    threat = _unit(external_threat, "external_threat")
    integrity = _unit(state.artifact_integrity, "artifact_integrity")
    resources = _unit(state.resource_health, "resource_health")
    execution = _unit(state.execution_health, "execution_health")
    viability = 0.5 * integrity + 0.25 * resources + 0.25 * execution
    snapshot_ok = bool(snapshot is not None and snapshot.verify() and snapshot.project_id == state.project_id and snapshot.generation <= state.generation)
    if threat > 0.85 and viability < 0.70:
        state.recovery_locked = True
        return AwakeningBranch.EMERGENCY_SAFE_STOP
    if viability >= 0.95 and execution >= 0.95:
        state.recovery_locked = False
        return AwakeningBranch.NORMAL_RESUME
    if snapshot_ok and viability >= 0.55:
        state.recovery_locked = False
        return AwakeningBranch.VERIFIED_RESTORE
    state.recovery_locked = True
    return AwakeningBranch.PARTIAL_HOLD

def handle_fault(state: RuntimeState, fault: FaultEvent, snapshot: Snapshot | None = None, external_threat: float = 0.0) -> AwakeningBranch:
    severity = _unit(fault.severity, "fault severity")
    weights = {FaultType.STORAGE_IO: ("resource_health", 0.30), FaultType.ARTIFACT_INTEGRITY: ("artifact_integrity", 0.45),
               FaultType.RESOURCE_PRESSURE: ("resource_health", 0.45), FaultType.EXECUTION_INTERRUPTION: ("execution_health", 0.50)}
    if not isinstance(fault.fault_type, FaultType):
        raise ClifeError("unknown fault type")
    field, weight = weights[fault.fault_type]
    setattr(state, field, max(0.0, _unit(getattr(state, field), field) - severity * weight))
    branch = branch_awakening(state, snapshot, external_threat)
    fault.mitigated = branch in (AwakeningBranch.NORMAL_RESUME, AwakeningBranch.VERIFIED_RESTORE)
    return branch

def transition_steps(current: float, target: float, max_steps: int = 32) -> tuple[float, ...]:
    """Finite interpolation; never loops on a floating-point threshold."""
    if isinstance(max_steps, bool) or not isinstance(max_steps, int) or not 1 <= max_steps <= 256:
        raise ClifeError("max_steps must be an integer in 1..256")
    if not math.isfinite(current) or not math.isfinite(target):
        raise ClifeError("transition endpoints must be finite")
    return tuple(current + (target - current) * (index / max_steps) for index in range(1, max_steps + 1))

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="CLife bounded project checkpoint and recovery tools.")
    commands = parser.add_subparsers(dest="action", required=True)
    capture = commands.add_parser("capture", help="capture a project file as a verified checkpoint")
    capture.add_argument("source", type=Path); capture.add_argument("destination", type=Path)
    capture.add_argument("--project-id", required=True); capture.add_argument("--generation", type=int, required=True)
    verify = commands.add_parser("verify", help="verify without executing the payload"); verify.add_argument("checkpoint", type=Path)
    restore = commands.add_parser("restore", help="export checkpoint bytes to a new file")
    restore.add_argument("checkpoint", type=Path); restore.add_argument("destination", type=Path); restore.add_argument("--project-id", required=True)
    args = parser.parse_args(argv)
    try:
        if args.action == "capture":
            if args.source.stat().st_size > MAX_PAYLOAD_BYTES: raise ClifeError("source file exceeds the 64 MiB limit")
            snap = Snapshot.capture(args.project_id, args.generation, args.source.read_bytes())
            save_snapshot(snap, args.destination)
            print(json.dumps({"status": "captured", "project_id": snap.project_id, "generation": snap.generation, "checksum": snap.checksum_sha256}))
        elif args.action == "verify":
            snap = load_snapshot(args.checkpoint)
            print(json.dumps({"status": "verified", "project_id": snap.project_id, "generation": snap.generation, "bytes": len(snap.payload)}))
        else:
            snap = load_snapshot(args.checkpoint); payload = restore_snapshot(snap, args.project_id)
            args.destination.parent.mkdir(parents=True, exist_ok=True); args.destination.write_bytes(payload)
            print(json.dumps({"status": "exported", "destination": str(args.destination), "bytes": len(payload)}))
        return 0
    except (ClifeError, OSError) as exc:
        parser.exit(2, f"reaper-clife: {exc}\n")
    return 2

if __name__ == "__main__":
    raise SystemExit(main())
