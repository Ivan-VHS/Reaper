"""Bounded typed channels and a structured single-process actor supervisor."""
from __future__ import annotations

import asyncio
import inspect
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Callable


class ChannelClosed(RuntimeError):
    pass


class ActorError(RuntimeError):
    pass


class TypedChannel:
    """An MPMC channel with runtime type checks, bounded capacity and backpressure."""

    def __init__(self, message_type: type | tuple[type, ...], capacity: int = 64) -> None:
        if capacity < 1:
            raise ValueError("channel capacity must be positive")
        if not isinstance(message_type, (type, tuple)):
            raise TypeError("message_type must be a type or tuple of types")
        self.message_type = message_type
        self.capacity = capacity
        self._items: deque[Any] = deque()
        self._closed = False
        self._condition = asyncio.Condition()

    async def send(self, message: Any) -> None:
        if not isinstance(message, self.message_type):
            expected = getattr(self.message_type, "__name__", repr(self.message_type))
            raise TypeError(f"channel expects {expected}, got {type(message).__name__}")
        async with self._condition:
            while len(self._items) >= self.capacity and not self._closed:
                await self._condition.wait()
            if self._closed:
                raise ChannelClosed("cannot send to a closed channel")
            self._items.append(message)
            self._condition.notify_all()

    async def receive(self) -> Any:
        async with self._condition:
            while not self._items and not self._closed:
                await self._condition.wait()
            if not self._items:
                raise ChannelClosed("channel is closed and empty")
            message = self._items.popleft()
            self._condition.notify_all()
            return message

    async def close(self) -> None:
        async with self._condition:
            self._closed = True
            self._condition.notify_all()

    @property
    def closed(self) -> bool:
        return self._closed


@dataclass(slots=True)
class _Actor:
    name: str
    factory: Callable[[], Callable[[Any], Any]]
    channel: TypedChannel
    max_restarts: int
    task: asyncio.Task[None] | None = None
    restarts: int = 0
    failures: list[str] = field(default_factory=list)
    failure: str | None = None


class ActorRef:
    def __init__(self, actor: _Actor) -> None:
        self._actor = actor

    async def tell(self, message: Any) -> None:
        if self._actor.failure is not None:
            raise ActorError(f"actor '{self._actor.name}' failed: {self._actor.failure}")
        await self._actor.channel.send(message)

    async def stop(self) -> None:
        await self._actor.channel.close()
        if self._actor.task is not None:
            await self._actor.task

    async def wait(self) -> None:
        if self._actor.task is not None:
            await self._actor.task

    @property
    def failures(self) -> tuple[str, ...]:
        return tuple(self._actor.failures)

    @property
    def restarts(self) -> int:
        return self._actor.restarts

    @property
    def failed(self) -> bool:
        return self._actor.failure is not None


class ActorSystem:
    """Owns all child actor tasks; leaving the scope closes and joins them."""

    def __init__(self) -> None:
        self._actors: dict[str, _Actor] = {}
        self._closed = False

    async def __aenter__(self) -> "ActorSystem":
        if self._closed:
            raise ActorError("actor system has been closed")
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        await self.close()
    
    async def spawn(
        self,
        name: str,
        handler_factory: Callable[[], Callable[[Any], Any]],
        message_type: type | tuple[type, ...],
        *,
        mailbox_capacity: int = 64,
        max_restarts: int = 0,
    ) -> ActorRef:
        if self._closed:
            raise ActorError("actor system has been closed")
        if not name or name in self._actors:
            raise ActorError("actor name must be non-empty and unique")
        if not callable(handler_factory):
            raise TypeError("handler_factory must be callable")
        if max_restarts < 0:
            raise ValueError("max_restarts cannot be negative")
        actor = _Actor(name, handler_factory, TypedChannel(message_type, mailbox_capacity), max_restarts)
        self._actors[name] = actor
        actor.task = asyncio.create_task(self._serve(actor), name=f"reaper-actor:{name}")
        return ActorRef(actor)

    async def _serve(self, actor: _Actor) -> None:
        try:
            handler = actor.factory()
            if not callable(handler):
                raise TypeError("handler_factory must return a callable")
            while True:
                try:
                    message = await actor.channel.receive()
                except ChannelClosed:
                    return
                try:
                    result = handler(message)
                    if inspect.isawaitable(result):
                        await result
                except Exception as error:
                    actor.failures.append(f"{type(error).__name__}: {error}")
                    if actor.restarts >= actor.max_restarts:
                        actor.failure = actor.failures[-1]
                        await actor.channel.close()
                        return
                    actor.restarts += 1
                    handler = actor.factory()
                    if not callable(handler):
                        raise TypeError("handler_factory must return a callable")
        except asyncio.CancelledError:
            raise
        except Exception as error:
            actor.failure = f"{type(error).__name__}: {error}"
            await actor.channel.close()

    async def close(self, timeout: float = 2.0) -> None:
        if self._closed:
            return
        self._closed = True
        actors = tuple(self._actors.values())
        for actor in actors:
            await actor.channel.close()
        tasks = [actor.task for actor in actors if actor.task is not None]
        if tasks:
            done, pending = await asyncio.wait(tasks, timeout=timeout)
            for task in pending:
                task.cancel()
            if pending:
                await asyncio.gather(*pending, return_exceptions=True)

    def status(self) -> tuple[dict[str, Any], ...]:
        return tuple({
            "name": actor.name,
            "restarts": actor.restarts,
            "failures": tuple(actor.failures),
            "failed": actor.failure is not None,
            "done": actor.task.done() if actor.task is not None else True,
        } for actor in self._actors.values())
