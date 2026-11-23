"""Typed results and explicit request context for Reaper programs.

The helpers are synchronous and deterministic. They do not create threads,
perform I/O, read a clock, or hide exceptions from unexpected host failures.
"""
from __future__ import annotations

import copy
import json
import re
from dataclasses import dataclass
from typing import Any, Callable

from .errors import ReaperRuntimeError


_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_ERROR_CODE = re.compile(r"^[A-Z][A-Z0-9_.-]{1,63}$")
_MAX_CONTEXT_BYTES = 16 * 1024
_MAX_ERROR_DETAILS_BYTES = 16 * 1024


class ResultContractError(ValueError):
    """An invalid Result, error envelope, or request context was supplied."""


def _canonical_json(value: Any, limit: int, label: str) -> str:
    try:
        rendered = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError, RecursionError) as error:
        raise ResultContractError(f"{label} must be finite JSON-compatible data: {error}") from error
    if len(rendered.encode("utf-8")) > limit:
        raise ResultContractError(f"{label} exceeds the {limit}-byte limit")
    return rendered


def _identifier(value: Any, label: str) -> str:
    if not isinstance(value, str) or not _IDENTIFIER.fullmatch(value):
        raise ResultContractError(
            f"{label} must be 1..128 characters using letters, digits, '.', '_', ':' or '-'"
        )
    return value


@dataclass(frozen=True, slots=True)
class RequestContext:
    """Explicit correlation metadata passed as a normal program value."""

    request_id: str
    trace_id: str
    parent_id: str | None
    _metadata_json: str = "{}"

    @property
    def metadata(self) -> dict[str, Any]:
        return json.loads(self._metadata_json)

    def as_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "trace_id": self.trace_id,
            "parent_id": self.parent_id,
            "metadata": self.metadata,
        }


@dataclass(frozen=True, slots=True)
class ErrorValue:
    code: str
    message: str
    _details_json: str = "{}"

    @property
    def details(self) -> dict[str, Any]:
        return json.loads(self._details_json)

    def as_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details,
        }


@dataclass(frozen=True, slots=True)
class ResultValue:
    """A success or failure value; failure never masquerades as a success payload."""

    succeeded: bool
    value: Any = None
    error: ErrorValue | None = None
    context: RequestContext | None = None

    def __post_init__(self) -> None:
        if self.succeeded and self.error is not None:
            raise ResultContractError("a successful Result cannot contain an error")
        if not self.succeeded and self.error is None:
            raise ResultContractError("a failed Result must contain an error")


def request_context(
    request_id: Any,
    trace_id: Any = None,
    parent_id: Any = None,
    metadata: Any = None,
) -> RequestContext:
    """Create bounded explicit correlation context without generating hidden IDs."""
    request = _identifier(request_id, "request_id")
    trace = _identifier(trace_id if trace_id is not None else request, "trace_id")
    parent = None if parent_id is None else _identifier(parent_id, "parent_id")
    details = {} if metadata is None else metadata
    if not isinstance(details, dict) or any(not isinstance(key, str) for key in details):
        raise ResultContractError("context metadata must be a map with text keys")
    encoded = _canonical_json(details, _MAX_CONTEXT_BYTES, "context metadata")
    return RequestContext(request, trace, parent, encoded)


def context_with(context: Any, key: Any, value: Any) -> RequestContext:
    if not isinstance(context, RequestContext):
        raise TypeError("context_with expects a RequestContext")
    if not isinstance(key, str) or not key or len(key) > 128:
        raise ResultContractError("context metadata key must contain 1..128 characters")
    metadata = context.metadata
    metadata[key] = copy.deepcopy(value)
    encoded = _canonical_json(metadata, _MAX_CONTEXT_BYTES, "context metadata")
    return RequestContext(
        context.request_id, context.trace_id, context.parent_id, encoded
    )


def context_get(context: Any, key: Any) -> Any:
    if not isinstance(context, RequestContext):
        raise TypeError("context_get expects a RequestContext")
    if not isinstance(key, str):
        raise TypeError("context_get key must be text")
    if key == "request_id":
        return context.request_id
    if key == "trace_id":
        return context.trace_id
    if key == "parent_id":
        return context.parent_id
    return copy.deepcopy(context.metadata.get(key))


def _context(value: Any) -> RequestContext | None:
    if value is None:
        return None
    if not isinstance(value, RequestContext):
        raise TypeError("result context must be a RequestContext or nothing")
    return value


def ok(value: Any, context: Any = None) -> ResultValue:
    return ResultValue(True, value=value, context=_context(context))


def err(code: Any, message: Any, details: Any = None, context: Any = None) -> ResultValue:
    if not isinstance(code, str) or not _ERROR_CODE.fullmatch(code):
        raise ResultContractError("error code must be an uppercase stable identifier")
    if not isinstance(message, str) or not message.strip() or len(message) > 2048:
        raise ResultContractError("error message must contain 1..2048 characters")
    payload = {} if details is None else details
    if not isinstance(payload, dict) or any(not isinstance(key, str) for key in payload):
        raise ResultContractError("error details must be a map with text keys")
    encoded = _canonical_json(payload, _MAX_ERROR_DETAILS_BYTES, "error details")
    return ResultValue(
        False,
        error=ErrorValue(code, message.strip(), encoded),
        context=_context(context),
    )


def _result(value: Any) -> ResultValue:
    if not isinstance(value, ResultValue):
        raise TypeError("expected a Result value created by ok() or err()")
    return value


def is_ok(value: Any) -> bool:
    return _result(value).succeeded


def is_err(value: Any) -> bool:
    return not _result(value).succeeded


def result_value(value: Any) -> Any:
    result = _result(value)
    if not result.succeeded:
        assert result.error is not None
        raise ValueError(f"{result.error.code}: {result.error.message}")
    return result.value


def result_error(value: Any) -> dict[str, Any] | None:
    result = _result(value)
    return None if result.succeeded else result.error.as_dict()


def result_context(value: Any) -> RequestContext | None:
    return _result(value).context


def _carry_context(result: ResultValue, context: RequestContext | None) -> ResultValue:
    if result.context is not None or context is None:
        return result
    return ResultValue(result.succeeded, result.value, result.error, context)


def result_map(value: Any, transform: Any, invoke: Callable[[Any, list[Any]], Any]) -> ResultValue:
    result = _result(value)
    if not result.succeeded:
        return result
    return ok(invoke(transform, [result.value]), result.context)


def result_and_then(
    value: Any, transform: Any, invoke: Callable[[Any, list[Any]], Any]
) -> ResultValue:
    result = _result(value)
    if not result.succeeded:
        return result
    return _carry_context(_result(invoke(transform, [result.value])), result.context)


def result_recover(
    value: Any, recover: Any, invoke: Callable[[Any, list[Any]], Any]
) -> ResultValue:
    result = _result(value)
    if result.succeeded:
        return result
    assert result.error is not None
    return _carry_context(_result(invoke(recover, [result.error.as_dict()])), result.context)


def context_to_map(context: Any) -> dict[str, Any]:
    if not isinstance(context, RequestContext):
        raise TypeError("context_to_map expects a RequestContext")
    return context.as_dict()


def result_or(value: Any, fallback: Any) -> Any:
    result = _result(value)
    return result.value if result.succeeded else fallback
