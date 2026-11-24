"""Score incoming text for spam signals and return a review recommendation."""
from __future__ import annotations

import re
from typing import Any

from .common import require_array, require_text

_URL = re.compile(r"https?://\S+", re.IGNORECASE)


def run(payload: dict[str, Any]) -> dict[str, Any]:
    message = require_text(payload.get("text"), "text", allow_empty=True)
    links_raw = payload.get("links")
    if links_raw is None:
        links = _URL.findall(message)
    else:
        links = require_array(payload, "links")
        for index, link in enumerate(links):
            require_text(link, f"links[{index}]")
    letters = [character for character in message if character.isalpha()]
    uppercase_ratio = (
        sum(character.isupper() for character in letters) / len(letters)
        if letters else 0.0
    )
    banned = payload.get("banned_phrases", [])
    if not isinstance(banned, list) or any(not isinstance(item, str) for item in banned):
        raise ValueError("banned_phrases must be an array of text values")
    matched = [phrase for phrase in banned if phrase and phrase.casefold() in message.casefold()]
    score = 0
    signals: list[str] = []
    if len(links) > 3:
        score += 40
        signals.append("link_count_above_3")
    if uppercase_ratio > 0.75:
        score += 25
        signals.append("uppercase_ratio_above_0_75")
    if matched:
        score += 80
        signals.append("banned_phrase_match")
    action = "block" if score >= 80 else "review" if score >= 40 else "allow"
    return {
        "action": action,
        "score": score,
        "signals": signals,
        "matched_phrases": matched,
        "link_count": len(links),
        "uppercase_ratio": round(uppercase_ratio, 6),
    }
