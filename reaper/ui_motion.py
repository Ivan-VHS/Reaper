"""Accessible spring-based motion policy for native desktop interfaces."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import math
import os
from pathlib import Path
import tkinter as tk

DURATIONS_MS = {
    "instant": 0, "micro": 100, "fast": 140,
    "standard": 180, "spatial": 220, "emphasis": 320,
}
EASING = "cubic-bezier(0.2, 0.8, 0.2, 1)"
INSTRUMENTAL_EASING = "cubic-bezier(0.05, 0.9, 0.2, 1)"
PADDLE_EASING = "cubic-bezier(0.22, 1.18, 0.36, 1)"
WATER_EASING = "cubic-bezier(0.37, 0, 0.63, 1)"


@dataclass(frozen=True)
class MotionPreferences:
    reduce_motion: bool = False
    eco_visuals: bool = False
    sync_to_bpm: bool = False
    expressive_motion: bool = False


def ease_out(progress: float) -> float:
    """Canonical fast-start/precise-stop cubic ease-out."""
    t = max(0.0, min(1.0, float(progress)))
    return 1.0 - (1.0 - t) ** 3


class Spring1D:
    """Bounded mass-spring-damper solver for UI-thread animation only."""

    def __init__(self, initial: float = 0.0, stiffness: float = 240.0,
                 damping: float = 22.0, mass: float = 1.0) -> None:
        initial_value = float(initial)
        stiffness_value = float(stiffness)
        damping_value = float(damping)
        mass_value = float(mass)
        if not all(math.isfinite(value) for value in (
            initial_value, stiffness_value, damping_value, mass_value
        )):
            raise ValueError("Spring parameters must be finite")
        self.value = initial_value
        self.target = initial_value
        self.velocity = 0.0
        self.stiffness = max(1.0, stiffness_value)
        self.damping = max(0.0, damping_value)
        self.mass = max(0.1, mass_value)

    def set_target(self, target: float) -> None:
        target = float(target)
        if not math.isfinite(target):
            raise ValueError("Spring target must be finite")
        self.target = target

    def snap(self, value: float) -> None:
        value = float(value)
        if not math.isfinite(value):
            raise ValueError("Spring value must be finite")
        self.value = self.target = value
        self.velocity = 0.0

    def step(self, dt: float, stiffness: float | None = None,
             damping: float | None = None, mass: float | None = None) -> float:
        """Advance with semi-implicit Euler, capped dt and two substeps."""
        dt = float(dt)
        if not math.isfinite(dt) or dt <= 0.0:
            return self.value
        k = float(self.stiffness if stiffness is None else stiffness)
        c = float(self.damping if damping is None else damping)
        m = float(self.mass if mass is None else mass)
        if not all(math.isfinite(value) for value in (k, c, m)):
            raise ValueError("Spring parameters must be finite")
        k = max(1.0, k)
        c = max(0.0, c)
        m = max(0.1, m)
        h = min(dt, 0.032) / 2.0
        for _ in range(2):
            acceleration = (-k * (self.value - self.target) - c * self.velocity) / m
            self.velocity += acceleration * h
            self.value += self.velocity * h
        if abs(self.value - self.target) < 0.001 and abs(self.velocity) < 0.001:
            self.value = self.target
            self.velocity = 0.0
        return self.value

    @property
    def settled(self) -> bool:
        return abs(self.value - self.target) < 0.001 and abs(self.velocity) < 0.001


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


def _boolean_preference(payload: dict[str, object], key: str) -> bool:
    """Accept JSON booleans only; strings such as "false" must not enable a mode."""
    value = payload.get(key, False)
    return value if isinstance(value, bool) else False


def load_preferences(app_key: str) -> MotionPreferences:
    try:
        payload = json.loads(_settings_path(app_key).read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            return MotionPreferences()
        return MotionPreferences(
            reduce_motion=_boolean_preference(payload, "reduce_motion"),
            eco_visuals=_boolean_preference(payload, "eco_visuals"),
            sync_to_bpm=_boolean_preference(payload, "sync_to_bpm"),
            expressive_motion=_boolean_preference(payload, "expressive_motion"),
        )
    except (OSError, ValueError, TypeError):
        return MotionPreferences()


def save_preferences(app_key: str, preferences: MotionPreferences) -> None:
    path = _settings_path(app_key)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps({"version": 2, **asdict(preferences)}, indent=2) + "\n",
            encoding="utf-8",
        )
    except OSError:
        return


def duration_for(category: str, preferences: MotionPreferences | None = None) -> int:
    """Return a bounded duration; accessibility and eco preferences take priority."""
    duration = DURATIONS_MS.get(category)
    if duration is None:
        raise ValueError(f"Unknown motion category: {category}")
    prefs = preferences or MotionPreferences()
    if prefs.reduce_motion or reduced_motion_enabled():
        return min(duration, 80)
    if prefs.eco_visuals:
        return min(duration, 80)
    if prefs.expressive_motion:
        return min(380, int(round(duration * 1.35)))
    return duration


class MotionController:
    """Runs short, non-blocking Tk window feedback without touching worker timing."""

    def __init__(self, root: tk.Misc, *, duration_ms: int = DURATIONS_MS["fast"],
                 app_key: str = "reaper-studio",
                 preferences: MotionPreferences | None = None) -> None:
        self.root = root
        self.app_key = app_key
        self.duration_ms = max(0, int(duration_ms))
        self.preferences = preferences or load_preferences(app_key)
        self._after_id: str | None = None
        self._spring: Spring1D | None = None
        self._ticks = 0
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
        """Spring-fade a native top-level window; reduced/eco modes stay still."""
        if (not self._enabled or self.preferences.reduce_motion
                or self.preferences.eco_visuals or self.duration_ms == 0):
            return
        try:
            self.root.attributes("-alpha", 0.94)
        except (tk.TclError, TypeError):
            self._enabled = False
            return
        preset = (340.0, 20.0, 0.85) if self.preferences.expressive_motion else (240.0, 22.0, 1.0)
        self._spring = Spring1D(0.94, *preset)
        self._spring.set_target(1.0)
        self._ticks = 0
        self._tick_spring()

    def _tick_spring(self) -> None:
        if not self._enabled or self._spring is None:
            return
        value = self._spring.step(0.016)
        try:
            self.root.attributes("-alpha", value)
        except (tk.TclError, TypeError):
            self._enabled = False
            self._spring = None
            return
        self._ticks += 1
        max_ticks = max(1, math.ceil(duration_for("spatial", self.preferences) / 16))
        if self._spring.settled or self._ticks >= max_ticks:
            try:
                self.root.attributes("-alpha", 1.0)
            except (tk.TclError, TypeError):
                pass
            self._spring = None
            self._after_id = None
            return
        self._after_id = self.root.after(16, self._tick_spring)

    def cancel(self) -> None:
        if self._after_id is not None:
            try:
                self.root.after_cancel(self._after_id)
            except tk.TclError:
                pass
            self._after_id = None
        self._spring = None
        try:
            self.root.attributes("-alpha", 1.0)
        except (tk.TclError, TypeError):
            pass


def fade_in_window(window: tk.Toplevel, preferences: MotionPreferences,
                   *, app_key: str = "reaper-studio") -> MotionController:
    """Attach a preference-aware spring transition to a Toplevel."""
    controller = MotionController(
        window, app_key=app_key, preferences=preferences,
        duration_ms=duration_for("spatial", preferences),
    )
    window._motion_controller = controller  # type: ignore[attr-defined]
    window.bind("<Destroy>",
                lambda event: controller.cancel() if event.widget is window else None,
                add="+")
    controller.fade_in()
    return controller
