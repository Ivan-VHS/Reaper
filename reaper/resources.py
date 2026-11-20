"""Deterministic ownership for files and external runtime resources."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TextIO


@dataclass(frozen=True, slots=True)
class ResourceHandle:
    manager_id: int
    resource_id: int


class ResourceError(RuntimeError):
    pass


class ResourceManager:
    def __init__(self, max_open: int = 64) -> None:
        self.max_open = max_open
        self._manager_id = id(self)
        self._next_id = 1
        self._files: dict[int, tuple[TextIO, str]] = {}

    def open_text(self, path: str, mode: str = "r", base_dir: str | Path | None = None) -> ResourceHandle:
        if mode not in {"r", "w", "a", "x"}:
            raise ResourceError("file mode must be one of: r, w, a, x")
        if len(self._files) >= self.max_open:
            raise ResourceError(f"open resource limit ({self.max_open}) exceeded")
        target = Path(path)
        if not target.is_absolute() and base_dir is not None:
            target = Path(base_dir) / target
        target = target.resolve()
        try:
            stream = target.open(mode, encoding="utf-8", newline="")
        except OSError as error:
            raise ResourceError(f"cannot open {target}: {error}") from error
        resource_id = self._next_id
        self._next_id += 1
        self._files[resource_id] = (stream, mode)
        return ResourceHandle(self._manager_id, resource_id)

    def _get(self, handle: ResourceHandle, operation: str) -> tuple[TextIO, str]:
        if not isinstance(handle, ResourceHandle) or handle.manager_id != self._manager_id:
            raise ResourceError("invalid or foreign resource handle")
        try:
            stream, mode = self._files[handle.resource_id]
        except KeyError as error:
            raise ResourceError("resource is already closed or unknown") from error
        if operation == "read" and mode not in {"r"}:
            raise ResourceError("resource is not open for reading")
        if operation == "write" and mode not in {"w", "a", "x"}:
            raise ResourceError("resource is not open for writing")
        return stream, mode

    def read(self, handle: ResourceHandle) -> str:
        stream, _ = self._get(handle, "read")
        try:
            return stream.read()
        except OSError as error:
            raise ResourceError(f"file read failed: {error}") from error

    def write(self, handle: ResourceHandle, value: str) -> int:
        stream, _ = self._get(handle, "write")
        if not isinstance(value, str):
            raise ResourceError("file_write expects text")
        try:
            return stream.write(value)
        except OSError as error:
            raise ResourceError(f"file write failed: {error}") from error

    def close(self, handle: ResourceHandle) -> None:
        stream, _ = self._get(handle, "close")
        try:
            stream.close()
        finally:
            self._files.pop(handle.resource_id, None)

    def close_all(self) -> list[str]:
        failures: list[str] = []
        for resource_id, (stream, _mode) in list(self._files.items()):
            try:
                stream.close()
            except OSError as error:
                failures.append(str(error))
            finally:
                self._files.pop(resource_id, None)
        return failures

    def stats(self) -> dict[str, int]:
        return {"open_files": len(self._files), "limit": self.max_open}
