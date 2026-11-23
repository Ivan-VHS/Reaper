"""Local-first polyglot immersion toolkit for Reaper.

No network, media playback, speech-recognition or translation side effects are
performed by this module. Learners import material they may use and practise
with contextual phrase cards.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
import sys
import unicodedata
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Iterable

SCHEMA_VERSION = 3
CEFR_LEVELS = ("A0", "A1", "A2", "B1", "B2", "C1", "C2")
CONTENT_KINDS = ("text", "dialogue", "story", "article")
SESSION_MODES = ("reading", "writing", "analysis", "review", "reflection")
SCRIPT_FAMILIES = ("auto", "latin", "cyrillic", "arabic", "devanagari", "han", "japanese", "hangul", "thai", "other")
LANGUAGE_SCRIPT_CODES = {
    "zh": "han", "yue": "han", "ja": "japanese", "ko": "hangul",
    "ar": "arabic", "fa": "arabic", "ur": "arabic",
    "hi": "devanagari", "mr": "devanagari", "th": "thai", "lo": "thai",
    "ru": "cyrillic", "uk": "cyrillic", "bg": "cyrillic",
    "sr": "cyrillic", "mk": "cyrillic", "be": "cyrillic",
}
LANGUAGE_SCRIPT_NAMES = {
    "chinese": "han", "mandarin": "han", "cantonese": "han", "中文": "han",
    "japanese": "japanese", "日本語": "japanese", "korean": "hangul", "한국어": "hangul",
    "arabic": "arabic", "persian": "arabic", "farsi": "arabic", "urdu": "arabic",
    "hindi": "devanagari", "marathi": "devanagari", "thai": "thai", "lao": "thai",
    "russian": "cyrillic", "ukrainian": "cyrillic", "bulgarian": "cyrillic",
    "serbian": "cyrillic", "macedonian": "cyrillic", "belarusian": "cyrillic",
}
TONAL_LANGUAGE_CODES = {"zh", "yue", "vi", "th", "lo", "yo", "ha"}
TONAL_LANGUAGE_NAMES = {"mandarin", "chinese", "cantonese", "vietnamese", "thai", "lao", "yoruba", "hausa"}
CJK_RANGES = ((0x3400, 0x4DBF), (0x4E00, 0x9FFF), (0xF900, 0xFAFF),
              (0x3040, 0x30FF), (0x31F0, 0x31FF), (0xAC00, 0xD7AF))


class PolyglotError(Exception):
    """A user-facing error from the polyglot subsystem."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def default_database_path() -> Path:
    configured = os.environ.get("REAPER_POLYGLOT_HOME")
    base = Path(configured).expanduser() if configured else Path.home() / ".reaper"
    return base / "polyglot.sqlite3"


def normalize_text(value: str) -> str:
    return unicodedata.normalize("NFKC", value).strip()


def infer_script_family(language: str, language_code: str = "") -> str:
    """Infer a practical writing-system default from a language code/name."""
    code = language_code.strip().casefold().split("-")[0]
    if code in LANGUAGE_SCRIPT_CODES:
        return LANGUAGE_SCRIPT_CODES[code]
    return LANGUAGE_SCRIPT_NAMES.get(normalize_text(language).casefold(), "latin")


def infer_tonal_language(language: str, language_code: str = "") -> bool:
    code = language_code.strip().casefold().split("-")[0]
    return code in TONAL_LANGUAGE_CODES or normalize_text(language).casefold() in TONAL_LANGUAGE_NAMES


def default_orthography_focus(script_family: str, tonal_language: bool) -> str:
    if tonal_language:
        return "written tone marks, syllable boundaries, and minimal-pair spelling"
    return {
        "japanese": "kana and kanji spelling patterns, long-vowel notation, and small-kana combinations",
        "han": "character forms, written tone marks, and word-boundary segmentation",
        "hangul": "batchim spelling, syllable-block structure, and spacing rules",
        "arabic": "letter forms, vowel marks, hamza spelling, and joined-letter rules",
        "devanagari": "matras, conjunct letters, and retroflex spelling distinctions",
        "cyrillic": "stress marks, spelling alternations, and soft-sign conventions",
        "thai": "tone marks, vowel symbols, and consonant-class spelling",
    }.get(script_family, "spelling contrasts, stress marks, and written word boundaries")


def script_learning_notes(profile: dict[str, Any]) -> list[str]:
    script = profile.get("script_family", "latin")
    notes = {
        "japanese": ["Study kana and kanji together through recurring written words and phrases."],
        "han": ["Keep tone marks in written romanization and distinguish characters by their written forms."],
        "hangul": ["Study Hangul syllable blocks, batchim spelling, and spacing rules."],
        "arabic": ["Use written vowel marks early, then gradually remove reading aids."],
        "devanagari": ["Learn the native script directly; use transliteration only as a temporary reading bridge."],
        "cyrillic": ["Mark stress in written examples when it is not predictable from spelling."],
        "thai": ["Study tone marks, vowel symbols, and consonant-class spelling together."],
    }.get(script, ["Keep native spelling, written examples, and useful phrases linked from the beginning."])
    if profile.get("tonal_language"):
        notes.append("Preserve tone marks in written examples and compare minimal spelling pairs.")
    if profile.get("romanization_bridge"):
        notes.append("Romanization is a temporary bridge: reduce it as native-script reading becomes comfortable.")
    return notes


