"""Accessible spring motion policy and native feedback for Tk desktop interfaces."""
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
MOTION_PROFILES = {
    "normal": {"label": "Normal", "stiffness": 240, "damping": 22, "stagger_ms": 55},
    "expressive": {"label": "Expressive", "stiffness": 340, "damping": 14, "stagger_ms": 75},
    "reduced": {"label": "Reduced Motion", "stiffness": 460, "damping": 42, "stagger_ms": 0},
}


@dataclass(frozen=True)
class MotionPreferences:
    reduce_motion: bool = False
    eco_visuals: bool = False
    sync_to_bpm: bool = False
    motion_mode: str = "normal"
    stiffness: int = 240
    damping: int = 22
    stagger_ms: int = 55


def ease_out(progress: float) -> float:
    """Canonical fast-start/precise-stop cubic ease-out."""
    t = max(0.0, min(1.0, float(progress)))
    return 1.0 - (1.0 - t) ** 3


def reduced_motion_enabled() -> bool:
    """Respect the explicit process override and native Windows preference."""
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


def _bounded_int(value: object, default: int, minimum: int, maximum: int) -> int:
    try:
        return max(minimum, min(maximum, int(value)))
    except (TypeError, ValueError, OverflowError):
        return default


def load_preferences(app_key: str) -> MotionPreferences:
    try:
        payload = json.loads(_settings_path(app_key).read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            return MotionPreferences()
        mode = payload.get("motion_mode", "normal")
        if mode not in MOTION_PROFILES:
            mode = "normal"
        return MotionPreferences(
            reduce_motion=bool(payload.get("reduce_motion", False)),
            eco_visuals=bool(payload.get("eco_visuals", False)),
            sync_to_bpm=bool(payload.get("sync_to_bpm", False)),
            motion_mode=mode,
            stiffness=_bounded_int(payload.get("stiffness", 240), 240, 80, 520),
            damping=_bounded_int(payload.get("damping", 22), 22, 6, 50),
            stagger_ms=_bounded_int(payload.get("stagger_ms", 55), 55, 0, 180),
        )
    except (OSError, ValueError, TypeError):
        return MotionPreferences()


def save_preferences(app_key: str, preferences: MotionPreferences) -> None:
    path = _settings_path(app_key)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"version": 2, **asdict(preferences)}
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except OSError:
        return


def duration_for(category: str, preferences: MotionPreferences | None = None) -> int:
    """Return a bounded duration; all retained reduced-motion effects stay <=80 ms."""
    duration = DURATIONS_MS.get(category)
    if duration is None:
        raise ValueError(f"Unknown motion category: {category}")
    prefs = preferences or MotionPreferences()
    if (
        reduced_motion_enabled() or prefs.reduce_motion or prefs.eco_visuals
        or prefs.motion_mode == "reduced"
    ):
        return min(duration, 80)
    if prefs.motion_mode == "expressive":
        return min(380, round(duration * 1.15))
    return duration


class Spring1D:
    """Small deterministic damped spring solver for short UI-only transitions."""

    def __init__(
        self, initial: float = 0.0, stiffness: float = 240.0,
        damping: float = 22.0, mass: float = 1.0,
    ) -> None:
        self.value = float(initial)
        self.target = float(initial)
        self.velocity = 0.0
        self.stiffness = max(1.0, float(stiffness))
        self.damping = max(0.0, float(damping))
        self.mass = max(0.001, float(mass))

    def set_target(self, value: float) -> None:
        self.target = float(value)

    def snap(self, value: float) -> None:
        self.value = self.target = float(value)
        self.velocity = 0.0

    def step(
        self, dt: float, stiffness: float | None = None,
        damping: float | None = None,
    ) -> float:
        k = max(1.0, float(stiffness if stiffness is not None else self.stiffness))
        c = max(0.0, float(damping if damping is not None else self.damping))
        frame = max(0.0, min(float(dt), 0.032))
        h = frame / 2.0
        for _ in range(2):
            acceleration = (-k * (self.value - self.target) - c * self.velocity) / self.mass
            self.velocity += acceleration * h
            self.value += self.velocity * h
        if abs(self.value - self.target) < 0.001 and abs(self.velocity) < 0.001:
            self.value = self.target
            self.velocity = 0.0
        return self.value


