from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from reaper.clife import (
    CLifeError,
    RepositoryNetwork,
    ReflashPlan,
    apply_reflash_plan,
    create_checkpoint,
    plan_reflash,
    restore_checkpoint,
    verify_checkpoint,
)


class CLifeCheckpointTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / "project"
        self.root.mkdir()
        (self.root / "src").mkdir()
        (self.root / "src" / "main.py").write_text("value = 1\n", encoding="utf-8")
        (self.root / "README.md").write_text("project\n", encoding="utf-8")
        (self.root / ".git").mkdir()
        (self.root / ".git" / "private-index").write_text("excluded\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_checkpoint_verify_and_restore_to_new_directory(self) -> None:
        checkpoint = create_checkpoint(self.root)
        verification = verify_checkpoint(checkpoint.path)

        self.assertTrue(verification.valid, verification.errors)
        self.assertEqual(verification.files, 2)
        (self.root / "src" / "main.py").write_text("value = 99\n", encoding="utf-8")

        restored = restore_checkpoint(
            checkpoint.path, Path(self.temporary.name) / "recovered" / "project"
        )
        self.assertEqual(
            (restored / "src" / "main.py").read_text(encoding="utf-8"), "value = 1\n"
        )
        self.assertFalse((restored / ".git").exists())

    def test_checkpoint_detects_modified_content(self) -> None:
        checkpoint = create_checkpoint(self.root)
        snapshot_file = Path(checkpoint.path) / "files" / "README.md"
        snapshot_file.write_text("tampered\n", encoding="utf-8")

        verification = verify_checkpoint(checkpoint.path)
        self.assertFalse(verification.valid)
        self.assertTrue(any("verification failed" in item for item in verification.errors))

    def test_restore_refuses_to_overwrite_nonempty_destination(self) -> None:
        checkpoint = create_checkpoint(self.root)
        destination = Path(self.temporary.name) / "existing"
        destination.mkdir()
        (destination / "keep.txt").write_text("keep\n", encoding="utf-8")

        with self.assertRaises(CLifeError):
            restore_checkpoint(checkpoint.path, destination)
        self.assertEqual((destination / "keep.txt").read_text(encoding="utf-8"), "keep\n")


class CLifeReflashTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / "project"
        self.root.mkdir()
        (self.root / "app.rpr").write_text('emit "old"\n', encoding="utf-8")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_plan_is_non_mutating_and_apply_creates_rollback_point(self) -> None:
        plan = plan_reflash(self.root, {
            "app.rpr": 'emit "new"\n',
            "config/settings.json": '{"enabled": true}\n',
        })
        self.assertEqual(
            (self.root / "app.rpr").read_text(encoding="utf-8"), 'emit "old"\n'
        )

        decoded = ReflashPlan.from_json(plan.to_json())
        result = apply_reflash_plan(self.root, decoded)

        self.assertEqual((self.root / "app.rpr").read_text(encoding="utf-8"), 'emit "new"\n')
        self.assertEqual(
            (self.root / "config" / "settings.json").read_text(encoding="utf-8"),
            '{"enabled": true}\n',
        )
        self.assertTrue(verify_checkpoint(result.checkpoint).valid)

        rollback = Path(self.temporary.name) / "rollback-copy"
        restore_checkpoint(result.checkpoint, rollback)
        self.assertEqual((rollback / "app.rpr").read_text(encoding="utf-8"), 'emit "old"\n')
        self.assertFalse((rollback / "config" / "settings.json").exists())

    def test_stale_plan_is_rejected_before_any_change(self) -> None:
        plan = plan_reflash(self.root, {"app.rpr": 'emit "planned"\n'})
        (self.root / "app.rpr").write_text('emit "concurrent"\n', encoding="utf-8")

        with self.assertRaisesRegex(CLifeError, "stale reflash plan"):
            apply_reflash_plan(self.root, plan)
        self.assertEqual(
            (self.root / "app.rpr").read_text(encoding="utf-8"), 'emit "concurrent"\n'
        )

    def test_path_traversal_is_rejected(self) -> None:
        with self.assertRaises(CLifeError):
            plan_reflash(self.root, {"../outside.txt": "nope"})

    def test_case_insensitive_path_collision_is_rejected(self) -> None:
        with self.assertRaisesRegex(CLifeError, "colliding reflash path"):
            plan_reflash(self.root, {"Config.json": "one", "config.json": "two"})

    def test_plan_rejects_tampered_embedded_content(self) -> None:
        payload = json.loads(plan_reflash(self.root, {"app.rpr": "next"}).to_json())
        payload["changes"][0]["content_base64"] = "bm90LXRoZS1wbGFubmVkLWNvbnRlbnQ="
        with self.assertRaisesRegex(CLifeError, "content size or checksum is invalid"):
            ReflashPlan.from_json(json.dumps(payload))


class CLifeNetworkTests(unittest.TestCase):
    def test_selected_file_propagation_is_a_reviewable_plan(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "source"
            destination = Path(temporary) / "destination"
            source.mkdir()
            destination.mkdir()
            (source / "shared.rpr").write_text('emit "source"\n', encoding="utf-8")
            (destination / "shared.rpr").write_text('emit "destination"\n', encoding="utf-8")

            network = RepositoryNetwork()
            network.register("source", source)
            network.register("destination", destination)
            plan = network.plan_propagation("source", "destination", ["shared.rpr"])

            self.assertEqual(
                (destination / "shared.rpr").read_text(encoding="utf-8"),
                'emit "destination"\n',
            )
            result = apply_reflash_plan(destination, plan)
            self.assertEqual(
                (destination / "shared.rpr").read_text(encoding="utf-8"),
                'emit "source"\n',
            )
            self.assertEqual(result.changed_paths, ("shared.rpr",))
            statuses = {
                item["name"]: item["changed_since_registration"]
                for item in network.audit_all()["repositories"]
            }
            self.assertTrue(statuses["destination"])
            self.assertFalse(statuses["source"])


if __name__ == "__main__":
    unittest.main()
