"""Syntax selection for Reaper's shared parser and future frontend adapters."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .lexer import KEYWORD_ALIASES
from .source import SourceBuffer
from .errors import ReaperError


class SyntaxSelectionError(ReaperError):
    """A source requested a syntax mode that has no registered frontend."""

    def __init__(self, message: str) -> None:
        super().__init__(
            message,
            code="RPR-E0015",
            stage="syntax-router",
        )


@dataclass(frozen=True, slots=True)
class SyntaxProfile:
    mode_id: str
    extensions: tuple[str, ...]
    parser_entry: str
    lower_fn: str
    flow_arrows: bool = False
    localized_aliases: bool = False
    adapter_available: bool = True


@dataclass(frozen=True, slots=True)
class FrontendSelection:
    profile: SyntaxProfile
    source: SourceBuffer


class SyntaxRouter:
    """Resolve source format from an explicit override, directive, then extension.

    The currently executable frontends share Reaper's canonical parser. The
    Flow profile adds the flow-first arrow operator; MOST selects its localized
    keyword table. Other grammars can register a future adapter explicitly.
    """

    _DIRECTIVE = re.compile(r"^\s*#\s*!syntax\s*[:= ]\s*([a-zA-Z0-9_-]+)\s*$")

    def __init__(self) -> None:
        self._profiles: dict[str, SyntaxProfile] = {}
        self._extensions: dict[str, str] = {}
        self.register(SyntaxProfile(
            "reaper-classic", (".rpr",), "reaper.parser.Parser",
            "reaper.ir.lower", localized_aliases=True,
        ), aliases=("classic", "reaper"))
        self.register(SyntaxProfile(
            "reaper-flow", (".rflow",), "reaper.parser.Parser",
            "reaper.ir.lower", flow_arrows=True, localized_aliases=True,
        ), aliases=("flow", "flow-first"))
        self.register(SyntaxProfile(
            "localized-most", (".most",), "reaper.parser.Parser",
            "reaper.ir.lower", localized_aliases=True,
        ), aliases=("most", "localized"))
        self.register(SyntaxProfile(
            "embedded-dsl", (".rdsl",), "adapter:unregistered",
            "reaper.ir.lower", adapter_available=False,
        ), aliases=("dsl", "embedded"))

    def register(
        self,
        profile: SyntaxProfile,
        *,
        aliases: tuple[str, ...] = (),
    ) -> None:
        if not isinstance(profile, SyntaxProfile):
            raise TypeError("profile must be a SyntaxProfile")
        if not profile.mode_id or not profile.parser_entry or not profile.lower_fn:
            raise ValueError("syntax profile identifiers and entry points must be non-empty")
        keys = (profile.mode_id, *aliases)
        for key in keys:
            normalized = key.casefold().replace("_", "-")
            existing = self._profiles.get(normalized)
            if existing is not None and existing != profile:
                raise ValueError(f"syntax mode is already registered: {key}")
            self._profiles[normalized] = profile
        for extension in profile.extensions:
            normalized_extension = extension.casefold()
            if not normalized_extension.startswith("."):
                raise ValueError("syntax extensions must start with a dot")
            self._extensions[normalized_extension] = profile.mode_id

    def route(
        self,
        source: SourceBuffer,
        filename: str | None = None,
        syntax_mode: str | None = None,
    ) -> FrontendSelection:
        if not isinstance(source, SourceBuffer):
            raise TypeError("SyntaxRouter.route expects a SourceBuffer")

        selected = syntax_mode
        if selected is None:
            first_line = source.text.split("\n", 1)[0]
            directive = self._DIRECTIVE.match(first_line)
            if directive:
                selected = directive.group(1)
        if selected is None:
            extension = Path(filename or source.source_id).suffix.casefold()
            selected = self._extensions.get(extension, "reaper-classic")

        normalized = selected.casefold().replace("_", "-")
        profile = self._profiles.get(normalized)
        if profile is None:
            raise SyntaxSelectionError(f"unknown Reaper syntax mode: {selected}")
        if not profile.adapter_available:
            raise SyntaxSelectionError(
                f"syntax mode '{profile.mode_id}' is declared but has no executable frontend adapter"
            )

        return FrontendSelection(profile, source.with_syntax_mode(profile.mode_id))


DEFAULT_SYNTAX_ROUTER = SyntaxRouter()


def route_source(
    source: SourceBuffer,
    filename: str | None = None,
    syntax_mode: str | None = None,
) -> FrontendSelection:
    return DEFAULT_SYNTAX_ROUTER.route(source, filename, syntax_mode)