class MotionController:
    """Non-blocking window and toast feedback; never touches worker or DSP timing."""

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
        self._enabled = self._motion_enabled()
        self._toasts: list[tk.Toplevel] = []

    def _motion_enabled(self) -> bool:
        return not (
            reduced_motion_enabled() or self.preferences.reduce_motion
            or self.preferences.eco_visuals or self.preferences.motion_mode == "reduced"
        )

    def update_preferences(self, preferences: MotionPreferences) -> None:
        mode = preferences.motion_mode if preferences.motion_mode in MOTION_PROFILES else "normal"
        self.preferences = MotionPreferences(
            bool(preferences.reduce_motion), bool(preferences.eco_visuals),
            bool(preferences.sync_to_bpm), mode,
            _bounded_int(preferences.stiffness, 240, 80, 520),
            _bounded_int(preferences.damping, 22, 6, 50),
            _bounded_int(preferences.stagger_ms, 55, 0, 180),
        )
        save_preferences(self.app_key, self.preferences)
        self._enabled = self._motion_enabled()
        if not self._enabled:
            self.cancel()

    def fade_in(self) -> None:
        duration = duration_for("standard", self.preferences)
        if not self._enabled or duration == 0 or self.duration_ms == 0:
            return
        self.duration_ms = duration
        try:
            self.root.attributes("-alpha", 0.94)
        except (tk.TclError, TypeError):
            self._enabled = False
            return
        self._tick(0)

    def _tick(self, elapsed_ms: int) -> None:
        if not self._enabled:
            return
        progress = min(1.0, elapsed_ms / max(1, self.duration_ms))
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

    def show_toast(
        self, message: str, kind: str = "info", *, lifetime_ms: int = 2800,
    ) -> None:
        """Show a compact, dismissible native toast with a spring entrance."""
        if not isinstance(message, str) or not message.strip():
            return
        try:
            toast = tk.Toplevel(self.root)
            toast.overrideredirect(True)
            toast.transient(self.root)
            danger = kind.casefold() in {"error", "danger", "warning"}
            accent = "#B51A10" if danger else "#0039A6"
            surface = "#0B1F3A"
            frame = tk.Frame(
                toast, bg=surface, padx=14, pady=10,
                highlightthickness=1, highlightbackground="#58718F",
            )
            frame.pack(fill="both", expand=True)
            tk.Frame(frame, bg=accent, height=3).pack(fill="x", pady=(0, 8))
            tk.Label(
                frame, text=message[:220], bg=surface, fg="#FFFFFF",
                justify="left", anchor="w", wraplength=360,
                font=("Segoe UI", 9, "bold"),
            ).pack(fill="x")
            toast.update_idletasks()
            self.root.update_idletasks()
            width = toast.winfo_reqwidth()
            height = toast.winfo_reqheight()
            root_x = self.root.winfo_rootx()
            root_y = self.root.winfo_rooty()
            root_w = max(1, self.root.winfo_width())
            root_h = max(1, self.root.winfo_height())
            x = max(8, root_x + root_w - width - 20)
            stack_offset = len(self._toasts) * (height + 8)
            target_y = max(8, root_y + root_h - height - 20 - stack_offset)
            toast.geometry(f"+{x}+{target_y + (12 if self._enabled else 0)}")
            self._toasts.append(toast)

            def dismiss(_event: object = None) -> None:
                if toast in self._toasts:
                    self._toasts.remove(toast)
                try:
                    toast.destroy()
                except tk.TclError:
                    pass

            toast.bind("<Button-1>", dismiss)
            if self._enabled:
                spring = Spring1D(
                    12.0, self.preferences.stiffness, self.preferences.damping,
                )

                def animate() -> None:
                    try:
                        value = spring.step(
                            0.016, self.preferences.stiffness, self.preferences.damping,
                        )
                        toast.geometry(f"+{x}+{target_y + max(0, round(value))}")
                        if abs(value) > 0.25:
                            stagger = max(0, min(720, (len(self._toasts) - 1) * self.preferences.stagger_ms))
                toast.after(stagger, animate)
                    except tk.TclError:
                        return

                toast.after(16, animate)
            toast.after(max(800, int(lifetime_ms)), dismiss)
        except (tk.TclError, TypeError, RuntimeError):
            return

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
