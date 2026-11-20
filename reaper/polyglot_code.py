"""Programming-language immersion and engineering fluency toolkit.

This module is deliberately separate from :mod:`reaper.polyglot`, which
supports natural-language learning. It stores programming-language profiles,
concept mastery, cross-language mental models, katas, idioms, error journals
and practice sessions locally. It never downloads toolchains or executes
learner code.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
LEVELS = ("novice", "working", "proficient", "advanced")
TOPIC_STATUSES = ("unseen", "in_progress", "understood", "idiomatic")
SESSION_MODES = ("study", "reading", "coding", "testing", "refactoring",
                 "debugging", "project", "review")

FAMILIES = (
    "manual-memory", "ownership", "garbage-collected", "managed-runtime",
    "dynamic", "functional", "multi-paradigm",
)

STAGES: tuple[dict[str, Any], ...] = (
    {
        "id": 0, "name": "Environment and toolchain", "duration": "1–2 days",
        "goal": "Make the feedback loop fast, repeatable and observable.",
        "tasks": (
            "Install the official compiler/runtime and a version manager where appropriate.",
            "Identify the package manager, build command, formatter, linter and test runner.",
            "Configure editor support, language server, debugger and a clean scratch project.",
            "Record exact tool versions and a reproducible minimal build/test command.",
        ),
    },
    {
        "id": 1, "name": "Language skeleton", "duration": "1–2 weeks",
        "goal": "Write small programs without repeatedly translating syntax from another language.",
        "tasks": (
            "Practise values, bindings, primitive types, conversions and mutability.",
            "Implement conditions, loops, functions, methods, closures and scope rules.",
            "Use the language's core collections, strings, tuples, records and enums.",
            "Split code into modules; understand imports, visibility and package boundaries.",
            "Read compiler/interpreter diagnostics and fix deliberately introduced mistakes.",
        ),
    },
    {
        "id": 2, "name": "Semantics and execution model", "duration": "2–3 weeks",
        "goal": "Understand what the runtime and type system actually guarantee and cost.",
        "tasks": (
            "Map static/dynamic typing, inference, generics, interfaces/traits and sum types.",
            "Trace stack, heap, copying, references, ownership, lifetimes or garbage collection.",
            "Compare exceptions, result values, error codes, panics and recovery boundaries.",
            "Build a small concurrency example; identify races, blocking and cancellation rules.",
            "Write down the execution model in your own words and test its edge cases.",
        ),
    },
    {
        "id": 3, "name": "Standard library and mini-projects", "duration": "2–3 weeks",
        "goal": "Solve useful problems with the language's own primitives before adding frameworks.",
        "tasks": (
            "Build a CLI that validates arguments and reads/writes files.",
            "Build a JSON/CSV/config transformer with explicit validation and useful errors.",
            "Build a small network or data-processing component where the standard library allows it.",
            "Write tests for empty input, malformed data, boundaries and failure paths.",
            "Add third-party dependencies only when they solve a concrete gap.",
        ),
    },
    {
        "id": 4, "name": "Idioms, testing and code reading", "duration": "2–3+ months",
        "goal": "Make solutions natural, maintainable and recognisable to experienced users of the language.",
        "tasks": (
            "Read official examples and small, maintained libraries written by language experts.",
            "Learn the standard test style, fixtures, integration tests and benchmark conventions.",
            "Capture idioms with a concrete example and the non-idiomatic alternative.",
            "Refactor early exercises using native abstractions and error-handling conventions.",
            "Keep a journal of compiler diagnostics, runtime surprises and their root causes.",
        ),
    },
    {
        "id": 5, "name": "Architecture and production fluency", "duration": "3–6+ months",
        "goal": "Make deliberate design choices based on constraints, workload and ecosystem.",
        "tasks": (
            "Profile representative workloads before optimising; identify allocation and I/O costs.",
            "Evaluate abstraction cost, binary/runtime footprint and deployment constraints.",
            "Design module/API boundaries and compatibility policies for real consumers.",
            "Review security, resource limits, observability and operational failure modes.",
            "Deliver and maintain a non-trivial project with documentation and reproducible tests.",
        ),
    },
)

CONCEPTS: tuple[dict[str, Any], ...] = (
    {"key": "toolchain", "title": "Toolchain and feedback loop", "stage": 0,
     "question": "Can you build, format, lint, test and debug a minimal project from the CLI?"},
    {"key": "syntax", "title": "Core syntax and values", "stage": 1,
     "question": "Can you express common control flow and data transformations without a syntax lookup?"},
    {"key": "functions-scope", "title": "Functions, scope and closures", "stage": 1,
     "question": "Do you understand parameter passing, captures, visibility and lifetime of locals?"},
    {"key": "types", "title": "Type system", "stage": 2,
     "question": "Can you explain inference, generics, interfaces/traits, nullability and sum types?"},
    {"key": "execution", "title": "Execution and runtime model", "stage": 2,
     "question": "Can you trace evaluation, stack frames, runtime services and observable side effects?"},
    {"key": "memory", "title": "Memory and value semantics", "stage": 2,
     "question": "Can you explain allocation, copying, references, ownership/lifetimes or garbage collection?"},
    {"key": "errors", "title": "Errors and failure boundaries", "stage": 2,
     "question": "Can you propagate, classify and handle failures without hiding useful diagnostics?"},
    {"key": "concurrency", "title": "Concurrency and asynchronous execution", "stage": 2,
     "question": "Can you identify scheduling, shared-state, cancellation, race and deadlock risks?"},
    {"key": "modules", "title": "Modules, packages and visibility", "stage": 1,
     "question": "Can you define stable module boundaries and understand the import/dependency graph?"},
    {"key": "stdlib", "title": "Standard library", "stage": 3,
     "question": "Can you solve common collection, text, file, time and data tasks with standard APIs?"},
    {"key": "io-data", "title": "Files, I/O and data formats", "stage": 3,
     "question": "Can you validate external data and handle partial reads, encoding and I/O failures?"},
    {"key": "testing-debugging", "title": "Testing and debugging", "stage": 4,
     "question": "Can you reproduce a bug, isolate it, test the regression and inspect runtime state?"},
    {"key": "idioms", "title": "Idiomatic code and live-code reading", "stage": 4,
     "question": "Can you recognise and apply the conventions used by experienced language users?"},
    {"key": "ecosystem", "title": "Ecosystem and dependency discipline", "stage": 5,
     "question": "Can you choose maintained dependencies and understand build, release and compatibility?"},
    {"key": "architecture", "title": "Architecture and performance", "stage": 5,
     "question": "Can you design module boundaries and profile before making performance claims?"},
    {"key": "interop", "title": "Interoperability and FFI", "stage": 5,
     "question": "Can you reason about ABI, ownership transfer, data layout and boundary errors where relevant?"},
)

KATAS: tuple[dict[str, Any], ...] = (
    {"id": "core-01", "stage": 1, "title": "Validated configuration loader",
     "task": "Read a small configuration file, apply defaults and reject malformed values with field-specific errors.",
     "checks": "Valid input, missing fields, wrong types, unknown keys and empty files are covered by tests."},
    {"id": "core-02", "stage": 1, "title": "Collection transformation",
     "task": "Transform a collection using the language's native iteration, filtering and aggregation idioms.",
     "checks": "Empty input, duplicates, ordering and boundary values are tested."},
    {"id": "sem-01", "stage": 2, "title": "Value, reference and copy probe",
     "task": "Write a small experiment that distinguishes copying, aliasing, mutation and ownership in this language.",
     "checks": "The observed output is explained; no assumptions are carried over from another language."},
    {"id": "sem-02", "stage": 2, "title": "Error-boundary design",
     "task": "Build a three-layer operation with validation, domain errors and a top-level reporting boundary.",
     "checks": "Failures preserve context, expected errors are typed/classified and no silent catch remains."},
    {"id": "sem-03", "stage": 2, "title": "Concurrency safety exercise",
     "task": "Process independent work concurrently using the idiomatic primitive available in the language.",
     "checks": "Cancellation, bounded work, shared-state safety and deterministic shutdown are considered."},
    {"id": "stdlib-01", "stage": 3, "title": "Practical CLI utility",
     "task": "Create a CLI with argument validation, help, file input/output and meaningful exit codes.",
     "checks": "Bad arguments, unreadable files, overwrite policy and a successful run are tested."},
    {"id": "stdlib-02", "stage": 3, "title": "Data format transformer",
     "task": "Convert JSON or CSV records into a normalised representation with validation.",
     "checks": "Encoding, malformed rows, missing values and large inputs are addressed."},
    {"id": "stdlib-03", "stage": 3, "title": "Small network or stream client",
     "task": "Consume a stream or service using standard-library facilities where practical.",
     "checks": "Timeouts, partial input, protocol errors and resource cleanup are handled."},
    {"id": "quality-01", "stage": 4, "title": "Test-first bug fix",
     "task": "Reproduce a real defect, add a failing regression test, fix it and retain the test.",
     "checks": "The test fails before the fix and passes after; adjacent edge cases are covered."},
    {"id": "quality-02", "stage": 4, "title": "Idiom refactor",
     "task": "Refactor an early exercise using the language's standard conventions and abstractions.",
     "checks": "Behaviour is preserved and the reason for each substantive change is documented."},
    {"id": "quality-03", "stage": 4, "title": "Read and explain a library",
     "task": "Trace one small public library from API entry point through implementation and tests.",
     "checks": "Record module boundaries, error model, naming idioms and one deliberate trade-off."},
    {"id": "production-01", "stage": 5, "title": "Profile-guided improvement",
     "task": "Benchmark a representative workload, identify one bottleneck and compare a targeted change.",
     "checks": "Before/after measurements are reproducible and correctness tests remain green."},
)

TOOLCHAINS = {
    "C / C++": ("cc", "gcc", "clang", "cmake", "ninja"),
    "Rust": ("rustc", "cargo"),
    "Go": ("go",),
    "Python": ("python", "python3", "pytest", "mypy", "ruff"),
    "Java": ("java", "javac", "mvn", "gradle"),
    "JavaScript / TypeScript": ("node", "npm", "pnpm", "yarn", "tsc"),
    "C# / .NET": ("dotnet",),
    "Zig": ("zig",),
    "Haskell": ("ghc", "cabal", "stack"),
    "OCaml": ("ocaml", "opam", "dune"),
    "Ruby": ("ruby", "bundle"),
    "PHP": ("php", "composer"),
    "Lua": ("lua", "luajit",),
}

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def default_database_path() -> Path:
    configured = os.environ.get("REAPER_POLYGLOT_CODE_HOME")
    base = Path(configured).expanduser() if configured else Path.home() / ".reaper"
    return base / "polyglot-code.sqlite3"


def infer_family(language: str) -> str:
    name = language.casefold().replace(" ", "").replace("-", "")
    if name in {"rust"}:
        return "ownership"
    if name in {"c", "c++", "cpp", "zig", "assembly", "asm"}:
        return "manual-memory"
    if name in {"go", "golang"}:
        return "garbage-collected"
    if name in {"java", "c#", "csharp", "kotlin", "swift", "dart", "scala"}:
        return "managed-runtime"
    if name in {"python", "javascript", "typescript", "ruby", "php", "lua", "perl"}:
        return "dynamic"
    if name in {"haskell", "ocaml", "f#", "elm", "clojure", "erlang", "elixir"}:
        return "functional"
    return "multi-paradigm"


class PolyglotCodeError(Exception):
    """User-facing error raised by the programming-language learning subsystem."""


class PolyglotCodeStore:
    """Independent SQLite store for programming-language fluency data."""

    def __init__(self, database: str | Path | None = None) -> None:
        self.path = Path(database).expanduser() if database else default_database_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(str(self.path))
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.execute("PRAGMA journal_mode = WAL")
        self._initialize()

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> "PolyglotCodeStore":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def _initialize(self) -> None:
        self.connection.executescript("""
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY, value TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS profiles (
                id INTEGER PRIMARY KEY,
                target_language TEXT NOT NULL COLLATE NOCASE UNIQUE,
                known_languages_json TEXT NOT NULL DEFAULT '[]',
                current_level TEXT NOT NULL,
                family TEXT NOT NULL,
                goal TEXT NOT NULL DEFAULT '',
                daily_minutes INTEGER NOT NULL DEFAULT 60,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS concept_progress (
                profile_id INTEGER NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
                concept_key TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('unseen','in_progress','understood','idiomatic')),
                notes TEXT NOT NULL DEFAULT '',
                evidence TEXT NOT NULL DEFAULT '',
                updated_at TEXT NOT NULL,
                PRIMARY KEY(profile_id, concept_key)
            );
            CREATE TABLE IF NOT EXISTS comparisons (
                id INTEGER PRIMARY KEY,
                profile_id INTEGER NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
                concept_key TEXT NOT NULL,
                known_language TEXT NOT NULL,
                known_model TEXT NOT NULL,
                target_model TEXT NOT NULL,
                tradeoff TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                UNIQUE(profile_id, concept_key, known_language)
            );
            CREATE TABLE IF NOT EXISTS idioms (
                id INTEGER PRIMARY KEY,
                profile_id INTEGER NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                pattern TEXT NOT NULL,
                anti_pattern TEXT NOT NULL DEFAULT '',
                notes TEXT NOT NULL DEFAULT '',
                source TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(profile_id, name)
            );
            CREATE TABLE IF NOT EXISTS kata_progress (
                profile_id INTEGER NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
                kata_id TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('in_progress','completed')),
                score INTEGER CHECK(score BETWEEN 0 AND 5),
                solution_path TEXT NOT NULL DEFAULT '',
                notes TEXT NOT NULL DEFAULT '',
                updated_at TEXT NOT NULL,
                PRIMARY KEY(profile_id, kata_id)
            );
            CREATE TABLE IF NOT EXISTS error_journal (
                id INTEGER PRIMARY KEY,
                profile_id INTEGER NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
                title TEXT NOT NULL,
                symptom TEXT NOT NULL,
                cause TEXT NOT NULL,
                fix TEXT NOT NULL,
                lesson TEXT NOT NULL,
                language_version TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY,
                profile_id INTEGER NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
                mode TEXT NOT NULL,
                minutes INTEGER NOT NULL,
                notes TEXT NOT NULL DEFAULT '',
                score INTEGER CHECK(score BETWEEN 0 AND 5),
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_code_sessions
                ON sessions(profile_id, created_at);
            CREATE INDEX IF NOT EXISTS idx_code_errors
                ON error_journal(profile_id, created_at);
        """)
        row = self.connection.execute(
            "SELECT value FROM metadata WHERE key='schema_version'"
        ).fetchone()
        if row is None:
            self.connection.execute(
                "INSERT INTO metadata(key,value) VALUES('schema_version',?)",
                (str(SCHEMA_VERSION),),
            )
        elif int(row["value"]) > SCHEMA_VERSION:
            raise PolyglotCodeError(
                f"database schema {row['value']} is newer than supported {SCHEMA_VERSION}"
            )
        self.connection.commit()

    def create_profile(
        self, target_language: str, known_languages: list[str] | None = None,
        level: str = "novice", family: str = "auto", goal: str = "",
        daily_minutes: int = 60,
    ) -> dict[str, Any]:
        target = target_language.strip()
        level = level.casefold()
        if not target:
            raise PolyglotCodeError("target language cannot be empty")
        if level not in LEVELS:
            raise PolyglotCodeError(f"level must be one of: {', '.join(LEVELS)}")
        if not 5 <= daily_minutes <= 240:
            raise PolyglotCodeError("daily minutes must be between 5 and 240")
        if family == "auto":
            family = infer_family(target)
        if family not in FAMILIES:
            raise PolyglotCodeError(f"family must be one of: {', '.join(FAMILIES)}")
        known = [item.strip() for item in (known_languages or []) if item.strip()]
        now = utc_now()
        self.connection.execute("""
            INSERT INTO profiles(
                target_language, known_languages_json, current_level, family,
                goal, daily_minutes, created_at, updated_at
            ) VALUES(?,?,?,?,?,?,?,?)
            ON CONFLICT(target_language) DO UPDATE SET
                known_languages_json=excluded.known_languages_json,
                current_level=excluded.current_level, family=excluded.family,
                goal=excluded.goal, daily_minutes=excluded.daily_minutes,
                updated_at=excluded.updated_at
        """, (target, json.dumps(known, ensure_ascii=False), level, family,
              goal.strip(), daily_minutes, now, now))
        self.connection.commit()
        return self.get_profile(target)

    def list_profiles(self) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            "SELECT * FROM profiles ORDER BY target_language COLLATE NOCASE"
        ).fetchall()
        return [self._profile_dict(row) for row in rows]

    @staticmethod
    def _profile_dict(row: sqlite3.Row) -> dict[str, Any]:
        result = dict(row)
        result["known_languages"] = json.loads(result.pop("known_languages_json"))
        return result

    def get_profile(self, target_language: str | None = None) -> dict[str, Any]:
        if target_language:
            row = self.connection.execute(
                "SELECT * FROM profiles WHERE target_language=? COLLATE NOCASE",
                (target_language.strip(),),
            ).fetchone()
            if row is None:
                raise PolyglotCodeError(f"profile not found: {target_language}")
            return self._profile_dict(row)
        rows = self.connection.execute(
            "SELECT * FROM profiles ORDER BY target_language COLLATE NOCASE"
        ).fetchall()
        if not rows:
            raise PolyglotCodeError(
                "no programming-language profiles; create one with "
                "reaper polyglot-code init Rust --known C,C++"
            )
        if len(rows) > 1:
            raise PolyglotCodeError("several profiles exist; select one with --target LANGUAGE")
        return self._profile_dict(rows[0])

    def list_concepts(self, profile: dict[str, Any]) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            "SELECT * FROM concept_progress WHERE profile_id=?", (profile["id"],)
        ).fetchall()
        progress = {row["concept_key"]: dict(row) for row in rows}
        result = []
        for concept in CONCEPTS:
            item = dict(concept)
            state = progress.get(concept["key"])
            item.update({
                "status": state["status"] if state else "unseen",
                "notes": state["notes"] if state else "",
                "evidence": state["evidence"] if state else "",
            })
            result.append(item)
        return result

    def update_concept(
        self, profile: dict[str, Any], key: str, status: str,
        notes: str = "", evidence: str = "",
    ) -> None:
        if key not in {item["key"] for item in CONCEPTS}:
            choices = ", ".join(item["key"] for item in CONCEPTS)
            raise PolyglotCodeError(f"unknown concept '{key}'; valid keys: {choices}")
        if status not in TOPIC_STATUSES:
            raise PolyglotCodeError(f"status must be one of: {', '.join(TOPIC_STATUSES)}")
        self.connection.execute("""
            INSERT INTO concept_progress(profile_id,concept_key,status,notes,evidence,updated_at)
            VALUES(?,?,?,?,?,?)
            ON CONFLICT(profile_id,concept_key) DO UPDATE SET
                status=excluded.status, notes=excluded.notes,
                evidence=excluded.evidence, updated_at=excluded.updated_at
        """, (profile["id"], key, status, notes.strip(), evidence.strip(), utc_now()))
        self.connection.commit()

    def save_comparison(
        self, profile: dict[str, Any], concept_key: str, known_language: str,
        known_model: str, target_model: str, tradeoff: str = "",
    ) -> None:
        if concept_key not in {item["key"] for item in CONCEPTS}:
            raise PolyglotCodeError(f"unknown concept: {concept_key}")
        if not known_language.strip() or not known_model.strip() or not target_model.strip():
            raise PolyglotCodeError("known language, known model and target model are required")
        self.connection.execute("""
            INSERT INTO comparisons(
                profile_id,concept_key,known_language,known_model,target_model,tradeoff,created_at
            ) VALUES(?,?,?,?,?,?,?)
            ON CONFLICT(profile_id,concept_key,known_language) DO UPDATE SET
                known_model=excluded.known_model, target_model=excluded.target_model,
                tradeoff=excluded.tradeoff, created_at=excluded.created_at
        """, (profile["id"], concept_key, known_language.strip(), known_model.strip(),
              target_model.strip(), tradeoff.strip(), utc_now()))
        self.connection.commit()

    def list_comparisons(self, profile: dict[str, Any]) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            "SELECT * FROM comparisons WHERE profile_id=? ORDER BY concept_key,known_language",
            (profile["id"],),
        ).fetchall()
        return [dict(row) for row in rows]

    def add_idiom(
        self, profile: dict[str, Any], name: str, pattern: str,
        anti_pattern: str = "", notes: str = "", source: str = "",
    ) -> int:
        if not name.strip() or not pattern.strip():
            raise PolyglotCodeError("idiom name and pattern cannot be empty")
        now = utc_now()
        self.connection.execute("""
            INSERT INTO idioms(profile_id,name,pattern,anti_pattern,notes,source,created_at,updated_at)
            VALUES(?,?,?,?,?,?,?,?)
            ON CONFLICT(profile_id,name) DO UPDATE SET
                pattern=excluded.pattern, anti_pattern=excluded.anti_pattern,
                notes=excluded.notes, source=excluded.source, updated_at=excluded.updated_at
        """, (profile["id"], name.strip(), pattern.strip(), anti_pattern.strip(),
              notes.strip(), source.strip(), now, now))
        self.connection.commit()
        row = self.connection.execute(
            "SELECT id FROM idioms WHERE profile_id=? AND name=?",
            (profile["id"], name.strip()),
        ).fetchone()
        return int(row["id"])

    def list_idioms(self, profile: dict[str, Any]) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            "SELECT * FROM idioms WHERE profile_id=? ORDER BY name COLLATE NOCASE",
            (profile["id"],),
        ).fetchall()
        return [dict(row) for row in rows]

    def add_error(
        self, profile: dict[str, Any], title: str, symptom: str, cause: str,
        fix: str, lesson: str, language_version: str = "",
    ) -> int:
        if not all(value.strip() for value in (title, symptom, cause, fix, lesson)):
            raise PolyglotCodeError("title, symptom, cause, fix and lesson are required")
        cursor = self.connection.execute("""
            INSERT INTO error_journal(
                profile_id,title,symptom,cause,fix,lesson,language_version,created_at
            ) VALUES(?,?,?,?,?,?,?,?)
        """, (profile["id"], title.strip(), symptom.strip(), cause.strip(), fix.strip(),
              lesson.strip(), language_version.strip(), utc_now()))
        self.connection.commit()
        return int(cursor.lastrowid)

    def list_errors(self, profile: dict[str, Any], limit: int = 20) -> list[dict[str, Any]]:
        if limit < 1:
            raise PolyglotCodeError("error limit must be positive")
        rows = self.connection.execute(
            "SELECT * FROM error_journal WHERE profile_id=? ORDER BY id DESC LIMIT ?",
            (profile["id"], limit),
        ).fetchall()
        return [dict(row) for row in rows]

    def list_katas(self, profile: dict[str, Any], stage: int | None = None) -> list[dict[str, Any]]:
        progress_rows = self.connection.execute(
            "SELECT * FROM kata_progress WHERE profile_id=?", (profile["id"],)
        ).fetchall()
        progress = {row["kata_id"]: dict(row) for row in progress_rows}
        items = []
        for kata in KATAS:
            if stage is not None and kata["stage"] != stage:
                continue
            state = progress.get(kata["id"], {})
            items.append({
                **kata, "status": state.get("status", "not_started"),
                "score": state.get("score"), "solution_path": state.get("solution_path", ""),
                "notes": state.get("notes", ""),
            })
        return items

    def complete_kata(
        self, profile: dict[str, Any], kata_id: str, score: int | None = None,
        notes: str = "", solution_path: str = "",
    ) -> None:
        if kata_id not in {item["id"] for item in KATAS}:
            raise PolyglotCodeError(f"unknown kata '{kata_id}'")
        if score is not None and not 0 <= score <= 5:
            raise PolyglotCodeError("kata score must be from 0 to 5")
        self.connection.execute("""
            INSERT INTO kata_progress(profile_id,kata_id,status,score,solution_path,notes,updated_at)
            VALUES(?,?,'completed',?,?,?,?)
            ON CONFLICT(profile_id,kata_id) DO UPDATE SET
                status='completed', score=excluded.score, solution_path=excluded.solution_path,
                notes=excluded.notes, updated_at=excluded.updated_at
        """, (profile["id"], kata_id, score, solution_path.strip(), notes.strip(), utc_now()))
        self.connection.commit()

    def log_session(
        self, profile: dict[str, Any], minutes: int, mode: str,
        notes: str = "", score: int | None = None,
    ) -> int:
        if minutes < 1 or minutes > 480:
            raise PolyglotCodeError("session minutes must be between 1 and 480")
        if mode not in SESSION_MODES:
            raise PolyglotCodeError(f"mode must be one of: {', '.join(SESSION_MODES)}")
        if score is not None and not 0 <= score <= 5:
            raise PolyglotCodeError("session score must be from 0 to 5")
        cursor = self.connection.execute("""
            INSERT INTO sessions(profile_id,mode,minutes,notes,score,created_at)
            VALUES(?,?,?,?,?,?)
        """, (profile["id"], mode, minutes, notes.strip(), score, utc_now()))
        self.connection.commit()
        return int(cursor.lastrowid)

    def daily_plan(self, profile: dict[str, Any], minutes: int | None = None) -> list[dict[str, Any]]:
        budget = profile["daily_minutes"] if minutes is None else minutes
        if not 5 <= budget <= 240:
            raise PolyglotCodeError("plan minutes must be between 5 and 240")
        mastered = sum(item["status"] in ("understood", "idiomatic")
                       for item in self.list_concepts(profile))
        ratio = mastered / len(CONCEPTS)
        if profile["current_level"] in ("novice", "working") or ratio < 0.35:
            tasks = [
                ("model", "Разобрать одну концепцию и построить модель исполнения", 0.30),
                ("coding", "Решить небольшую задачу без копирования чужого решения", 0.40),
                ("testing", "Проверить граничные случаи и добавить тесты", 0.15),
                ("review", "Записать выводы, ошибки и следующий шаг", 0.15),
            ]
        else:
            tasks = [
                ("reading", "Прочитать живой код или реализацию стандартной библиотеки", 0.25),
                ("project", "Продвинуть мини-проект или рабочую задачу", 0.40),
                ("refactoring", "Сделать идиоматичный рефакторинг и проверить поведение", 0.20),
                ("review", "Обновить ментальные модели и журнал ошибок", 0.15),
            ]
        if profile["family"] in ("ownership", "manual-memory"):
            tasks[0] = ("model", "Исследовать владение, время жизни, копирование и стоимость аллокаций", tasks[0][2] + 0.05)
            last = tasks[-1]
            tasks[-1] = (last[0], last[1], last[2] - 0.05)
        if profile["family"] in ("dynamic", "garbage-collected", "managed-runtime"):
            tasks[2] = (tasks[2][0], "Проверить контракты данных, мутабельность и стоимость аллокаций", tasks[2][2] + 0.05)
            last = tasks[-1]
            tasks[-1] = (last[0], last[1], last[2] - 0.05)
        allocations = [int(budget * weight) for _, _, weight in tasks]
        allocations[-1] += budget - sum(allocations)
        return [
            {"mode": mode, "task": task, "minutes": allocation}
            for (mode, task, _), allocation in zip(tasks, allocations)
        ]

    def report(self, profile: dict[str, Any]) -> dict[str, Any]:
        concepts = self.list_concepts(profile)
        mastered = sum(item["status"] in ("understood", "idiomatic") for item in concepts)
        kata_rows = self.list_katas(profile)
        completed = sum(item["status"] == "completed" for item in kata_rows)
        today = datetime.now(timezone.utc) - timedelta(days=7)
        recent = self.connection.execute("""
            SELECT COUNT(*) AS sessions, COALESCE(SUM(minutes),0) AS minutes
            FROM sessions WHERE profile_id=? AND created_at>=?
        """, (profile["id"], today.isoformat(timespec="seconds"))).fetchone()
        error_count = self.connection.execute(
            "SELECT COUNT(*) FROM error_journal WHERE profile_id=?", (profile["id"],)
        ).fetchone()[0]
        idiom_count = self.connection.execute(
            "SELECT COUNT(*) FROM idioms WHERE profile_id=?", (profile["id"],)
        ).fetchone()[0]
        comparison_count = self.connection.execute(
            "SELECT COUNT(*) FROM comparisons WHERE profile_id=?", (profile["id"],)
        ).fetchone()[0]
        return {
            "target_language": profile["target_language"],
            "known_languages": profile["known_languages"],
            "level": profile["current_level"], "family": profile["family"],
            "concepts_mastered": mastered, "concepts_total": len(concepts),
            "concept_coverage": mastered / len(concepts),
            "katas_completed": completed, "katas_total": len(kata_rows),
            "idioms": idiom_count, "comparisons": comparison_count,
            "error_notes": error_count,
            "last_7_days_sessions": int(recent["sessions"]),
            "last_7_days_minutes": int(recent["minutes"]),
            "next_concepts": [item["key"] for item in concepts
                              if item["status"] not in ("understood", "idiomatic")][:5],
        }

    def export_profile(self, profile: dict[str, Any]) -> dict[str, Any]:
        sessions = self.connection.execute(
            "SELECT * FROM sessions WHERE profile_id=? ORDER BY id",
            (profile["id"],),
        ).fetchall()
        errors = self.connection.execute(
            "SELECT * FROM error_journal WHERE profile_id=? ORDER BY id",
            (profile["id"],),
        ).fetchall()
        return {
            "schema_version": SCHEMA_VERSION,
            "exported_at": utc_now(),
            "profile": profile,
            "concepts": self.list_concepts(profile),
            "comparisons": self.list_comparisons(profile),
            "idioms": self.list_idioms(profile),
            "katas": self.list_katas(profile),
            "errors": [dict(row) for row in errors],
            "sessions": [dict(row) for row in sessions],
        }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="reaper polyglot-code",
        description="Local-first engineering fluency for programming languages.",
    )
    parser.add_argument("--db", help="SQLite database (default: ~/.reaper/polyglot-code.sqlite3)")
    parser.add_argument("--target", help="target language when multiple profiles exist")
    commands = parser.add_subparsers(dest="command", required=True)

    init = commands.add_parser("init", help="create or update a programming-language profile")
    init.add_argument("language")
    init.add_argument("--known", default="", help="comma-separated languages you already know")
    init.add_argument("--level", choices=LEVELS, default="novice")
    init.add_argument("--family", choices=("auto",) + FAMILIES, default="auto")
    init.add_argument("--goal", default="")
    init.add_argument("--minutes", type=int, default=60)
    commands.add_parser("profile", help="list configured language profiles")

    roadmap = commands.add_parser("roadmap", help="show the universal six-stage roadmap")
    roadmap.add_argument("--stage", type=int, choices=range(0, 6))
    concept = commands.add_parser("concept", help="track semantic concepts and mastery")
    concept_commands = concept.add_subparsers(dest="concept_command", required=True)
    concept_list = concept_commands.add_parser("list", help="list concept checklist")
    concept_list.add_argument("--status", choices=TOPIC_STATUSES)
    concept_update = concept_commands.add_parser("update", help="update mastery with evidence")
    concept_update.add_argument("key", choices=tuple(item["key"] for item in CONCEPTS))
    concept_update.add_argument("--status", required=True, choices=TOPIC_STATUSES)
    concept_update.add_argument("--notes", default="")
    concept_update.add_argument("--evidence", default="")

    compare = commands.add_parser("compare", help="record a cross-language mental-model comparison")
    compare.add_argument("concept", choices=tuple(item["key"] for item in CONCEPTS))
    compare.add_argument("--known-language", required=True)
    compare.add_argument("--known-model", required=True, help="how this problem is handled in the known language")
    compare.add_argument("--target-model", required=True, help="how the target language handles the same problem")
    compare.add_argument("--tradeoff", default="", help="performance, safety, clarity or complexity trade-off")

    katas = commands.add_parser("kata", help="track practical, language-neutral exercises")
    kata_commands = katas.add_subparsers(dest="kata_command", required=True)
    kata_list = kata_commands.add_parser("list", help="list katas")
    kata_list.add_argument("--stage", type=int, choices=range(0, 6))
    kata_complete = kata_commands.add_parser("complete", help="record a completed kata")
    kata_complete.add_argument("id")
    kata_complete.add_argument("--score", type=int, choices=range(0, 6))
    kata_complete.add_argument("--solution", default="")
    kata_complete.add_argument("--notes", default="")

    idiom = commands.add_parser("idiom", help="store language-native patterns")
    idiom_commands = idiom.add_subparsers(dest="idiom_command", required=True)
    idiom_add = idiom_commands.add_parser("add", help="add or replace an idiom note")
    idiom_add.add_argument("name")
    idiom_add.add_argument("--pattern", required=True)
    idiom_add.add_argument("--anti-pattern", default="")
    idiom_add.add_argument("--notes", default="")
    idiom_add.add_argument("--source", default="")
    idiom_commands.add_parser("list", help="list recorded idioms")

    error = commands.add_parser("error", help="maintain a diagnostic and root-cause journal")
    error_commands = error.add_subparsers(dest="error_command", required=True)
    error_add = error_commands.add_parser("add", help="record an error and its lesson")
    error_add.add_argument("title")
    error_add.add_argument("--symptom", required=True)
    error_add.add_argument("--cause", required=True)
    error_add.add_argument("--fix", required=True)
    error_add.add_argument("--lesson", required=True)
    error_add.add_argument("--version", default="")
    error_list = error_commands.add_parser("list", help="list recent errors")
    error_list.add_argument("--limit", type=int, default=20)

    commands.add_parser("toolchain", help="inspect known tool executables on PATH; never runs or installs them")
    plan = commands.add_parser("plan", help="build an adaptive daily engineering-practice plan")
    plan.add_argument("--minutes", type=int)
    session = commands.add_parser("session", help="record a completed practice session")
    session.add_argument("--minutes", type=int, required=True)
    session.add_argument("--mode", choices=SESSION_MODES, required=True)
    session.add_argument("--notes", default="")
    session.add_argument("--score", type=int, choices=range(0, 6))
    commands.add_parser("diagnose", help="show the main knowledge gaps to work on next")
    commands.add_parser("report", help="show progress and recent practice")
    export = commands.add_parser("export", help="export a profile as portable JSON")
    export.add_argument("--output", type=Path)
    return parser


def _print_roadmap(stage_filter: int | None = None) -> None:
    for stage in STAGES:
        if stage_filter is not None and stage["id"] != stage_filter:
            continue
        print(f"\nЭтап {stage['id']}: {stage['name']} · {stage['duration']}")
        print(f"  Цель: {stage['goal']}")
        for task in stage["tasks"]:
            print(f"  • {task}")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        with PolyglotCodeStore(args.db) as store:
            if args.command == "init":
                known = [item.strip() for item in args.known.split(",") if item.strip()]
                profile = store.create_profile(
                    args.language, known, args.level, args.family, args.goal, args.minutes
                )
                print(
                    f"Профиль готов: {profile['target_language']} · {profile['current_level']} · "
                    f"{profile['family']} · {profile['daily_minutes']} мин/день"
                )
                if known:
                    print("Уже известные языки: " + ", ".join(known))
                return 0
            if args.command == "profile":
                profiles = store.list_profiles()
                if not profiles:
                    print("Профилей пока нет. Начните: reaper polyglot-code init Rust --known C,C++")
                for item in profiles:
                    known = ", ".join(item["known_languages"]) or "не указаны"
                    print(
                        f"{item['target_language']} | {item['current_level']} | {item['family']} | "
                        f"знаю: {known} | {item['daily_minutes']} мин/день"
                    )
                return 0
            if args.command == "roadmap":
                _print_roadmap(args.stage)
                return 0

            profile = store.get_profile(args.target)
            if args.command == "concept":
                concepts = store.list_concepts(profile)
                if args.concept_command == "update":
                    store.update_concept(profile, args.key, args.status, args.notes, args.evidence)
                    print(f"Концепция обновлена: {args.key} → {args.status}")
                else:
                    rows = [item for item in concepts
                            if args.status is None or item["status"] == args.status]
                    for item in rows:
                        print(f"[{item['status']:<11}] {item['key']:<18} {item['title']}")
                        print(f"              {item['question']}")
                return 0
            if args.command == "compare":
                store.save_comparison(
                    profile, args.concept, args.known_language, args.known_model,
                    args.target_model, args.tradeoff,
                )
                print(f"Сравнение сохранено: {args.known_language} → {profile['target_language']} / {args.concept}")
                print("Модель: что решает концепция → аналог → компромисс.")
                return 0
            if args.command == "kata":
                if args.kata_command == "complete":
                    store.complete_kata(profile, args.id, args.score, args.notes, args.solution)
                    print(f"Ката отмечена выполненной: {args.id}")
                else:
                    for item in store.list_katas(profile, args.stage):
                        print(f"[{item['status']:<11}] {item['id']:<15} {item['title']} (этап {item['stage']})")
                        print(f"              {item['task']}")
                        print(f"              Проверка: {item['checks']}")
                return 0
            if args.command == "idiom":
                if args.idiom_command == "add":
                    item_id = store.add_idiom(
                        profile, args.name, args.pattern, args.anti_pattern,
                        args.notes, args.source,
                    )
                    print(f"Идиома сохранена: #{item_id} · {args.name}")
                else:
                    items = store.list_idioms(profile)
                    if not items:
                        print("Идиом пока нет. Добавьте пример через: reaper polyglot-code idiom add --help")
                    for item in items:
                        print(f"#{item['id']} {item['name']}: {item['pattern']}")
                        if item["anti_pattern"]:
                            print(f"  Вместо: {item['anti_pattern']}")
                        if item["notes"]:
                            print(f"  Почему: {item['notes']}")
                return 0
            if args.command == "error":
                if args.error_command == "add":
                    item_id = store.add_error(
                        profile, args.title, args.symptom, args.cause,
                        args.fix, args.lesson, args.version,
                    )
                    print(f"Ошибка записана: #{item_id} · причина и урок сохранены")
                else:
                    for item in store.list_errors(profile, args.limit):
                        print(f"#{item['id']} {item['title']} [{item['language_version'] or 'версия не указана'}]")
                        print(f"  Симптом: {item['symptom']}")
                        print(f"  Причина: {item['cause']}")
                        print(f"  Исправление: {item['fix']}")
                        print(f"  Вывод: {item['lesson']}")
                return 0
            if args.command == "toolchain":
                for label, executables in TOOLCHAINS.items():
                    found = [name for name in executables if shutil.which(name)]
                    state = ", ".join(found) if found else "не найдено в PATH"
                    print(f"{label:<24} {state}")
                print("Проверка только PATH: исполняемые файлы не запускались, установки не выполнялись.")
                return 0
            if args.command == "plan":
                tasks = store.daily_plan(profile, args.minutes)
                total = sum(item["minutes"] for item in tasks)
                print(f"План: {profile['target_language']} · {total} минут · семейство {profile['family']}")
                for item in tasks:
                    print(f"  {item['minutes']:>3} мин · {item['mode']:<12} {item['task']}")
                return 0
            if args.command == "session":
                session_id = store.log_session(profile, args.minutes, args.mode, args.notes, args.score)
                print(f"Сессия сохранена: #{session_id} · {args.minutes} мин · {args.mode}")
                return 0
            if args.command == "diagnose":
                concepts = store.list_concepts(profile)
                gaps = [item for item in concepts if item["status"] not in ("understood", "idiomatic")]
                print(f"Самодиагностика: закрыто {len(concepts) - len(gaps)} из {len(concepts)} концепций.")
                for item in gaps[:8]:
                    print(f"  [{item['status']}] Этап {item['stage']} · {item['title']}: {item['question']}")
                if not gaps:
                    print("Базовая карта закрыта. Переходите к архитектуре, профилированию и реальному проекту.")
                return 0
            if args.command == "report":
                data = store.report(profile)
                print(f"Язык: {data['target_language']} · {data['level']} · {data['family']}")
                print(f"Концепции: {data['concepts_mastered']}/{data['concepts_total']} ({data['concept_coverage']:.0%})")
                print(f"Практические ката: {data['katas_completed']}/{data['katas_total']}")
                print(f"Идиомы: {data['idioms']} · сопоставления моделей: {data['comparisons']} · записей ошибок: {data['error_notes']}")
                print(f"За 7 дней: {data['last_7_days_sessions']} сессий · {data['last_7_days_minutes']} минут")
                if data["next_concepts"]:
                    print("Следующие концепции: " + ", ".join(data["next_concepts"]))
                return 0
            if args.command == "export":
                payload = json.dumps(store.export_profile(profile), ensure_ascii=False, indent=2)
                if args.output:
                    args.output.parent.mkdir(parents=True, exist_ok=True)
                    args.output.write_text(payload + "\n", encoding="utf-8")
                    print(f"Экспортировано: {args.output}")
                else:
                    print(payload)
                return 0
    except (PolyglotCodeError, OSError, sqlite3.Error) as error:
        print(f"reaper polyglot-code: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