def _is_cjk(character: str) -> bool:
    point = ord(character)
    return any(start <= point <= end for start, end in CJK_RANGES)


def _is_compact_script(character: str) -> bool:
    point = ord(character)
    return _is_cjk(character) or 0x0E00 <= point <= 0x0E7F


def tokenize(text: str) -> list[str]:
    """Tokenize whitespace languages and approximate compact scripts by grapheme units.

    Chinese/Japanese/Korean morphology is not inferred. Compact-script characters
    are counted as units and combining marks remain attached to their base.
    This is a coverage heuristic, not a comprehension score.
    """
    normalized = unicodedata.normalize("NFKC", text).casefold()
    tokens: list[str] = []
    index = 0
    while index < len(normalized):
        character = normalized[index]
        if unicodedata.category(character).startswith("M") and tokens:
            tokens[-1] += character
            index += 1
            continue
        if _is_compact_script(character):
            unit = character
            index += 1
            while index < len(normalized) and unicodedata.category(normalized[index]).startswith("M"):
                unit += normalized[index]
                index += 1
            tokens.append(unit)
            continue
        if character.isalnum():
            start = index
            index += 1
            while index < len(normalized):
                following = normalized[index]
                if _is_compact_script(following):
                    break
                category = unicodedata.category(following)
                if following.isalnum() or category.startswith("M") or following in {"'", "’"}:
                    index += 1
                else:
                    break
            tokens.append(normalized[start:index])
            continue
        index += 1
    return tokens


def clean_subtitles(text: str) -> str:
    """Remove common SRT/VTT numbering and timestamp lines."""
    output: list[str] = []
    timestamp = re.compile(r"^\s*(?:\d{1,2}:)?\d{2}:\d{2}[,.]\d{3}\s*-->")
    for line in text.replace("\ufeff", "").splitlines():
        value = line.strip()
        if not value or value.upper() == "WEBVTT" or value.isdigit():
            continue
        if timestamp.match(value) or value.startswith(("NOTE ", "STYLE", "REGION")):
            continue
        output.append(value)
    return "\n".join(output)


