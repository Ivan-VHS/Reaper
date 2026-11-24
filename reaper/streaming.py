"""Typed result values and bounded, fused single-pass streams for Reaper.

The stream adapter is deliberately single-use. map/filter append stages to one
shared source state; iter_fused executes every stage in one source loop without
building intermediate lists.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

T = TypeVar("T")
E = TypeVar("E")


@dataclass(frozen=True, slots=True)
class ResultValue(Generic[T, E]):
    """Runtime representation of Result<T, E>.

    The generic parameters document the host-side contract. Reaper's current
    reference interpreter does not yet perform compile-time generic checking.
    """

    _success: bool
    _payload: Any

    @classmethod
    def ok(cls, value: T) -> "ResultValue[T, E]":
        return cls(True, value)

    @classmethod
    def err(cls, error: E) -> "ResultValue[T, E]":
        return cls(False, error)

    @property
    def is_ok(self) -> bool:
        return self._success

    @property
    def is_err(self) -> bool:
        return not self._success

    @property
    def value(self) -> T:
        if not self._success:
            raise ValueError("cannot read value from an Err result")
        return self._payload

    @property
    def error(self) -> E:
        if self._success:
            raise ValueError("cannot read error from an Ok result")
        return self._payload


@dataclass(slots=True)
class _StreamState:
    iterator: Iterator[Any]
    max_items: int
    on_step: Callable[[], None] | None
    consumed: bool = False
    closed: bool = False
    source_items: int = 0


class StreamValue:
    """A bounded, single-use stream with an interpreter-fused transform plan."""

    __slots__ = ("_state", "_stages")

    def __init__(
        self,
        source: Iterable[Any],
        *,
        max_items: int,
        on_step: Callable[[], None] | None = None,
        _state: _StreamState | None = None,
        _stages: tuple[tuple[str, Callable[[Any], Any]], ...] = (),
    ) -> None:
        if _state is not None:
            self._state = _state
            self._stages = _stages
            return

        if isinstance(source, dict):
            raise TypeError("stream() does not accept a map; stream its values explicitly")
        if isinstance(source, (bytes, bytearray)):
            raise TypeError("stream() expects an iterable of Reaper values, not bytes")
        try:
            iterator = iter(source)
        except TypeError as error:
            raise TypeError("stream() expects an iterable value") from error

        try:
            source_size = len(source)  # type: ignore[arg-type]
        except (TypeError, OverflowError):
            source_size = None
        if source_size is not None and source_size > max_items:
            raise ValueError(f"stream item limit ({max_items}) exceeded")

        self._state = _StreamState(
            iterator=iterator,
            max_items=max_items,
            on_step=on_step,
        )
        self._stages = _stages

    def map(self, function: Callable[[Any], Any]) -> "StreamValue":
        if not callable(function):
            raise TypeError("stream map stage must be callable")
        return StreamValue(
            (),
            max_items=self._state.max_items,
            _state=self._state,
            _stages=(*self._stages, ("map", function)),
        )

    def filter(self, predicate: Callable[[Any], Any]) -> "StreamValue":
        if not callable(predicate):
            raise TypeError("stream filter stage must be callable")
        return StreamValue(
            (),
            max_items=self._state.max_items,
            _state=self._state,
            _stages=(*self._stages, ("filter", predicate)),
        )

    def iter_fused(self) -> Iterator[Any]:
        state = self._state
        if state.closed:
            raise ValueError("stream is closed")
        if state.consumed:
            raise ValueError("stream has already been consumed")

        state.consumed = True
        try:
            for source_value in state.iterator:
                state.source_items += 1
                if state.source_items > state.max_items:
                    raise ValueError(f"stream item limit ({state.max_items}) exceeded")
                if state.on_step is not None:
                    state.on_step()

                value = source_value
                accepted = True
                for stage_kind, function in self._stages:
                    if stage_kind == "map":
                        value = function(value)
                    elif stage_kind == "filter":
                        if not function(value):
                            accepted = False
                            break
                    else:  # Defensive guard against an invalid internal plan.
                        raise RuntimeError(f"unknown stream stage: {stage_kind}")

                if accepted:
                    yield value
        finally:
            self.close()

    def close(self) -> None:
        if self._state.closed:
            return
        self._state.closed = True
        close = getattr(self._state.iterator, "close", None)
        if callable(close):
            close()

    @property
    def consumed(self) -> bool:
        return self._state.consumed

    @property
    def source_items(self) -> int:
        return self._state.source_items

    @property
    def stage_count(self) -> int:
        return len(self._stages)

    def __iter__(self) -> Iterator[Any]:
        return self.iter_fused()

    def __repr__(self) -> str:
        status = "consumed" if self.consumed else "ready"
        return f"Stream<{status}, stages={len(self._stages)}>"
