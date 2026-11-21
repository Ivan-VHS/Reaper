"""Accessible, persisted motion policy for the Tk desktop interface."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import tkinter as tk

DURATIONS_MS = {
    "instant": 0,
    "micro": 100,
    "fast": 140,
    "standard": 180,
    "spatial": 220,
    "emphasis": 320,
}
EASING = "cubic-bezier(0.2, 0.8, 0.2, 1)"
INSTRUMENTAL_EASING = "cubic-bezier(0.05, 0.9, 0.2, 1)"


@dataclass(frozen=True)
class MotionPreferences:
    reduce_motion: bool = False
    eco_visuals: bool = False
    sync_to_bpm: bool = False


def ease_out(progress: float) -> float:
    """Canonical fast-start/precise-stop cubic ease-out."""
    t = max(0.0, min(1.0, float(progress)))
    return 1.0 - (1.0 - t) ** 3


def reduced_motion_enabled() -> bool:
    """Respect explicit process override and the native Windows preference."""
    override = os.environ.get("UI_REDUCED_MOTION", "").strip().lower()
    if override in {"1", "true", "yes", "on"}:
        return True
    if os.name == "nt":
        try:
            import ctypes
            enabled = ctypes.c_int(1)
            if ctypes.windll.user32.SystemParametersInfoW(
                0x1042, 0, ctypes.byref(enabled), 0
            ):
                return not bool(enabled.value)
        except (AttributeError, OSError, TypeError):
            pass
    return False


def _settings_path(app_key: str) -> Path:
    base = os.environ.get("APPDATA")
    if base:
        return Path(base) / app_key / "ui-motion.json"
    config_home = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return config_home / app_key / "ui-motion.json"


def load_preferences(app_key: str) -> MotionPreferences:
    try:
        payload = json.loads(_settings_path(app_key).read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            return MotionPreferences()
        return MotionPreferences(
            reduce_motion=bool(payload.get("reduce_motion", False)),
            eco_visuals=bool(payload.get("eco_visuals", False)),
            sync_to_bpm=bool(payload.get("sync_to_bpm", False)),
        )
    except (OSError, ValueError, TypeError):
        return MotionPreferences()


def save_preferences(app_key: str, preferences: MotionPreferences) -> None:
    path = _settings_path(app_key)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps({"version": 1, **asdict(preferences)}, indent=2) + "\n",
            encoding="utf-8",
        )
    except OSError:
        return


def duration_for(category: str, preferences: MotionPreferences | None = None) -> int:
    """Return a bounded duration; reduced-motion transitions never exceed 80 ms."""
    duration = DURATIONS_MS.get(category)
    if duration is None:
        raise ValueError(f"Unknown motion category: {category}")
    if (preferences and preferences.reduce_motion) or reduced_motion_enabled():
        return min(duration, 80)
    if preferences and preferences.eco_visuals:
        return min(duration, 80)
    return duration


class MotionController:
    """Runs short, non-blocking Tk window feedback without touching worker timing."""

    def __init__(
        self,
        root: tk.Misc,
        *,
        duration_ms: int = DURATIONS_MS["fast"],
        app_key: str = "reaper-studio",
    ) -> None:
        self.root = root
        self.app_key = app_key
        self.duration_ms = max(0, int(duration_ms))
        self.preferences = load_preferences(app_key)
        self._after_id: str | None = None
        self._enabled = not reduced_motion_enabled()

    def update_preferences(self, preferences: MotionPreferences) -> None:
        self.preferences = preferences
        save_preferences(self.app_key, preferences)
        self._enabled = not reduced_motion_enabled() and not (
            preferences.reduce_motion or preferences.eco_visuals
        )
        if not self._enabled:
            self.cancel()

    def fade_in(self) -> None:
        if (
            not self._enabled or self.preferences.reduce_motion
            or self.preferences.eco_visuals or self.duration_ms == 0
        ):
            return
        try:
            self.root.attributes("-alpha", 0.94)
        except (tk.TclError, TypeError):
            self._enabled = False
            return
        self._tick(0)

    def _tick(self, elapsed_ms: int) -> None:
        if not self._enabled:
            return
        progress = min(1.0, elapsed_ms / self.duration_ms)
        try:
            self.root.attributes("-alpha", 0.94 + 0.06 * ease_out(progress))
        except (tk.TclError, TypeError):
            self._enabled = False
            return
        if progress < 1.0:
            self._after_id = self.root.after(
                16, self._tick, min(self.duration_ms, elapsed_ms + 16)
            )
        else:
            self._after_id = None

    def cancel(self) -> None:
        if self._after_id is not None:
            try:
                self.root.after_cancel(self._after_id)
            except tk.TclError:
                pass
            self._after_id = None
        try:
            self.root.attributes("-alpha", 1.0)
        except (tk.TclError, TypeError):
            pass