class PolyglotStore:
    """SQLite-backed language profiles, material, phrase cards and practice."""

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

    def __enter__(self) -> "PolyglotStore":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def _initialize(self) -> None:
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY, value TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS profiles (
                id INTEGER PRIMARY KEY,
                target_language TEXT NOT NULL COLLATE NOCASE UNIQUE,
                native_language TEXT NOT NULL,
                current_level TEXT NOT NULL DEFAULT 'A0',
                goal TEXT NOT NULL DEFAULT '',
                daily_minutes INTEGER NOT NULL DEFAULT 45,
                language_code TEXT NOT NULL DEFAULT '',
                script_family TEXT NOT NULL DEFAULT 'auto',
                tonal_language INTEGER NOT NULL DEFAULT 0,
                romanization_bridge INTEGER NOT NULL DEFAULT 0,
                phonetic_focus TEXT NOT NULL DEFAULT '',
                orthography_focus TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS content (
                id INTEGER PRIMARY KEY,
                profile_id INTEGER NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
                title TEXT NOT NULL, kind TEXT NOT NULL, body TEXT NOT NULL,
                translation TEXT NOT NULL DEFAULT '', source TEXT NOT NULL DEFAULT '',
                media_path TEXT NOT NULL DEFAULT '', level TEXT NOT NULL DEFAULT '',
                word_count INTEGER NOT NULL DEFAULT 0, fingerprint TEXT NOT NULL,
                created_at TEXT NOT NULL, UNIQUE(profile_id, fingerprint)
            );
            CREATE TABLE IF NOT EXISTS phrases (
                id INTEGER PRIMARY KEY,
                profile_id INTEGER NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
                content_id INTEGER REFERENCES content(id) ON DELETE SET NULL,
                phrase TEXT NOT NULL, translation TEXT NOT NULL,
                context TEXT NOT NULL DEFAULT '', pronunciation TEXT NOT NULL DEFAULT '',
                source TEXT NOT NULL DEFAULT '', tags_json TEXT NOT NULL DEFAULT '[]',
                personal_example TEXT NOT NULL DEFAULT '', frequency_rank INTEGER,
                ease REAL NOT NULL DEFAULT 2.5, interval_days INTEGER NOT NULL DEFAULT 0,
                repetitions INTEGER NOT NULL DEFAULT 0, lapses INTEGER NOT NULL DEFAULT 0,
                due_on TEXT NOT NULL, last_reviewed_at TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
                UNIQUE(profile_id, phrase, context)
            );
            CREATE TABLE IF NOT EXISTS review_events (
                id INTEGER PRIMARY KEY,
                phrase_id INTEGER NOT NULL REFERENCES phrases(id) ON DELETE CASCADE,
                rating INTEGER NOT NULL CHECK(rating BETWEEN 0 AND 5),
                previous_interval INTEGER NOT NULL, next_interval INTEGER NOT NULL,
                due_on TEXT NOT NULL, created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY,
                profile_id INTEGER NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
                mode TEXT NOT NULL, minutes INTEGER NOT NULL,
                notes TEXT NOT NULL DEFAULT '', score INTEGER,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_phrases_due
                ON phrases(profile_id, due_on, created_at);
            CREATE INDEX IF NOT EXISTS idx_content_profile
                ON content(profile_id, created_at);
            CREATE INDEX IF NOT EXISTS idx_sessions_profile
                ON sessions(profile_id, created_at);
            """
        )
        # Additive migrations keep existing local workspaces usable.
        migrations = {
            "profiles": {
                "language_code": "TEXT NOT NULL DEFAULT ''",
                "script_family": "TEXT NOT NULL DEFAULT 'auto'",
                "tonal_language": "INTEGER NOT NULL DEFAULT 0",
                "romanization_bridge": "INTEGER NOT NULL DEFAULT 0",
                "phonetic_focus": "TEXT NOT NULL DEFAULT ''",
                "orthography_focus": "TEXT NOT NULL DEFAULT ''",
            },
            "phrases": {
                "personal_example": "TEXT NOT NULL DEFAULT ''",
                "frequency_rank": "INTEGER",
            },
        }
        for table, additions in migrations.items():
            present = {row["name"] for row in self.connection.execute(f"PRAGMA table_info({table})")}
            for column, declaration in additions.items():
                if column not in present:
                    self.connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {declaration}")

        row = self.connection.execute(
            "SELECT value FROM metadata WHERE key='schema_version'"
        ).fetchone()
        if row is None:
            self.connection.execute(
                "INSERT INTO metadata(key,value) VALUES('schema_version',?)",
                (str(SCHEMA_VERSION),),
            )
        elif int(row["value"]) > SCHEMA_VERSION:
            raise PolyglotError(
                f"database schema {row['value']} is newer than supported {SCHEMA_VERSION}"
            )
        elif int(row["value"]) < SCHEMA_VERSION:
            self.connection.execute(
                "UPDATE metadata SET value=? WHERE key='schema_version'",
                (str(SCHEMA_VERSION),),
            )

        # Older profiles lacked script and written-orthography guidance.
        legacy_profiles = self.connection.execute(
            """SELECT id,target_language,language_code FROM profiles
               WHERE script_family='auto' OR script_family='' OR orthography_focus=''"""
        ).fetchall()
        for legacy in legacy_profiles:
            language = legacy["target_language"]
            code = legacy["language_code"] or ""
            script = infer_script_family(language, code)
            tonal = infer_tonal_language(language, code)
            bridge = script in {"han", "japanese", "hangul", "arabic", "devanagari", "thai"}
            focus = default_orthography_focus(script, tonal)
            self.connection.execute(
                """UPDATE profiles SET script_family=?,tonal_language=?,
                   romanization_bridge=?,orthography_focus=? WHERE id=?""",
                (script, int(tonal), int(bridge), focus, legacy["id"]),
            )
        self.connection.commit()

    def create_profile(
        self, target_language: str, native_language: str, level: str = "A0",
        goal: str = "", daily_minutes: int = 45, language_code: str = "",
        script_family: str = "auto", tonal_language: bool | None = None,
        romanization_bridge: bool | None = None, orthography_focus: str = "",
    ) -> dict[str, Any]:
        target_language = normalize_text(target_language)
        native_language = normalize_text(native_language)
        level = level.upper()
        if not target_language or not native_language:
            raise PolyglotError("target and native language names cannot be empty")
        if level not in CEFR_LEVELS:
            raise PolyglotError(f"level must be one of: {', '.join(CEFR_LEVELS)}")
        if isinstance(daily_minutes, bool) or not isinstance(daily_minutes, int) or not 5 <= daily_minutes <= 240:
            raise PolyglotError("daily minutes must be an integer between 5 and 240")
        if script_family not in SCRIPT_FAMILIES:
            raise PolyglotError(f"script family must be one of: {', '.join(SCRIPT_FAMILIES)}")
        language_code = language_code.strip().casefold()
        resolved_script = infer_script_family(target_language, language_code) if script_family == "auto" else script_family
        inferred_tonal = infer_tonal_language(target_language, language_code)
        if tonal_language is not None and not isinstance(tonal_language, bool):
            raise PolyglotError("tonal_language must be a boolean or None")
        if romanization_bridge is not None and not isinstance(romanization_bridge, bool):
            raise PolyglotError("romanization_bridge must be a boolean or None")
        tonal = inferred_tonal if tonal_language is None else tonal_language
        bridge_default = resolved_script in {"han", "japanese", "hangul", "arabic", "devanagari", "thai"}
        bridge = bridge_default if romanization_bridge is None else romanization_bridge
        focus = orthography_focus.strip() or default_orthography_focus(resolved_script, tonal)
        now = utc_now()
        self.connection.execute(
            """
            INSERT INTO profiles(target_language,native_language,current_level,goal,
                                 daily_minutes,language_code,script_family,tonal_language,
                                 romanization_bridge,orthography_focus,created_at,updated_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(target_language) DO UPDATE SET
              native_language=excluded.native_language,
              current_level=excluded.current_level, goal=excluded.goal,
              daily_minutes=excluded.daily_minutes, language_code=excluded.language_code,
              script_family=excluded.script_family, tonal_language=excluded.tonal_language,
              romanization_bridge=excluded.romanization_bridge,
              orthography_focus=excluded.orthography_focus, updated_at=excluded.updated_at
            """,
            (target_language, native_language, level, goal, daily_minutes, language_code,
             resolved_script, int(tonal), int(bridge), focus, now, now),
        )
        self.connection.commit()
        return self.get_profile(target_language)

    def list_profiles(self) -> list[dict[str, Any]]:
        return [dict(row) for row in self.connection.execute(
            "SELECT * FROM profiles ORDER BY target_language COLLATE NOCASE"
        ).fetchall()]

    def get_profile(self, target_language: str | None = None) -> dict[str, Any]:
        profiles = self.list_profiles()
        if not profiles:
            raise PolyglotError("no language profile exists; run 'reaper polyglot init' first")
        if target_language:
            for profile in profiles:
                if profile["target_language"].casefold() == target_language.casefold():
                    return profile
            raise PolyglotError(f"language profile not found: {target_language}")
        if len(profiles) != 1:
            names = ", ".join(item["target_language"] for item in profiles)
            raise PolyglotError(f"choose a target with --target; configured languages: {names}")
        return profiles[0]

    def add_content(
        self, profile: dict[str, Any], title: str, body: str, kind: str = "text",
        translation: str = "", source: str = "", level: str = "",
    ) -> int:
        if kind not in CONTENT_KINDS:
            raise PolyglotError(f"content kind must be one of: {', '.join(CONTENT_KINDS)}")
        level = level.upper()
        if level and level not in CEFR_LEVELS:
            raise PolyglotError(f"content level must be one of: {', '.join(CEFR_LEVELS)}")
        if Path(source or title).suffix.casefold() in (".srt", ".vtt"):
            body = clean_subtitles(body)
        else:
            body = body.strip()
        if not body:
            raise PolyglotError("content body is empty")
        title = title.strip() or "Untitled content"
        fingerprint = hashlib.sha256((title + "\0" + body).encode("utf-8")).hexdigest()
        try:
            cursor = self.connection.execute(
                """
                INSERT INTO content(profile_id,title,kind,body,translation,source,
                                    level,word_count,fingerprint,created_at)
                VALUES(?,?,?,?,?,?,?,?,?,?)
                """,
                (profile["id"], title, kind, body, translation, source,
                 level, len(tokenize(body)), fingerprint, utc_now()),
            )
        except sqlite3.IntegrityError as error:
            raise PolyglotError("this content is already imported for the selected language") from error
        self.connection.commit()
        return int(cursor.lastrowid)

    def _known_terms(self, profile_id: int) -> set[str]:
        rows = self.connection.execute(
            "SELECT phrase FROM phrases WHERE profile_id=? AND repetitions>0",
            (profile_id,),
        ).fetchall()
        return {token for row in rows for token in tokenize(row["phrase"])}

    def _content_summary(self, profile: dict[str, Any], item: dict[str, Any]) -> dict[str, Any]:
        terms = tokenize(item["body"])
        unique = set(terms)
        known = self._known_terms(profile["id"])
        ratio = sum(token in known for token in terms) / len(terms) if terms else 0.0
        item["coverage"] = round(ratio, 3)
        item["unique_terms"] = len(unique)
        item["unknown_terms"] = sorted(unique - known)[:30]
        item["in_comprehensible_band"] = 0.70 <= ratio <= 0.90
        item["coverage_note"] = (
            "rough character-level estimate for compact-script text (CJK/Thai)"
            if any(_is_compact_script(char) for char in item["body"])
            else "rough token estimate based on reviewed phrase cards"
        )
        return item

    def list_content(self, profile: dict[str, Any]) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            "SELECT * FROM content WHERE profile_id=? ORDER BY created_at DESC",
            (profile["id"],),
        ).fetchall()
        return [self._content_summary(profile, dict(row)) for row in rows]

    def get_content(self, profile: dict[str, Any], content_id: int) -> dict[str, Any]:
        row = self.connection.execute(
            "SELECT * FROM content WHERE profile_id=? AND id=?",
            (profile["id"], content_id),
        ).fetchone()
        if row is None:
            raise PolyglotError(f"content item not found: {content_id}")
        return self._content_summary(profile, dict(row))

    def recommend_content(self, profile: dict[str, Any], limit: int = 10) -> list[dict[str, Any]]:
        items = self.list_content(profile)
        items.sort(key=lambda item: (
            0 if item["in_comprehensible_band"] else 1,
            abs(item["coverage"] - 0.80), item["created_at"],
        ))
        return items[:max(1, min(limit, 100))]

    def add_phrase(
        self, profile: dict[str, Any], phrase: str, translation: str,
        context: str = "", source: str = "",
        tags: Iterable[str] = (), content_id: int | None = None,
        personal_example: str = "", frequency_rank: int | None = None,
    ) -> int:
        phrase, translation = normalize_text(phrase), normalize_text(translation)
        if not phrase or not translation:
            raise PolyglotError("phrase and translation are required")
        if content_id is not None:
            self.get_content(profile, content_id)
        if frequency_rank is not None and (
            isinstance(frequency_rank, bool) or not isinstance(frequency_rank, int) or frequency_rank < 1
        ):
            raise PolyglotError("frequency rank must be a positive integer")
        now = utc_now()
        try:
            cursor = self.connection.execute(
                """
                INSERT INTO phrases(profile_id,content_id,phrase,translation,context,
                    source,tags_json,personal_example,frequency_rank,
                    due_on,created_at,updated_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (profile["id"], content_id, phrase, translation, context,
                 source, json.dumps(list(tags), ensure_ascii=False),
                 personal_example.strip(), frequency_rank, date.today().isoformat(), now, now),
            )
        except sqlite3.IntegrityError as error:
            raise PolyglotError("this phrase and context already exist for the selected language") from error
        self.connection.commit()
        return int(cursor.lastrowid)

    def list_phrases(
        self, profile: dict[str, Any], due_only: bool = False, limit: int = 100,
    ) -> list[dict[str, Any]]:
        query, params = "SELECT * FROM phrases WHERE profile_id=?", [profile["id"]]
        if due_only:
            query += " AND due_on<=?"
            params.append(date.today().isoformat())
        query += " ORDER BY CASE WHEN frequency_rank IS NULL THEN 1 ELSE 0 END, frequency_rank, due_on,created_at LIMIT ?"
        params.append(max(1, min(limit, 500)))
        rows = self.connection.execute(query, params).fetchall()
        result = []
        for row in rows:
            item = dict(row)
            item["tags"] = json.loads(item.pop("tags_json"))
            result.append(item)
        return result

    def record_review(self, phrase_id: int, rating: int) -> dict[str, Any]:
        if isinstance(rating, bool) or not isinstance(rating, int) or not 0 <= rating <= 5:
            raise PolyglotError("review rating must be an integer from 0 to 5")
        row = self.connection.execute("SELECT * FROM phrases WHERE id=?", (phrase_id,)).fetchone()
        if row is None:
            raise PolyglotError(f"phrase card not found: {phrase_id}")
        old_interval = int(row["interval_days"])
        repetitions, ease, lapses = int(row["repetitions"]), float(row["ease"]), int(row["lapses"])
        if rating < 3:
            repetitions, interval, lapses = 0, 1, lapses + 1
            ease = max(1.3, ease - (0.20 if rating <= 1 else 0.15))
        else:
            interval = 1 if repetitions == 0 else 3 if repetitions == 1 else max(
                1, int(round(old_interval * ease * (1.15 if rating == 5 else 1.0)))
            )
            repetitions += 1
            if rating == 3:
                ease = max(1.3, ease - 0.05)
            elif rating == 5:
                ease = min(3.0, ease + 0.10)
        due = (date.today() + timedelta(days=interval)).isoformat()
        now = utc_now()
        self.connection.execute(
            """UPDATE phrases SET ease=?,interval_days=?,repetitions=?,lapses=?,
               due_on=?,last_reviewed_at=?,updated_at=? WHERE id=?""",
            (ease, interval, repetitions, lapses, due, now, now, phrase_id),
        )
        self.connection.execute(
            """INSERT INTO review_events(phrase_id,rating,previous_interval,next_interval,due_on,created_at)
               VALUES(?,?,?,?,?,?)""",
            (phrase_id, rating, old_interval, interval, due, now),
        )
        self.connection.commit()
        return {
            "phrase_id": phrase_id, "rating": rating, "interval_days": interval,
            "repetitions": repetitions, "lapses": lapses, "ease": round(ease, 2),
            "due_on": due, "status": "learning" if repetitions < 2 else "reviewed",
        }

    def due_count(self, profile: dict[str, Any]) -> int:
        row = self.connection.execute(
            "SELECT COUNT(*) AS count FROM phrases WHERE profile_id=? AND due_on<=?",
            (profile["id"], date.today().isoformat()),
        ).fetchone()
        return int(row["count"])

    def log_session(
        self, profile: dict[str, Any], minutes: int, mode: str,
        notes: str = "", score: int | None = None,
    ) -> int:
        if mode not in SESSION_MODES:
            raise PolyglotError(f"session mode must be one of: {', '.join(SESSION_MODES)}")
        if isinstance(minutes, bool) or not 1 <= minutes <= 1440:
            raise PolyglotError("session minutes must be between 1 and 1440")
        if score is not None and (isinstance(score, bool) or not 0 <= score <= 5):
            raise PolyglotError("session score must be an integer from 0 to 5")
        cursor = self.connection.execute(
            """INSERT INTO sessions(profile_id,mode,minutes,notes,score,created_at)
               VALUES(?,?,?,?,?,?)""",
            (profile["id"], mode, minutes, notes, score, utc_now()),
        )
        self.connection.commit()
        return int(cursor.lastrowid)

    def session_plan(self, profile: dict[str, Any]) -> list[dict[str, Any]]:
        total, due = int(profile["daily_minutes"]), self.due_count(profile)
        beginner = profile["current_level"] in ("A0", "A1", "A2")
        review_weight = min(0.35, 0.15 + due * 0.005)
        weights = (
            [0.40, 0.25, review_weight, 0.10, 0.05]
            if beginner else [0.30, 0.20, review_weight, 0.25, 0.05]
        )
        remainder_weight = 1.0 - sum(weights)
        weights[0] += remainder_weight * (0.60 if beginner else 0.45)
        weights[3] += remainder_weight * (0.40 if beginner else 0.55)
        raw = [total * weight for weight in weights]
        minutes = [int(value) for value in raw]
        remainder = total - sum(minutes)
        order = sorted(range(len(raw)), key=lambda i: raw[i] - minutes[i], reverse=True)
        for index in order[:remainder]:
            minutes[index] += 1
        tasks = [
            ("reading", "Прочитать текст и сохранить 2–5 полезных фраз"),
            ("writing", "Составить собственный короткий текст с новыми выражениями"),
            ("review", f"Повторить карточки с учётом контекста ({due} ожидают)"),
            ("analysis", "Разобрать грамматику, написание и структуру примеров"),
            ("reflection", "Отметить, что стало легче и какие письменные навыки требуют практики"),
        ]
        if profile.get("tonal_language"):
            tasks[3] = (tasks[3][0], tasks[3][1] + "; сохраняйте тоновые знаки в письменной транскрипции")
        if profile.get("romanization_bridge"):
            tasks[0] = (tasks[0][0], tasks[0][1] + "; постепенно переходите на родную письменность")
        if profile.get("orthography_focus"):
            tasks[3] = (tasks[3][0], tasks[3][1] + f"; фокус: {profile['orthography_focus']}")
        return [
            {"mode": mode, "minutes": amount, "task": task}
            for (mode, task), amount in zip(tasks, minutes) if amount > 0
        ]

    def report(self, profile: dict[str, Any]) -> dict[str, Any]:
        counts = self.connection.execute(
            """SELECT COUNT(*) AS total,
                SUM(CASE WHEN repetitions>0 THEN 1 ELSE 0 END) AS reviewed,
                SUM(CASE WHEN repetitions>=2 THEN 1 ELSE 0 END) AS consolidated
               FROM phrases WHERE profile_id=?""",
            (profile["id"],),
        ).fetchone()
        cutoff = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        sessions = self.connection.execute(
            """SELECT COALESCE(SUM(minutes),0) AS minutes,COUNT(*) AS count
               FROM sessions WHERE profile_id=? AND created_at>=?""",
            (profile["id"], cutoff),
        ).fetchone()
        content_count = self.connection.execute(
            "SELECT COUNT(*) AS count FROM content WHERE profile_id=?", (profile["id"],)
        ).fetchone()["count"]
        lifetime = self.connection.execute(
            "SELECT COALESCE(SUM(minutes),0) AS minutes FROM sessions WHERE profile_id=?",
            (profile["id"],),
        ).fetchone()
        total_minutes = int(lifetime["minutes"] or 0)
        total_hours = total_minutes / 60
        if total_minutes == 0:
            phase = "setup"
        elif total_hours < 10:
            phase = "written_foundation"
        elif total_hours < 40:
            phase = "comprehensible_input"
        elif total_hours < 100:
            phase = "guided_output"
        elif total_hours < 300:
            phase = "authentic_content"
        else:
            phase = "automation"
        return {
            "profile": profile, "content_items": int(content_count),
            "phrase_cards": int(counts["total"] or 0),
            "reviewed_cards": int(counts["reviewed"] or 0),
            "consolidated_cards": int(counts["consolidated"] or 0),
            "due_cards": self.due_count(profile), "known_terms": len(self._known_terms(profile["id"])),
            "last_7_days_minutes": int(sessions["minutes"] or 0),
            "last_7_days_sessions": int(sessions["count"] or 0),
            "total_study_minutes": total_minutes,
            "total_study_hours": round(total_hours, 2),
            "learning_phase": phase,
            "phase_note": "Exposure-hour phases are planning heuristics, not proficiency predictions.",
            "script_guidance": script_learning_notes(profile),
        }

    def export_profile(self, profile: dict[str, Any]) -> dict[str, Any]:
        def rows(table: str) -> list[dict[str, Any]]:
            return [dict(row) for row in self.connection.execute(
                f"SELECT * FROM {table} WHERE profile_id=? ORDER BY id", (profile["id"],)
            )]
        return {
            "schema_version": SCHEMA_VERSION, "exported_at": utc_now(),
            "profile": profile, "content": rows("content"),
            "phrases": rows("phrases"), "sessions": rows("sessions"),
        }


def run_review(
    store: PolyglotStore, profile: dict[str, Any], limit: int = 10,
    fixed_rating: int | None = None, input_fn: Callable[[str], str] = input,
    output_fn: Callable[[str], None] = print,
) -> int:
    queue = store.list_phrases(profile, due_only=True, limit=limit)
    if not queue:
        output_fn("Карточек к повторению нет. Добавьте фразы из понятного материала.")
        return 0
    reviewed = 0
    for card in queue:
        output_fn("")
        output_fn(f"ВСПОМНИ: {card['translation']}")
        if card["context"]:
            output_fn(f"Контекст: {card['context']}")
        if fixed_rating is None:
            input_fn("Вспомните или запишите ответ, затем нажмите Enter… ")
        output_fn(f"Ответ: {card['phrase']}")
        if card.get("personal_example"):
            output_fn(f"Личный пример: {card['personal_example']}")
        rating = fixed_rating
        if rating is None:
            while True:
                raw = input_fn("Оценка 0–5 (0 = не вспомнил, 5 = легко): ").strip()
                try:
                    parsed = int(raw)
                    if 0 <= parsed <= 5:
                        rating = parsed
                        break
                except ValueError:
                    pass
                output_fn("Введите целое число от 0 до 5.")
        result = store.record_review(int(card["id"]), int(rating))
        output_fn(f"Следующее повторение: {result['due_on']} (интервал {result['interval_days']} дн.)")
        reviewed += 1
    return reviewed


def _read_content_file(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as error:
        raise PolyglotError(f"cannot read content file {path}: {error}") from error
    return clean_subtitles(text) if path.suffix.casefold() in (".srt", ".vtt") else text


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="reaper polyglot",
        description="Local-first immersion, contextual phrase memory and adaptive planning.",
    )
    parser.add_argument("--db", help="SQLite database path (default: ~/.reaper/polyglot.sqlite3)")
    parser.add_argument("--target", help="target profile when several languages are configured")
    commands = parser.add_subparsers(dest="command", required=True)

    init = commands.add_parser("init", help="create or update a language profile")
    init.add_argument("language", help="target language, e.g. English, Japanese or Français")
    init.add_argument("--native", required=True)
    init.add_argument("--level", default="A0", choices=CEFR_LEVELS)
    init.add_argument("--goal", default="")
    init.add_argument("--minutes", type=int, default=45)
    init.add_argument("--code", default="", help="optional language code, e.g. es, ja, zh, ko")
    init.add_argument("--script", choices=SCRIPT_FAMILIES, default="auto")
    tonal = init.add_mutually_exclusive_group()
    tonal.add_argument("--tonal", dest="tonal_language", action="store_true")
    tonal.add_argument("--non-tonal", dest="tonal_language", action="store_false")
    init.set_defaults(tonal_language=None)
    init.add_argument("--romanization-bridge", choices=("on", "off"), default=None)
    init.add_argument("--orthography-focus", default="")
    commands.add_parser("profile", help="list configured language profiles")

    content = commands.add_parser("content", help="manage contextual learning material")
    content_commands = content.add_subparsers(dest="content_command", required=True)
    add_content = content_commands.add_parser("add", help="import UTF-8 text, Markdown, SRT or VTT")
    add_content.add_argument("file", type=Path)
    add_content.add_argument("--title", default="")
    add_content.add_argument("--kind", choices=CONTENT_KINDS, default="text")
    add_content.add_argument("--level", default="", choices=("",) + CEFR_LEVELS)
    add_content.add_argument("--translation", default="")
    add_content.add_argument("--source", default="")
    content_commands.add_parser("list", help="list imported material")

    phrase = commands.add_parser("phrase", help="manage phrase cards")
    phrase_commands = phrase.add_subparsers(dest="phrase_command", required=True)
    add_phrase = phrase_commands.add_parser("add", help="add phrase, translation and context")
    add_phrase.add_argument("phrase")
    add_phrase.add_argument("--translation", required=True)
    add_phrase.add_argument("--context", default="")
        add_phrase.add_argument("--source", default="")
    add_phrase.add_argument("--content-id", type=int)
    add_phrase.add_argument("--personal-example", default="", help="a sentence you can use about your own life")
    add_phrase.add_argument("--frequency-rank", type=int, help="optional manually supplied frequency rank")
    add_phrase.add_argument("--tag", action="append", default=[])
    list_phrase = phrase_commands.add_parser("list", help="list phrase cards")
    list_phrase.add_argument("--due", action="store_true")
    list_phrase.add_argument("--limit", type=int, default=100)

    plan = commands.add_parser("plan", help="build the daily adaptive study plan")
    plan.add_argument("--minutes", type=int, help="temporary override of daily minutes")
    suggest = commands.add_parser("suggest", help="rank content by estimated comprehensibility")
    suggest.add_argument("--limit", type=int, default=10)
    review = commands.add_parser("review", help="run an interactive spaced-repetition session")
    review.add_argument("--limit", type=int, default=10)
    review.add_argument("--rating", type=int, help="apply a fixed rating to each due card")
    session = commands.add_parser("session", help="record a completed practice session")
    session.add_argument("--minutes", type=int, required=True)
    session.add_argument("--mode", choices=SESSION_MODES, required=True)
    session.add_argument("--notes", default="")
    session.add_argument("--score", type=int, choices=range(0, 6))
    practice = commands.add_parser("practice", help="record a written composition attempt")
    practice.add_argument("--mode", choices=("writing",), default="writing")
    practice.add_argument("--minutes", type=int, default=5)
    practice.add_argument("--score", type=int, choices=range(0, 6))
    practice.add_argument("--notes", default="")
    commands.add_parser("report", help="show progress and pending reviews")
    export = commands.add_parser("export", help="export a profile as JSON")
    export.add_argument("--output", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        with PolyglotStore(args.db) as store:
            if args.command == "init":
                profile = store.create_profile(
                    args.language, args.native, args.level, args.goal, args.minutes,
                    language_code=args.code, script_family=args.script,
                    tonal_language=args.tonal_language,
                    romanization_bridge=(None if args.romanization_bridge is None else args.romanization_bridge == "on"),
                    orthography_focus=args.orthography_focus,
                )
                print(
                    f"Профиль настроен: {profile['target_language']} ({profile['current_level']}), "
                    f"цель: {profile['goal'] or 'не задана'}"
                )
                return 0
            if args.command == "profile":
                profiles = store.list_profiles()
                if not profiles:
                    print("Профилей пока нет. Создайте первый: reaper polyglot init English --native Russian")
                for profile in profiles:
                    print(
                        f"{profile['target_language']} ← {profile['native_language']} | "
                        f"{profile['current_level']} | {profile['daily_minutes']} мин/день | "
                        f"{profile['script_family']} | "
                        f"{'тональный' if profile['tonal_language'] else 'нетональный'} | "
                        f"транслитерация: {'вкл.' if profile['romanization_bridge'] else 'выкл.'} | "
                        f"{profile['goal'] or 'цель не задана'}"
                    )
                    for note in script_learning_notes(profile):
                        print(f"  подсказка: {note}")
                return 0

            profile = store.get_profile(args.target)
            if args.command == "content":
                if args.content_command == "add":
                    body = _read_content_file(args.file)
                    content_id = store.add_content(
                        profile, args.title or args.file.stem, body, args.kind,
                        args.translation, args.source or str(args.file), args.level,
                    )
                    print(f"Материал импортирован: id={content_id}, токенов={len(tokenize(body))}")
                else:
                    items = store.list_content(profile)
                    if not items:
                        print("Материалов нет. Импортируйте .txt, .md, .srt или .vtt файл.")
                    for item in items:
                        print(
                            f"#{item['id']} [{item['kind']}] {item['title']} | {item['word_count']} токенов | "
                            f"покрытие ~{item['coverage']:.0%} | {item['level'] or 'уровень не указан'}"
                        )
                return 0
            if args.command == "phrase":
                if args.phrase_command == "add":
                    card_id = store.add_phrase(
                        profile, args.phrase, args.translation, args.context,
                        args.source, args.tag, args.content_id,
                        args.personal_example, args.frequency_rank,
                    )
                    print(f"Фраза добавлена: id={card_id}; первое повторение назначено на сегодня.")
                else:
                    cards = store.list_phrases(profile, args.due, args.limit)
                    if not cards:
                        print("Нет карточек к повторению." if args.due else "Карточек пока нет.")
                    for card in cards:
                        print(
                            f"#{card['id']} {card['phrase']} — {card['translation']} | "
                            f"повторений: {card['repetitions']} | следующее: {card['due_on']} | "
                            f"частотный ранг: {card['frequency_rank'] or '—'}"
                        )
                return 0
            if args.command == "plan":
                if args.minutes is not None:
                    if not 5 <= args.minutes <= 240:
                        raise PolyglotError("plan minutes must be between 5 and 240")
                    profile = dict(profile)
                    profile["daily_minutes"] = args.minutes
                tasks = store.session_plan(profile)
                print(f"План на день: {profile['target_language']} · {profile['daily_minutes']} минут")
                for task in tasks:
                    print(f"  {task['minutes']:>3} мин · {task['mode']:<12} {task['task']}")
                return 0
            if args.command == "suggest":
                items = store.recommend_content(profile, args.limit)
                if not items:
                    print("Сначала импортируйте понятный текст, диалог или субтитры.")
                for item in items:
                    label = "подходит 70–90%" if item["in_comprehensible_band"] else "вне целевого диапазона"
                    print(
                        f"#{item['id']} {item['title']} — ~{item['coverage']:.0%} ({label}); "
                        f"{item['coverage_note']}"
                    )
                return 0
            if args.command == "review":
                if args.limit < 1:
                    raise PolyglotError("review limit must be positive")
                if args.rating is not None and not 0 <= args.rating <= 5:
                    raise PolyglotError("review rating must be from 0 to 5")
                count = run_review(store, profile, args.limit, args.rating)
                print(f"Повторено карточек: {count}")
                return 0
            if args.command == "session":
                session_id = store.log_session(profile, args.minutes, args.mode, args.notes, args.score)
                print(f"Сессия сохранена: #{session_id} · {args.minutes} мин · {args.mode}")
                return 0
            if args.command == "practice":
                notes = args.notes or input(
                    f"Коротко зафиксируйте, что вы сказали/написали на {profile['target_language']}: "
                ).strip()
                session_id = store.log_session(profile, args.minutes, args.mode, notes, args.score)
                print(f"Практика сохранена: #{session_id} · {args.minutes} мин · {args.mode}")
                return 0
            if args.command == "report":
                data = store.report(profile)
                print(f"Язык: {profile['target_language']} ({profile['current_level']})")
                print(f"Материалы: {data['content_items']}")
                print(
                    f"Карточки: {data['phrase_cards']} · повторялись: {data['reviewed_cards']} · "
                    f"закреплены (2+ повторения): {data['consolidated_cards']}"
                )
                print(f"Ожидают повторения: {data['due_cards']} · известных токенов: {data['known_terms']}")
                print(f"Этап: {data['learning_phase']} · всего практики: {data['total_study_hours']} ч")
                for note in data["script_guidance"]:
                    print(f"Подсказка: {note}")
                print(
                    f"За 7 дней: {data['last_7_days_sessions']} сессий · "
                    f"{data['last_7_days_minutes']} минут практики"
                )
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
    except (PolyglotError, OSError, sqlite3.Error) as error:
        print(f"reaper polyglot: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
