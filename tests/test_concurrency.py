from __future__ import annotations

import asyncio
import unittest

from reaper.concurrency import ActorError, ActorSystem, ChannelClosed, TypedChannel


class ConcurrencyTests(unittest.IsolatedAsyncioTestCase):
    async def test_typed_channel_enforces_type_and_close(self) -> None:
        channel = TypedChannel(int, capacity=1)
        await channel.send(5)
        with self.assertRaises(TypeError):
            await channel.send("wrong")
        self.assertEqual(await channel.receive(), 5)
        await channel.close()
        with self.assertRaises(ChannelClosed):
            await channel.receive()

    async def test_channel_backpressure_resumes_after_receive(self) -> None:
        channel = TypedChannel(str, capacity=1)
        await channel.send("first")
        sender = asyncio.create_task(channel.send("second"))
        await asyncio.sleep(0)
        self.assertFalse(sender.done())
        self.assertEqual(await channel.receive(), "first")
        await sender
        self.assertEqual(await channel.receive(), "second")

    async def test_actor_processes_messages_and_scope_joins_children(self) -> None:
        seen: list[int] = []
        async with ActorSystem() as system:
            actor = await system.spawn(
                "counter",
                lambda: (lambda value: seen.append(value)),
                int,
                mailbox_capacity=4,
            )
            await actor.tell(3)
            await actor.tell(8)
            await actor.stop()
            self.assertEqual(seen, [3, 8])
        self.assertTrue(system.status()[0]["done"])

    async def test_actor_supervision_rebuilds_handler_after_failure(self) -> None:
        seen: list[int] = []
        created = 0

        def factory():
            nonlocal created
            created += 1
            def handler(value: int) -> None:
                if value == 0:
                    raise ValueError("transient")
                seen.append(value)
            return handler

        async with ActorSystem() as system:
            actor = await system.spawn("worker", factory, int, max_restarts=1)
            await actor.tell(0)
            await actor.tell(7)
            await actor.stop()
            self.assertEqual(actor.restarts, 1)
            self.assertEqual(len(actor.failures), 1)
            self.assertEqual(seen, [7])
            self.assertEqual(created, 2)

    async def test_actor_rejects_duplicate_names(self) -> None:
        async with ActorSystem() as system:
            await system.spawn("one", lambda: (lambda _message: None), str)
            with self.assertRaises(ActorError):
                await system.spawn("one", lambda: (lambda _message: None), str)


if __name__ == "__main__":
    unittest.main()
