"""Deterministic semantic impact-profile catalogue for Reaper.

Ranks are ordinal lexical weights (1..5), not physical measurements.
"""
from __future__ import annotations

from typing import Any

DIMENSIONS = ("acoustic", "scale", "kinetic", "reach", "impulse")

_ROWS = (
    (1, "Грохот", "Массивный", "Баллистический", [5,5,4,3,4]),
    (2, "Громыхание", "Громоздкий", "Ракетный", [5,5,5,4,5]),
    (3, "Раскат", "Объёмный", "Снарядный", [4,4,4,3,4]),
    (4, "Рокот", "Крупный", "Артиллерийский", [5,4,4,4,4]),
    (5, "Гул", "Гигантский", "Гиперзвуковой", [5,5,5,5,5]),
    (6, "Рёв", "Исполинский", "Сверхзвуковой", [5,5,5,4,5]),
    (7, "Рев", "Огромный", "Ударный", [4,5,4,3,5]),
    (8, "Бум", "Могучий", "Импульсный", [4,4,5,3,5]),
    (9, "Удар", "Мощный", "Кинетический", [4,4,5,3,5]),
    (10, "Треск", "Тяжеловесный", "Реактивный", [4,4,5,3,4]),
    (11, "Трещание", "Основательный", "Траекторный", [3,4,4,4,3]),
    (12, "Бах", "Монументальный", "Динамический", [5,5,5,4,5]),
    (13, "Грохотание", "Колоссальный", "Разгонный", [5,5,5,4,5]),
    (14, "Раскатистость", "Внушительный", "Ускоренный", [4,4,5,3,4]),
    (15, "Громогласие", "Габаритный", "Снарядоподобный", [5,5,4,4,4]),
    (16, "Громоподобие", "Тяжёлый", "Пробивной", [5,5,4,3,5]),
    (17, "Шум", "Дородный", "Разрушительный", [3,4,3,2,3]),
    (18, "Резонанс", "Крепкий", "Мощностной", [4,4,3,3,4]),
    (19, "Рокотание", "Масштабный", "Дальнобойный", [4,5,4,5,4]),
    (20, "Оглушительность", "Великолепный", "Гиперскоростной", [5,5,5,5,5]),
)

_PROFILES: tuple[dict[str, Any], ...] = tuple(
    {
        "id": row[0],
        "sound": row[1],
        "scale": row[2],
        "motion": row[3],
        "ranks": dict(zip(DIMENSIONS, row[4])),
    }
    for row in _ROWS
)


def catalog() -> list[dict[str, Any]]:
    """Return independent copies of all 20 profiles."""
    return [{**profile, "ranks": dict(profile["ranks"])} for profile in _PROFILES]


def search_profiles(query: str) -> list[dict[str, Any]]:
    """Find profiles when every query token matches a phrase component."""
    if not isinstance(query, str) or not query.strip():
        raise ValueError("query must be non-empty text")
    terms = query.casefold().split()
    matches = []
    for profile in _PROFILES:
        haystack = " ".join(
            (profile["sound"], profile["scale"], profile["motion"])
        ).casefold()
        if all(term in haystack for term in terms):
            matches.append(profile)
    return [{**profile, "ranks": dict(profile["ranks"])} for profile in matches]


def find_profile(query: str | int) -> dict[str, Any]:
    """Resolve a profile by numeric ID or an exact/partial lexical query."""
    if isinstance(query, bool):
        raise ValueError("profile query must be an ID or text")
    if isinstance(query, int):
        matches = [profile for profile in _PROFILES if profile["id"] == query]
    else:
        matches = search_profiles(query)
    if not matches:
        raise ValueError(f"no impact profile matches: {query}")
    if len(matches) > 1:
        raise ValueError(f"ambiguous impact profile query: {query}")
    profile = matches[0]
    return {**profile, "ranks": dict(profile["ranks"])}


def rank_profiles(
    profiles: list[dict[str, Any]] | tuple[dict[str, Any], ...],
    dimension: str,
) -> list[dict[str, Any]]:
    """Stable descending sort by one declared ordinal dimension."""
    if dimension not in DIMENSIONS:
        raise ValueError(
            f"unknown dimension {dimension!r}; expected one of {', '.join(DIMENSIONS)}"
        )
    if not isinstance(profiles, (list, tuple)):
        raise TypeError("profiles must be a list")
    for profile in profiles:
        if not isinstance(profile, dict):
            raise TypeError("each profile must be a map")
        ranks = profile.get("ranks")
        if not isinstance(ranks, dict):
            raise ValueError("profile is missing its ranks map")
        value = ranks.get(dimension)
        if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 5:
            raise ValueError(f"profile has an invalid {dimension!r} rank")
    return sorted(profiles, key=lambda item: item["ranks"][dimension], reverse=True)


def format_catalog() -> str:
    lines = [
        "Impact profile lexicon (20 semantic profiles; ordinal ranks 1..5):",
        "ID | sound | scale | motion | acoustic scale kinetic reach impulse",
    ]
    for profile in _PROFILES:
        ranks = profile["ranks"]
        lines.append(
            f'{profile["id"]:02d} | {profile["sound"]} | {profile["scale"]} | '
            f'{profile["motion"]} | '
            + " ".join(str(ranks[key]) for key in DIMENSIONS)
        )
    lines.append("Ranks are lexical ordering aids, not physical measurements.")
    return "\n".join(lines)
