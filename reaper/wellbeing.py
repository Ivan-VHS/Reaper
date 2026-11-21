"""Offline, transcript-grounded mental wellbeing awareness reference.

This module is educational only. It does not screen, diagnose, score risk, or
recommend treatment. Missing transcript sections remain marked as unavailable.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

RESOURCE_PATH = Path(__file__).resolve().parents[1] / "data" / "wellbeing" / "depression-awareness.v1.json"
MAX_RESOURCE_BYTES = 256 * 1024
ALLOWED_EVIDENCE = {"transcript_excerpt", "insufficient_transcript"}


class WellbeingReferenceError(ValueError):
    """Invalid or unsafe wellbeing reference bundle."""


def load_reference(path: Path = RESOURCE_PATH) -> dict[str, Any]:
    try:
        if path.stat().st_size > MAX_RESOURCE_BYTES:
            raise WellbeingReferenceError("wellbeing reference exceeds the 256 KiB limit")
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise WellbeingReferenceError(f"cannot read wellbeing reference: {error}") from error
    except (UnicodeError, json.JSONDecodeError) as error:
        raise WellbeingReferenceError(f"invalid wellbeing reference JSON: {error}") from error

    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise WellbeingReferenceError("unsupported wellbeing reference schema_version")
    source = payload.get("source")
    coverage = payload.get("transcript_coverage")
    topics = payload.get("topics")
    guardrails = payload.get("guardrails")
    if not isinstance(source, dict) or not source.get("video_url", "").startswith("https://www.youtube.com/watch?v="):
        raise WellbeingReferenceError("source provenance is missing or invalid")
    if not isinstance(coverage, dict) or coverage.get("missing_middle") is not True:
        raise WellbeingReferenceError("the unavailable middle transcript segment must remain explicit")
    segments = coverage.get("available_segments")
    if not isinstance(segments, list) or not segments:
        raise WellbeingReferenceError("at least one transcript segment is required")
    for segment in segments:
        if (not isinstance(segment, dict)
                or type(segment.get("start_seconds")) is not int
                or type(segment.get("end_seconds")) is not int
                or segment["start_seconds"] < 0
                or segment["end_seconds"] <= segment["start_seconds"]):
            raise WellbeingReferenceError("transcript segment has invalid time bounds")
    if not isinstance(topics, list) or not topics:
        raise WellbeingReferenceError("topic catalogue is empty")
    seen: set[str] = set()
    for topic in topics:
        if not isinstance(topic, dict):
            raise WellbeingReferenceError("topic entries must be objects")
        topic_id = topic.get("id")
        if not isinstance(topic_id, str) or not topic_id or topic_id in seen:
            raise WellbeingReferenceError("topic IDs must be non-empty and unique")
        seen.add(topic_id)
        if topic.get("evidence_status") not in ALLOWED_EVIDENCE:
            raise WellbeingReferenceError(f"topic {topic_id!r} has an unknown evidence status")
        if not isinstance(topic.get("summary"), str) or not topic["summary"].strip():
            raise WellbeingReferenceError(f"topic {topic_id!r} has no summary")
        timestamps = topic.get("timestamps_seconds")
        if not isinstance(timestamps, list) or any(type(value) is not int or value < 0 for value in timestamps):
            raise WellbeingReferenceError(f"topic {topic_id!r} has invalid timestamps")
    missing_topic = next((row for row in topics if row["id"] == "antidepressant-myths"), None)
    if missing_topic is not None and (missing_topic["evidence_status"] != "insufficient_transcript"
                                      or missing_topic["timestamps_seconds"]):
        raise WellbeingReferenceError("antidepressant myths must remain unverified without transcript evidence")
    if not isinstance(guardrails, list) or len(guardrails) < 6:
        raise WellbeingReferenceError("minimum safety guardrails are missing")
    safety_text = " ".join(item for item in guardrails if isinstance(item, str)).casefold()
    for required in ("не медичний", "не проводити самодіагностику", "не призначати", "домислами"):
        if required not in safety_text:
            raise WellbeingReferenceError(f"required safety boundary is missing: {required}")
    return payload


def get_topic(topic_id: str, path: Path = RESOURCE_PATH) -> dict[str, Any]:
    payload = load_reference(path)
    for topic in payload["topics"]:
        if topic["id"] == topic_id:
            return topic
    raise KeyError(f"unknown wellbeing topic: {topic_id}")


def format_catalog(payload: dict[str, Any]) -> str:
    source = payload["source"]
    lines = [
        "Mental Wellbeing & Depression Awareness v1",
        f"Source: {source['channel']} — {source['title']}",
        f"Published: {source['published_at']} | Duration: {source['duration']}",
        "Transcript coverage: 00:00–00:07:55 and 01:17:16–01:19:53; middle unavailable.",
        "",
    ]
    for topic in payload["topics"]:
        status = topic["evidence_status"].replace("_", " ")
        lines.append(f"- {topic['id']} [{status}]: {topic['title']}")
    lines.extend([
        "",
        "Educational reference only: no diagnosis, screening, risk scoring or treatment advice.",
        "Medication decisions must be discussed with a qualified prescriber.",
    ])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read the offline mental wellbeing awareness catalogue.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--catalog", action="store_true", help="show all source-grounded topics")
    group.add_argument("--topic", metavar="ID", help="show one topic by stable ID")
    parser.add_argument("--json", action="store_true", help="emit structured JSON")
    args = parser.parse_args(argv)
    try:
        payload = load_reference()
        if args.topic:
            selected = get_topic(args.topic)
            result: Any = {"source": payload["source"], "topic": selected}
            text = json.dumps(result, ensure_ascii=False, indent=2) if args.json else (
                f"{selected['title']}\n{selected['summary']}\n"
                f"Evidence: {selected['evidence_status']}\n"
                f"Video: {payload['source']['video_url']}"
            )
        else:
            result = payload
            text = json.dumps(result, ensure_ascii=False, indent=2) if args.json else format_catalog(payload)
    except (WellbeingReferenceError, KeyError) as error:
        parser.exit(2, f"reaper wellbeing: {error}\n")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
