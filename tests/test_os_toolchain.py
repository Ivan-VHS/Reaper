from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from reaper.os_toolchain import (
    PROJECT_SCHEMA,
    ProjectError,
    build_plan,
    load_project,
    validate_project_files,
)


class FreestandingToolchainTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        (self.root / "src").mkdir()
        (self.root / "include").mkdir()
        (self.root / "src" / "boot.c").write_text(
            "void _start(void) { for (;;) {} }\n", encoding="utf-8"
        )
        (self.root / "linker.ld").write_text(
            "ENTRY(_start)\nSECTIONS { . = 1M; .text : { *(.text*) } }\n",
            encoding="utf-8",
        )
        self.manifest = self.root / "reaper-os.json"
        self.data = {
            "schema": PROJECT_SCHEMA,
            "name": "test-kernel",
            "target": "x86_64-unknown-none-elf",
            "format": "elf",
            "entry": "_start",
            "output": "build/kernel.elf",
            "sources": ["src/boot.c"],
            "include_dirs": ["include"],
            "linker_script": "linker.ld",
        }

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write_manifest(self) -> None:
        self.manifest.write_text(
            json.dumps(self.data, indent=2), encoding="utf-8"
        )

    def test_manifest_and_relative_paths_are_validated(self) -> None:
        self.write_manifest()
        project = load_project(self.manifest)
        validate_project_files(project)
        self.assertEqual(project.target, "x86_64-unknown-none-elf")
        self.assertEqual(project.sources, ((self.root / "src" / "boot.c").resolve(),))

    def test_unknown_manifest_fields_are_rejected(self) -> None:
        self.data["mystery_switch"] = True
        self.write_manifest()
        with self.assertRaisesRegex(ProjectError, "unknown project field"):
            load_project(self.manifest)

    def test_unsupported_target_is_rejected(self) -> None:
        self.data["target"] = "armv7-unknown-none"
        self.write_manifest()
        with self.assertRaisesRegex(ProjectError, "unsupported target"):
            load_project(self.manifest)

    def test_non_elf_output_is_not_claimed(self) -> None:
        self.data["format"] = "pe"
        self.write_manifest()
        with self.assertRaisesRegex(ProjectError, "currently supports"):
            load_project(self.manifest)

    def test_build_plan_is_freestanding_and_has_no_hosted_runtime(self) -> None:
        self.write_manifest()
        project = load_project(self.manifest)
        commands = build_plan(project)
        self.assertEqual(len(commands), 2)
        compile_command, link_command = commands
        self.assertIn("-ffreestanding", compile_command)
        self.assertIn("-fno-builtin", compile_command)
        self.assertIn("-mno-red-zone", compile_command)
        self.assertIn("-nostdlib", link_command)
        self.assertIn("-static", link_command)
        self.assertIn("-fuse-ld=lld", link_command)
        self.assertFalse(any("libc" in item for item in link_command))

    def test_aarch64_does_not_receive_x86_red_zone_flag(self) -> None:
        self.data["target"] = "aarch64-unknown-none-elf"
        self.write_manifest()
        project = load_project(self.manifest)
        command = build_plan(project)[0]
        self.assertNotIn("-mno-red-zone", command)

    def test_missing_source_is_reported(self) -> None:
        self.data["sources"] = ["src/missing.c"]
        self.write_manifest()
        project = load_project(self.manifest)
        with self.assertRaisesRegex(ProjectError, "not found"):
            validate_project_files(project)


if __name__ == "__main__":
    unittest.main()
