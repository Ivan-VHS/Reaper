"""Small, opt-in motion primitives for a Tk desktop interface.

Motion is deliberately restrained and respects UI_REDUCED_MOTION=1 plus the
Windows client-area animation accessibility setting.
"""
from __future__ import annotations

import os
import tkinter as tk


DURATIONS_MS = {
    "instant": 0,
    "micro": 100,
    "fast": 140,
    "standard": 180,
    "spatial": 240,
    "emphasis": 280,
}


def ease_out(progress: float) -> float:
    """Cubic ease-out, clamped to the [0, 1] interval."""
    t = max(0.0, min(1.0, float(progress)))
    return 1.0 - (1.0 - t) ** 3


def reduced_motion_enabled() -> bool:
    """Read the portable override and Windows animation accessibility flag."""
    override = os.environ.get("UI_REDUCED_MOTION", "").strip().lower()
    if override in {"1", "true", "yes", "on"}:
        return True
    if os.name == "nt":
        try:
            import ctypes
            enabled = ctypes.c_int(1)
            # SPI_GETCLIENTAREAANIMATION: FALSE means client-area animation is off.
            if ctypes.windll.user32.SystemParametersInfoW(
                0x1042, 0, ctypes.byref(enabled), 0
            ):
                return not bool(enabled.value)
        except (AttributeError, OSError, TypeError):
            pass
    return False


class MotionController:
    """Applies a short native window entrance without changing layout."""

    def __init__(self, root: tk.Misc, *, duration_ms: int = DURATIONS_MS["fast"]) -> None:
        self.root = root
        self.duration_ms = max(0, int(duration_ms))
        self._after_id: str | None = None
        self._enabled = not reduced_motion_enabled()

    def fade_in(self) -> None:
        """Fade in only when enabled and supported by the current window system."""
        if not self._enabled or self.duration_ms == 0:
            return
        try:
            self._start()
        except tk.TclError:
            self._enabled = False

    def _start(self) -> None:
        if not self._enabled:
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
        alpha = 0.94 + 0.06 * ease_out(progress)
        try:
            self.root.attributes("-alpha", alpha)
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
        """Cancel a pending animation and leave the window fully visible."""
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
