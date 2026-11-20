"""Local-first language immersion workspace for Reaper.

The module combines contextual vocabulary, an approximate comprehensible-input
estimator, deterministic spaced repetition, four-pillar study plans, and
session analytics. It deliberately does not claim to assess pronunciation:
speech confidence and correction notes are learner-reported until an ASR
provider is explicitly integrated.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
import unicodedata
from datetime import date, timedelta
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
DEFAULT_STORE = Path.home() / ".reaper" / "polyglot.json"
MAX_STORE_BYTES = 8 * 1024 * 1024
MAX_TEXT_LENGTH = 100_000
MAX_DAILY_MINUTES = 240

PILLARS = {
    "audio_visual": {
        "label": "Audio and visual input",
        "weight": 30,
        "task": "Listen to a short clip with transcript, captions, or visual context.",
    },
    "contextual_reading": {
        "label": "Contextual reading",
        "weight": 25,
        "task": "Read a short passage; save useful phrases, not isolated word lists.",
    },
    "spaced_repetition": {
        "label": "Contextual retention",
        "weight": 20,
        "task": "Review due phrase cards, then create one personal example.",
    },
    "speaking_feedback": {
        "label": "Speaking and feedback",
        "weight": 25,
        "task": "Retell the content or record a short monologue; note one correction.",
    },
}

RATINGS = {"again", "hard", "good", "easy"}
LEVELS = {"A0", "A1", "A2", "B1", "B2", "C1", "C2"}
SCRIPT_CHOICES = {
    "auto", "latin", "cyrillic", "arabic", "devanagari", "han",
    "japanese", "hangul", "thai", "other",
}
TONAL_LANGUAGE_CODES = {"zh", "yue", "vi", "th"}
COMPACT_SCRIPTS = {"han", "japanese", "hangul", "thai"}

LANGUAGE_SCRIPTS = {
    "zh": "han", "cmn": "han", "yue": "han",
    "ja": "japanese", "jpn": "japanese",
    "ko": "hangul", "kor": "hangul",
    "ar": "arabic", "ara": "arabic", "fa": "arabic", "ur": "arabic",
    "hi": "devanagari", "hin": "devanagari", "mr": "devanagari",
    "th": "thai", "tha": "thai",
    "ru": "cyrillic", "uk": "cyrillic", "bg": "cyrillic",
    "sr": "cyrillic", "mk": "cyrillic", "be": "cyrillic",
}
LANGUAGE_NAMES = {
    "chinese": "han", "mandarin": "han", "cantonese": "han",
    "japanese": "japanese", "korean": "hangul", "arabic": "arabic",
    "hindi": "devanagari", "thai": "thai", "russian": "cyrillic",
    "ukrainian": "cyrillic", "bulgarian": "cyrillic", "serbian": "cyrillic",
}

class PolyglotError(ValueError):
    """Invalid profile, workspace, phrase, or study operation."""


def _today(value: date | str | None = None) -> date:
    if value is None:
        return date.today()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError) as error:
        raise PolyglotError("date must use YYYY-MM-DD format") from error


def _bounded_text(value: str, label: str, maximum: int = MAX_TEXT_LENGTH) -> str:
    if not isinstance(value, str):
        raise PolyglotError(f"{label} must be text")
    value = value.strip()
    if not value:
        raise PolyglotError(f"{label} cannot be empty")
    if len(value) > maximum:
        raise PolyglotError(f"{label} exceeds {maximum} characters")
    return value


def _language_script(code: str, name: str) -> str:
    key = code.strip().lower().split("-")[0]
    if key in LANGUAGE_SCRIPTS:
        return LANGUAGE_SCRIPTS[key]
    return LANGUAGE_NAMES.get(name.strip().lower(), "latin")


def detect_script(text: str) -> str:
    """Return the dominant script family in a sample, not a language identity."""
    counts = {key: 0 for key in (
        "han", "japanese", "hangul", "arabic", "devanagari",
        "cyrillic", "thai", "latin",
    )}
    for char in text[:20_000]:
        code = ord(char)
        if 0x3040 <= code <= 0x30FF:
            counts["japanese"] += 1
        elif 0x4E00 <= code <= 0x9FFF or 0x3400 <= code <= 0x4DBF:
            counts["han"] += 1
        elif 0xAC00 <= code <= 0xD7AF:
            counts["hangul"] += 1
        elif 0x0600 <= code <= 0x06FF or 0x0750 <= code <= 0x077F:
            counts["arabic"] += 1
        elif 0x0900 <= code <= 0x097F:
            counts["devanagari"] += 1
        elif 0x0400 <= code <= 0x052F:
            counts["cyrillic"] += 1
        elif 0x0E00 <= code <= 0x0E7F:
            counts["thai"] += 1
        elif "LATIN" in unicodedata.name(char, ""):
            counts["latin"] += 1
    if counts["japanese"] and counts["han"]:
        return "japanese"
    return max(counts, key=counts.get) if any(counts.values()) else "other"


def _letters(text: str) -> str:
    return "".join(
        char.casefold()
        for char in unicodedata.normalize("NFKC", text)
        if unicodedata.category(char).startswith("L")
    )


def _word_units(text: str) -> list[str]:
    return re.findall(r"[^\W_]+(?:['’][^\W_]+)*", unicodedata.normalize("NFKC", text).casefold())


def _script_advice(script: str, tonal: bool) -> list[str]:
    advice: list[str] = []
    if script in COMPACT_SCRIPTS:
        advice.append("Use native-script text with audio; whitespace word counts are not reliable for this script.")
    if script == "japanese":
        advice.append("Learn kana alongside listening; add kanji in recurring words and phrases.")
    elif script == "han":
        advice.append("Attach pronunciation and tone information to each new spoken word or phrase.")
    elif script == "hangul":
        advice.append("Pair Hangul syllable blocks with natural audio; watch sound changes across word boundaries.")
    elif script == "arabic":
        advice.append("Use fully vowelled examples at the beginning, then gradually remove reading aids.")
    elif script == "devanagari":
        advice.append("Learn the native script alongside sound; use transliteration only as a temporary bridge.")
    elif script == "cyrillic":
        advice.append("Pair spelling with stress marks and audio when stress is unpredictable.")
    if tonal:
        advice.append("Treat tone as part of the syllable: store and review pronunciation with every new phrase.")
    return advice


def _lexical_coverage(text: str, known_phrases: list[str], target_script: str) -> tuple[float, int, int, str]:
    observed_script = detect_script(text)
    compact = observed_script in COMPACT_SCRIPTS or target_script in COMPACT_SCRIPTS
    if compact:
        sample = _letters(text)
        if not sample:
            return 0.0, 0, 0, observed_script
        vocabulary = sorted(
            {_letters(item) for item in known_phrases if _letters(item)},
            key=lambda item: (-len(item), item),
        )
        covered = [False] * len(sample)
        for term in vocabulary:
            start = 0
            while True:
                index = sample.find(term, start)
                if index < 0:
                    break
                for position in range(index, index + len(term)):
                    covered[position] = True
                start = index + max(1, len(term))
        total = len(sample)
        known = sum(covered)
    else:
        units = _word_units(text)
        if not units:
            return 0.0, 0, 0, observed_script
        vocabulary: set[str] = set()
        for phrase in known_phrases:
            vocabulary.update(_word_units(phrase))
        total = len(units)
        known = sum(unit in vocabulary for unit in units)
    return known / total if total else 0.0, known, total, observed_script


class PolyglotWorkspace:
    """Persistent, local-first workspace for one target language."""

    def __init__(self, path: Path, data: dict[str, Any]) -> None:
        self.path = Path(path)
        self.data = data

    @classmethod
    def create(
        cls,
        path: str | Path = DEFAULT_STORE,
        *,
        target_language: str,
        language_code: str = "",
        support_language: str = "Russian",
        level: str = "A0",
        goal: str = "Everyday conversation",
        daily_minutes: int = 45,
        script: str = "auto",
        comprehension_target: float = 0.8,
        phonetic_focus: str = "",
        on_date: date | str | None = None,
    ) -> "PolyglotWorkspace":
        destination = Path(path).expanduser()
        if destination.exists():
            raise PolyglotError(f"workspace already exists: {destination}; refusing to overwrite it")
        target_language = _bounded_text(target_language, "target language", 120)
        support_language = _bounded_text(support_language, "support language", 120)
        if level not in LEVELS:
            raise PolyglotError(f"level must be one of {', '.join(sorted(LEVELS))}")
        if isinstance(daily_minutes, bool) or not isinstance(daily_minutes, int) or not 15 <= daily_minutes <= MAX_DAILY_MINUTES:
            raise PolyglotError("daily minutes must be an integer from 15 to 240")
        if script not in SCRIPT_CHOICES:
            raise PolyglotError(f"script must be one of {', '.join(sorted(SCRIPT_CHOICES))}")
        if not isinstance(comprehension_target, (int, float)) or not 0.7 <= comprehension_target <= 0.9:
            raise PolyglotError("comprehension target must be between 0.70 and 0.90")
        language_code = language_code.strip().lower()
        actual_script = _language_script(language_code, target_language) if script == "auto" else script
        tonal = language_code.split("-")[0] in TONAL_LANGUAGE_CODES or target_language.lower() in {"mandarin", "chinese", "vietnamese", "thai", "cantonese"}
        today = _today(on_date)
        data = {
            "schema_version": SCHEMA_VERSION,
            "profile": {
                "target_language": target_language,
                "language_code": language_code,
                "support_language": support_language,
                "level": level,
                "goal": _bounded_text(goal, "goal", 500),
                "daily_minutes": daily_minutes,
                "script_family": actual_script,
                "romanization_bridge": actual_script in COMPACT_SCRIPTS or actual_script in {"arabic", "devanagari"},
                "phonetic_focus": phonetic_focus.strip() or ("tones and syllable-level pronunciation" if tonal else "sound contrasts, stress, and connected speech"),
                "tonal_language": tonal,
                "comprehension_target": float(comprehension_target),
                "created_on": today.isoformat(),
            },
            "phrases": [],
            "content": [],
            "sessions": [],
        }
        workspace = cls(destination, data)
        workspace.save()
        return workspace

    @classmethod
    def load(cls, path: str | Path = DEFAULT_STORE) -> "PolyglotWorkspace":
        source = Path(path).expanduser()
        try:
            size = source.stat().st_size
            if size > MAX_STORE_BYTES:
                raise PolyglotError(f"workspace exceeds {MAX_STORE_BYTES} bytes")
            raw = source.read_text(encoding="utf-8")
            data = json.loads(raw)
        except OSError:
            raise
        except (UnicodeError, json.JSONDecodeError) as error:
            raise PolyglotError(f"cannot read workspace JSON: {error}") from error
        if not isinstance(data, dict) or data.get("schema_version") != SCHEMA_VERSION:
            raise PolyglotError("unsupported or malformed polyglot workspace schema")
        if not isinstance(data.get("profile"), dict):
            raise PolyglotError("workspace profile is missing")
        required_profile = {"target_language", "language_code", "support_language", "level", "goal", "daily_minutes", "script_family", "romanization_bridge", "phonetic_focus", "tonal_language", "comprehension_target", "created_on"}
        if not required_profile.issubset(data["profile"]):
            raise PolyglotError("workspace profile is incomplete")
        for key in ("phrases", "content", "sessions"):
            if not isinstance(data.get(key), list):
                raise PolyglotError(f"workspace {key} collection is malformed")
        return cls(source, data)

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(self.data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        if len(payload.encode("utf-8")) > MAX_STORE_BYTES:
            raise PolyglotError(f"workspace would exceed {MAX_STORE_BYTES} bytes")
        temp_name: str | None = None
        try:
            with tempfile.NamedTemporaryFile(
                "w", encoding="utf-8", newline="\n",
                dir=self.path.parent, prefix=self.path.name + ".", suffix=".tmp",
                delete=False,
            ) as temporary:
                temp_name = temporary.name
                temporary.write(payload)
                temporary.flush()
                os.fsync(temporary.fileno())
            Path(temp_name).replace(self.path)
        finally:
            if temp_name and Path(temp_name).exists():
                Path(temp_name).unlink()

    @property
    def profile(self) -> dict[str, Any]:
        return self.data["profile"]

    def configure(
        self,
        *,
        level: str | None = None,
        goal: str | None = None,
        daily_minutes: int | None = None,
        comprehension_target: float | None = None,
        romanization_bridge: bool | None = None,
        phonetic_focus: str | None = None,
    ) -> dict[str, Any]:
        if level is not None:
            if level not in LEVELS:
                raise PolyglotError(f"level must be one of {', '.join(sorted(LEVELS))}")
            self.profile["level"] = level
        if goal is not None:
            self.profile["goal"] = _bounded_text(goal, "goal", 500)
        if daily_minutes is not None:
            if isinstance(daily_minutes, bool) or not isinstance(daily_minutes, int) or not 15 <= daily_minutes <= MAX_DAILY_MINUTES:
                raise PolyglotError("daily minutes must be an integer from 15 to 240")
            self.profile["daily_minutes"] = daily_minutes
        if comprehension_target is not None:
            if not isinstance(comprehension_target, (int, float)) or not 0.7 <= comprehension_target <= 0.9:
                raise PolyglotError("comprehension target must be between 0.70 and 0.90")
            self.profile["comprehension_target"] = float(comprehension_target)
        if romanization_bridge is not None:
            if not isinstance(romanization_bridge, bool):
                raise PolyglotError("romanization bridge must be a boolean")
            self.profile["romanization_bridge"] = romanization_bridge
        if phonetic_focus is not None:
            self.profile["phonetic_focus"] = phonetic_focus.strip()
        return dict(self.profile)

    def _next_id(self, collection: str, prefix: str) -> str:
        return f"{prefix}-{len(self.data[collection]) + 1:06d}"

    def add_phrase(
        self,
        text: str,
        meaning: str,
        *,
        context: str = "",
        source: str = "",
        audio_ref: str = "",
        pronunciation: str = "",
        personal_example: str = "",
        tags: list[str] | None = None,
        frequency_rank: int | None = None,
        on_date: date | str | None = None,
    ) -> dict[str, Any]:
        target_text = _bounded_text(text, "phrase")
        for item in self.data["phrases"]:
            if _letters(item["text"]) == _letters(target_text):
                raise PolyglotError(f"phrase already exists as {item['id']}")
        if frequency_rank is not None and (isinstance(frequency_rank, bool) or not isinstance(frequency_rank, int) or not 1 <= frequency_rank <= 1_000_000):
            raise PolyglotError("frequency rank must be between 1 and 1000000")
        record = {
            "id": self._next_id("phrases", "phrase"),
            "text": target_text,
            "meaning": _bounded_text(meaning, "meaning"),
            "context": context.strip(),
            "source": source.strip(),
            "audio_ref": audio_ref.strip(),
            "pronunciation": pronunciation.strip(),
            "personal_example": personal_example.strip(),
            "tags": sorted({tag.strip() for tag in (tags or []) if tag.strip()}),
            "frequency_rank": frequency_rank,
            "ease_factor": 2.5,
            "interval_days": 0,
            "repetitions": 0,
            "review_count": 0,
            "last_reviewed": None,
            "due_on": _today(on_date).isoformat(),
        }
        self.data["phrases"].append(record)
        return record

    def add_content(
        self,
        title: str,
        text: str,
        *,
        source: str = "",
        audio_ref: str = "",
        notes: str = "",
        on_date: date | str | None = None,
    ) -> dict[str, Any]:
        sample = _bounded_text(text, "content")
        coverage = self.analyze_text(sample)
        record = {
            "id": self._next_id("content", "content"),
            "title": _bounded_text(title, "content title", 300),
            "text": sample,
            "source": source.strip(),
            "audio_ref": audio_ref.strip(),
            "notes": notes.strip(),
            "added_on": _today(on_date).isoformat(),
            "comprehension": coverage["coverage"],
            "comprehension_band": coverage["band"],
            "script_family": coverage["script_family"],
        }
        self.data["content"].append(record)
        return record

    def analyze_text(self, text: str) -> dict[str, Any]:
        sample = _bounded_text(text, "text to analyze")
        coverage, known, total, observed_script = _lexical_coverage(
            sample,
            [item["text"] for item in self.data["phrases"]],
            self.profile["script_family"],
        )
        target = float(self.profile["comprehension_target"])
        if total == 0:
            band = "insufficient_text"
            recommendation = "Add a longer text sample before estimating comprehension."
        elif coverage < target - 0.1:
            band = "too_hard"
            recommendation = "Choose a shorter or easier item, replay it with transcript and visual context, and ignore nonessential unknown words."
        elif coverage > target + 0.1:
            band = "too_easy"
            recommendation = "Increase difficulty gradually: use a longer passage, faster natural audio, or fewer support cues."
        else:
            band = "comprehensible"
            recommendation = "Good working range. Listen and read together, then retell the main idea."
        return {
            "coverage": round(coverage, 4),
            "known_units": known,
            "total_units": total,
            "target": target,
            "band": band,
            "script_family": observed_script,
            "is_heuristic": True,
            "recommendation": recommendation,
        }

    def due_phrases(self, on_date: date | str | None = None) -> list[dict[str, Any]]:
        today = _today(on_date)
        due = [item for item in self.data["phrases"] if date.fromisoformat(item["due_on"]) <= today]
        return sorted(due, key=lambda item: (item["due_on"], item["frequency_rank"] or 1_000_001, item["id"]))

    def review_phrase(
        self,
        phrase_id: str,
        rating: str,
        *,
        on_date: date | str | None = None,
    ) -> dict[str, Any]:
        if rating not in RATINGS:
            raise PolyglotError(f"rating must be one of {', '.join(sorted(RATINGS))}")
        phrase = next((item for item in self.data["phrases"] if item["id"] == phrase_id), None)
        if phrase is None:
            raise PolyglotError(f"unknown phrase id: {phrase_id}")
        today = _today(on_date)
        ease = float(phrase["ease_factor"])
        previous = int(phrase["interval_days"])
        repetitions = int(phrase["repetitions"])
        if rating == "again":
            ease = max(1.3, ease - 0.2)
            interval = 1
            repetitions = 0
        elif rating == "hard":
            ease = max(1.3, ease - 0.15)
            interval = max(1, round(previous * 1.2)) if repetitions else 1
            repetitions += 1
        elif rating == "good":
            interval = 1 if repetitions == 0 else 6 if repetitions == 1 else max(1, round(previous * ease))
            repetitions += 1
        else:
            ease += 0.15
            interval = 2 if repetitions == 0 else 8 if repetitions == 1 else max(2, round(previous * ease * 1.3))
            repetitions += 1
        phrase.update({
            "ease_factor": round(ease, 3),
            "interval_days": interval,
            "repetitions": repetitions,
            "review_count": int(phrase["review_count"]) + 1,
            "last_reviewed": today.isoformat(),
            "due_on": (today + timedelta(days=interval)).isoformat(),
            "last_rating": rating,
        })
        return phrase

    def log_session(
        self,
        pillar: str,
        minutes: int,
        *,
        comprehension: float | None = None,
        oral_confidence: int | None = None,
        notes: str = "",
        on_date: date | str | None = None,
    ) -> dict[str, Any]:
        if pillar not in PILLARS:
            raise PolyglotError(f"pillar must be one of {', '.join(PILLARS)}")
        if isinstance(minutes, bool) or not isinstance(minutes, int) or not 1 <= minutes <= 720:
            raise PolyglotError("session minutes must be an integer from 1 to 720")
        if comprehension is not None and (isinstance(comprehension, bool) or not isinstance(comprehension, (int, float)) or not 0 <= comprehension <= 1):
            raise PolyglotError("comprehension must be between 0 and 1")
        if oral_confidence is not None and (isinstance(oral_confidence, bool) or not isinstance(oral_confidence, int) or not 1 <= oral_confidence <= 5):
            raise PolyglotError("oral confidence must be an integer from 1 to 5")
        record = {
            "id": self._next_id("sessions", "session"),
            "date": _today(on_date).isoformat(),
            "pillar": pillar,
            "minutes": minutes,
            "comprehension": round(float(comprehension), 4) if comprehension is not None else None,
            "oral_confidence": oral_confidence,
            "notes": notes.strip(),
        }
        self.data["sessions"].append(record)
        return record

    def daily_plan(self, on_date: date | str | None = None) -> dict[str, Any]:
        today = _today(on_date)
        total = int(self.profile["daily_minutes"])
        due_count = len(self.due_phrases(today))
        # Largest-remainder allocation guarantees an exact total and at least
        # one minute for each pillar in the supported 15-minute minimum plan.
        raw = {key: total * item["weight"] / 100 for key, item in PILLARS.items()}
        minutes = {key: int(value) for key, value in raw.items()}
        remaining = total - sum(minutes.values())
        for key in sorted(raw, key=lambda item: (-(raw[item] - minutes[item]), item))[:remaining]:
            minutes[key] += 1
        tasks = []
        for key, details in PILLARS.items():
            task = details["task"]
            if key == "spaced_repetition":
                task = f"Review {due_count} due phrase card(s); add a personal example for one card."
            elif key == "audio_visual" and self.profile["tonal_language"]:
                task += " Keep tone and syllable pronunciation attached to each phrase."
            elif key == "contextual_reading" and self.profile["romanization_bridge"]:
                task += " Prefer native script; use transliteration only as a temporary bridge."
            elif key == "speaking_feedback":
                task += " Self-rate clarity from 1 to 5 and write down one correction; this is not automated speech scoring."
            tasks.append({
                "pillar": key,
                "label": details["label"],
                "minutes": minutes[key],
                "task": task,
            })
        return {
            "date": today.isoformat(),
            "target_language": self.profile["target_language"],
            "level": self.profile["level"],
            "total_minutes": total,
            "due_phrase_count": due_count,
            "comprehension_target": self.profile["comprehension_target"],
            "tasks": tasks,
        }

    def status(self, on_date: date | str | None = None) -> dict[str, Any]:
        total_minutes = sum(int(item["minutes"]) for item in self.data["sessions"])
        observations = [item["comprehension"] for item in self.data["sessions"] if item["comprehension"] is not None]
        average = sum(observations) / len(observations) if observations else None
        hours = total_minutes / 60
        if total_minutes == 0:
            phase = "setup"
        elif hours < 10:
            phase = "sound_foundation"
        elif hours < 40:
            phase = "comprehensible_input"
        elif hours < 100:
            phase = "guided_output"
        elif hours < 300:
            phase = "authentic_content"
        else:
            phase = "automation"
        today = _today(on_date)
        return {
            "profile": dict(self.profile),
            "phase": phase,
            "study_minutes": total_minutes,
            "study_hours": round(hours, 2),
            "phrase_count": len(self.data["phrases"]),
            "content_count": len(self.data["content"]),
            "session_count": len(self.data["sessions"]),
            "due_phrase_count": len(self.due_phrases(today)),
            "average_session_comprehension": round(average, 4) if average is not None else None,
            "script_guidance": _script_advice(
                self.profile["script_family"],
                bool(self.profile["tonal_language"]),
            ),
            "progress_model": "Exposure-hour phases are planning heuristics, not proficiency predictions.",
        }


def _json_default(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"cannot encode {type(value).__name__}")


def _add_store(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--store", type=Path, default=DEFAULT_STORE, help=f"workspace JSON path (default: {DEFAULT_STORE})")
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")


def _emit(payload: Any, as_json: bool, message: str = "") -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default))
    elif message:
        print(message)
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default))


def build_polyglot_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="reaper polyglot",
        description="Build a local, context-first language immersion workspace.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    init = commands.add_parser("init", help="create a target-language learning profile")
    _add_store(init)
    init.add_argument("--target-language", required=True)
    init.add_argument("--code", default="", help="optional ISO language code, e.g. es, ja, zh")
    init.add_argument("--support-language", default="Russian")
    init.add_argument("--level", choices=sorted(LEVELS), default="A0")
    init.add_argument("--goal", default="Everyday conversation")
    init.add_argument("--daily-minutes", type=int, default=45)
    init.add_argument("--script", choices=sorted(SCRIPT_CHOICES), default="auto")
    init.add_argument("--comprehension-target", type=float, default=0.8)
    init.add_argument("--phonetic-focus", default="")

    configure = commands.add_parser("configure", help="adjust level, goals, input target, or writing bridge")
    _add_store(configure)
    configure.add_argument("--level", choices=sorted(LEVELS), default=None)
    configure.add_argument("--goal", default=None)
    configure.add_argument("--daily-minutes", type=int, default=None)
    configure.add_argument("--comprehension-target", type=float, default=None)
    configure.add_argument("--romanization-bridge", choices=("on", "off"), default=None)
    configure.add_argument("--phonetic-focus", default=None)

    status = commands.add_parser("status", help="show learning progress and script guidance")
    _add_store(status)
    status.add_argument("--date", default=None)

    plan = commands.add_parser("plan", help="generate the four-pillar daily routine")
    _add_store(plan)
    plan.add_argument("--date", default=None)

    due = commands.add_parser("due", help="list phrase cards due for review")
    _add_store(due)
    due.add_argument("--date", default=None)

    phrase = commands.add_parser("add-phrase", help="save a contextual phrase card")
    _add_store(phrase)
    phrase.add_argument("--text", required=True)
    phrase.add_argument("--meaning", required=True)
    phrase.add_argument("--context", default="")
    phrase.add_argument("--source", default="")
    phrase.add_argument("--audio-ref", default="")
    phrase.add_argument("--pronunciation", default="")
    phrase.add_argument("--personal-example", default="")
    phrase.add_argument("--tags", nargs="*", default=[])
    phrase.add_argument("--frequency-rank", type=int, default=None)

    content = commands.add_parser("add-content", help="store a text/audio item and estimate its comprehensibility")
    _add_store(content)
    content.add_argument("--title", required=True)
    content.add_argument("--text", required=True)
    content.add_argument("--source", default="")
    content.add_argument("--audio-ref", default="")
    content.add_argument("--notes", default="")

    analyze = commands.add_parser("analyze", help="estimate known-vocabulary coverage in a passage")
    _add_store(analyze)
    source_group = analyze.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--text")
    source_group.add_argument("--file", type=Path)

    review = commands.add_parser("review", help="grade one due phrase card")
    _add_store(review)
    review.add_argument("--id", required=True)
    review.add_argument("--rating", required=True, choices=sorted(RATINGS))
    review.add_argument("--date", default=None)

    log = commands.add_parser("log", help="record a study session")
    _add_store(log)
    log.add_argument("--pillar", required=True, choices=list(PILLARS))
    log.add_argument("--minutes", type=int, required=True)
    log.add_argument("--comprehension", type=float, default=None)
    log.add_argument("--oral-confidence", type=int, default=None)
    log.add_argument("--notes", default="")
    log.add_argument("--date", default=None)
    return parser


def polyglot_main(argv: list[str] | None = None) -> int:
    parser = build_polyglot_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "init":
            workspace = PolyglotWorkspace.create(
                args.store,
                target_language=args.target_language,
                language_code=args.code,
                support_language=args.support_language,
                level=args.level,
                goal=args.goal,
                daily_minutes=args.daily_minutes,
                script=args.script,
                comprehension_target=args.comprehension_target,
                phonetic_focus=args.phonetic_focus,
            )
            payload = {"created": True, "store": str(workspace.path), "profile": workspace.profile}
            _emit(payload, args.json, f"Polyglot workspace created: {workspace.path}")
            return 0

        workspace = PolyglotWorkspace.load(args.store)
        if args.command == "configure":
            payload = workspace.configure(
                level=args.level,
                goal=args.goal,
                daily_minutes=args.daily_minutes,
                comprehension_target=args.comprehension_target,
                romanization_bridge=(
                    None if args.romanization_bridge is None
                    else args.romanization_bridge == "on"
                ),
                phonetic_focus=args.phonetic_focus,
            )
            workspace.save()
            _emit(payload, args.json, "Polyglot profile updated.")
        elif args.command == "status":
            payload = workspace.status(args.date)
            _emit(payload, args.json, f"{payload['profile']['target_language']}: {payload['phase']}; {payload['phrase_count']} phrase(s), {payload['due_phrase_count']} due, {payload['study_minutes']} study minute(s)")
        elif args.command == "plan":
            payload = workspace.daily_plan(args.date)
            _emit(payload, args.json, "\n".join(f"{item['minutes']:>3} min  {item['label']}: {item['task']}" for item in payload["tasks"]) + f"\nTotal: {payload['total_minutes']} min")
        elif args.command == "due":
            payload = workspace.due_phrases(args.date)
            _emit(payload, args.json, "\n".join(f"{item['id']}  {item['text']} — {item['meaning']} (due {item['due_on']})" for item in payload) or "No phrase cards due.")
        elif args.command == "add-phrase":
            payload = workspace.add_phrase(
                args.text, args.meaning, context=args.context, source=args.source,
                audio_ref=args.audio_ref, pronunciation=args.pronunciation,
                personal_example=args.personal_example, tags=args.tags,
                frequency_rank=args.frequency_rank,
            )
            workspace.save()
            _emit(payload, args.json, f"Saved {payload['id']}: {payload['text']} — {payload['meaning']}")
        elif args.command == "add-content":
            payload = workspace.add_content(
                args.title, args.text, source=args.source,
                audio_ref=args.audio_ref, notes=args.notes,
            )
            workspace.save()
            _emit(payload, args.json, f"Saved {payload['id']}: {payload['title']} ({payload['comprehension_band']}, {payload['comprehension']:.0%} estimated known coverage)")
        elif args.command == "analyze":
            text = args.text if args.text is not None else args.file.read_text(encoding="utf-8")
            payload = workspace.analyze_text(text)
            _emit(payload, args.json, f"{payload['band']}: {payload['coverage']:.0%} estimated known coverage. {payload['recommendation']}")
        elif args.command == "review":
            payload = workspace.review_phrase(args.id, args.rating, on_date=args.date)
            workspace.save()
            _emit(payload, args.json, f"{payload['id']} reviewed as {args.rating}; next review: {payload['due_on']}")
        elif args.command == "log":
            payload = workspace.log_session(
                args.pillar, args.minutes, comprehension=args.comprehension,
                oral_confidence=args.oral_confidence, notes=args.notes, on_date=args.date,
            )
            workspace.save()
            _emit(payload, args.json, f"Logged {payload['minutes']} min in {payload['pillar']}.")
        else:
            parser.error("unknown polyglot command")
        return 0
    except (PolyglotError, OSError) as error:
        print(f"reaper polyglot: {error}", file=sys.stderr)
        return 1
