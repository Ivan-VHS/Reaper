"""Anatidae white-blue-red theme primitives for Reaper Studio."""
from __future__ import annotations

import ctypes
import json
import os
import subprocess
import sys
from pathlib import Path
import tkinter as tk
from tkinter import ttk
from typing import Iterator

THEME_ENV = "REAPER_UI_THEME"
PALETTES: dict[str, dict[str, str]] = {
    "light": {
        "bg": "#F4F8FD", "surface": "#FFFFFF", "elevated": "#EAF1FA",
        "fg": "#122C45", "secondary": "#314B66", "muted": "#4D6177",
        "blue": "#004E98", "blue_hover": "#1A5FDB", "on_blue": "#FFFFFF",
        "red": "#B5122D", "red_hover": "#9C1026", "on_red": "#FFFFFF",
        "border": "#CAD8E8", "focus": "#1A5FDB",
        "selection": "#D9E8FF", "selection_fg": "#003366", "disabled": "#71849A",
    },
    "dark": {
        "bg": "#071A2D", "surface": "#0F2A45", "elevated": "#173A5E",
        "fg": "#E8EDF2", "secondary": "#D0DCE8", "muted": "#B3C4D6",
        "blue": "#70A5FF", "blue_hover": "#8AB6FF", "on_blue": "#061A30",
        "red": "#FF7B86", "red_hover": "#FF9AA2", "on_red": "#2B0610",
        "border": "#31516F", "focus": "#8AB6FF",
        "selection": "#244F82", "selection_fg": "#FFFFFF", "disabled": "#8096AC",
    },
}


def contrast_ratio(foreground: str, background: str) -> float:
    """Return WCAG contrast ratio for two #RRGGBB colors."""
    def luminance(value: str) -> float:
        raw = value.lstrip("#")
        if len(raw) != 6:
            raise ValueError(f"Expected #RRGGBB color, got {value!r}")
        channels = [int(raw[i:i + 2], 16) / 255 for i in (0, 2, 4)]
        linear = [
            channel / 12.92 if channel <= 0.04045
            else ((channel + 0.055) / 1.055) ** 2.4
            for channel in channels
        ]
        return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]

    first, second = sorted((luminance(foreground), luminance(background)), reverse=True)
    return (first + 0.05) / (second + 0.05)


def set_dpi_awareness() -> None:
    """Request per-monitor DPI awareness on Windows before creating Tk."""
    if os.name != "nt":
        return
    try:
        user32 = ctypes.windll.user32
        setter = getattr(user32, "SetProcessDpiAwarenessContext", None)
        if setter is not None:
            setter(ctypes.c_void_p(-4))  # PER_MONITOR_AWARE_V2
        else:
            user32.SetProcessDPIAware()
    except (AttributeError, OSError):
        return


def _settings_path(app_key: str) -> Path:
    base = os.environ.get("APPDATA")
    if base:
        return Path(base) / app_key / "ui-settings.json"
    config_home = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return config_home / app_key / "ui-settings.json"


def _load_theme(app_key: str) -> str:
    try:
        payload = json.loads(_settings_path(app_key).read_text(encoding="utf-8"))
        theme = payload.get("theme") if isinstance(payload, dict) else None
        return theme if theme in PALETTES else "light"
    except (OSError, ValueError, TypeError):
        return "light"


def _save_theme(app_key: str, theme: str) -> None:
    path = _settings_path(app_key)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps({"version": 1, "theme": theme}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    except OSError:
        return


def _system_dark() -> bool:
    if sys.platform == "win32":
        try:
            import winreg
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
            ) as key:
                value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                return int(value) == 0
        except (OSError, ImportError, ValueError):
            return False
    if sys.platform == "darwin":
        try:
            result = subprocess.run(
                ["defaults", "read", "-g", "AppleInterfaceStyle"],
                capture_output=True, text=True, timeout=1, check=False,
            )
            return result.stdout.strip().casefold() == "dark"
        except (OSError, subprocess.SubprocessError):
            return False
    gtk_theme = os.environ.get("GTK_THEME", "").casefold()
    return gtk_theme.endswith(":dark") or "-dark" in gtk_theme


def palette_for(mode: str = "system", *, system_dark: bool | None = None) -> dict[str, str]:
    """Compatibility adapter for the previous Reaper theme API."""
    requested = str(mode or "system").casefold()
    override = os.environ.get(THEME_ENV, "").casefold()
    if requested == "system" and override in PALETTES:
        requested = override
    if requested == "system":
        requested = "dark" if (_system_dark() if system_dark is None else system_dark) else "light"
    if requested not in PALETTES:
        raise ValueError("Theme must be 'system', 'light' or 'dark'")
    result = dict(PALETTES[requested])
    result.update({
        "mode": requested, "page": result["bg"], "surface_alt": result["elevated"],
        "text": result["fg"], "accent": result["blue"], "accent_hover": result["blue_hover"],
        "danger": result["red"], "editor": result["surface"],
        "editor_text": result["fg"], "log": result["surface"], "log_text": result["fg"],
    })
    return result


def _walk(widget: tk.Misc) -> Iterator[tk.Misc]:
    for child in widget.winfo_children():
        yield child
        yield from _walk(child)


def _paint_native_widgets(root: tk.Misc, palette: dict[str, str]) -> None:
    for widget in _walk(root):
        try:
            widget_class = widget.winfo_class()
            if widget_class in {"Text", "Listbox", "Entry"}:
                widget.configure(
                    background=palette["surface"], foreground=palette["fg"],
                    insertbackground=palette["fg"], selectbackground=palette["selection"],
                    selectforeground=palette["selection_fg"],
                    highlightbackground=palette["border"], highlightcolor=palette["focus"],
                    highlightthickness=1, relief="flat", borderwidth=1,
                )
            elif widget_class == "Menu":
                widget.configure(
                    background=palette["surface"], foreground=palette["fg"],
                    activebackground=palette["selection"],
                    activeforeground=palette["selection_fg"],
                    selectcolor=palette["blue"], relief="flat", borderwidth=0,
                )
        except tk.TclError:
            continue


def apply_theme(root: tk.Misc, app_key: str, theme: str | None = None) -> str:
    """Apply and persist light/dark semantic tokens across all Studio surfaces."""
    selected = theme if theme in PALETTES else (
        getattr(root, "_anatidae_theme", None) or _load_theme(app_key)
    )
    palette = PALETTES[selected]
    root._anatidae_theme = selected  # type: ignore[attr-defined]
    root._anatidae_palette = dict(palette)  # type: ignore[attr-defined]
    try:
        root.configure(background=palette["bg"])
        root.option_add("*Font", ("Segoe UI", 11))
        for key, value in {
            "*Text.background": palette["surface"], "*Text.foreground": palette["fg"],
            "*Text.insertBackground": palette["fg"], "*Text.selectBackground": palette["selection"],
            "*Text.selectForeground": palette["selection_fg"], "*Text.highlightBackground": palette["border"],
            "*Text.highlightColor": palette["focus"], "*Listbox.background": palette["surface"],
            "*Listbox.foreground": palette["fg"], "*Listbox.selectBackground": palette["selection"],
            "*Listbox.selectForeground": palette["selection_fg"],
        }.items():
            root.option_add(key, value)
    except tk.TclError:
        pass

    style = ttk.Style(root)
    try:
        if "clam" in style.theme_names():
            style.theme_use("clam")
    except tk.TclError:
        pass
    style.configure(".", font=("Segoe UI", 11), background=palette["bg"], foreground=palette["fg"])
    style.configure("TFrame", background=palette["bg"])
    style.configure("Pane.TFrame", background=palette["surface"])
    style.configure("TLabel", background=palette["bg"], foreground=palette["fg"])
    style.configure("Title.TLabel", background=palette["bg"], foreground=palette["blue"], font=("Segoe UI Semibold", 19))
    style.configure("Section.TLabel", background=palette["bg"], foreground=palette["blue"], font=("Segoe UI Semibold", 11), padding=(4, 5))
    style.configure("Muted.TLabel", background=palette["bg"], foreground=palette["muted"])
    style.configure(
        "TButton", background=palette["surface"], foreground=palette["blue"],
        bordercolor=palette["border"], lightcolor=palette["surface"], darkcolor=palette["border"],
        borderwidth=1, relief="flat", focusthickness=2, focuscolor=palette["focus"],
        padding=(14, 13),
    )
    style.map(
        "TButton",
        background=[("disabled", palette["elevated"]), ("pressed", palette["selection"]), ("active", palette["elevated"])],
        foreground=[("disabled", palette["disabled"]), ("pressed", palette["selection_fg"]), ("active", palette["blue"])],
    )
    style.configure(
        "Primary.TButton", background=palette["blue"], foreground=palette["on_blue"],
        bordercolor=palette["blue"], lightcolor=palette["blue"], darkcolor=palette["blue"],
        padding=(15, 13),
    )
    style.map(
        "Primary.TButton",
        background=[("disabled", palette["elevated"]), ("pressed", palette["blue"]), ("active", palette["blue_hover"])],
        foreground=[("disabled", palette["disabled"]), ("!disabled", palette["on_blue"])],
    )
    style.configure(
        "Danger.TButton", background=palette["red"], foreground=palette["on_red"],
        bordercolor=palette["red"], lightcolor=palette["red"], darkcolor=palette["red"],
        padding=(14, 13),
    )
    style.map(
        "Danger.TButton",
        background=[("disabled", palette["elevated"]), ("pressed", palette["red"]), ("active", palette["red_hover"])],
        foreground=[("disabled", palette["disabled"]), ("!disabled", palette["on_red"])],
    )
    style.configure("TEntry", fieldbackground=palette["surface"], foreground=palette["fg"], bordercolor=palette["border"], padding=(8, 7))
    style.map("TEntry", fieldbackground=[("focus", palette["surface"])], bordercolor=[("focus", palette["focus"])])
    style.configure("TNotebook", background=palette["bg"], borderwidth=0, tabmargins=(0, 3, 0, 0))
    style.configure("TNotebook.Tab", background=palette["elevated"], foreground=palette["secondary"], padding=(16, 13))
    style.map(
        "TNotebook.Tab",
        background=[("selected", palette["surface"]), ("active", palette["selection"])],
        foreground=[("selected", palette["blue"]), ("active", palette["blue"])],
    )
    style.configure(
        "Treeview", background=palette["surface"], fieldbackground=palette["surface"],
        foreground=palette["fg"], rowheight=42, bordercolor=palette["border"], relief="flat",
    )
    style.configure("Treeview.Heading", background=palette["elevated"], foreground=palette["fg"], font=("Segoe UI Semibold", 10), padding=(9, 9))
    style.map("Treeview", background=[("selected", palette["selection"])], foreground=[("selected", palette["selection_fg"])])
    style.configure("TLabelFrame", background=palette["bg"], foreground=palette["fg"], bordercolor=palette["border"])
    style.configure("TLabelFrame.Label", background=palette["bg"], foreground=palette["blue"], font=("Segoe UI Semibold", 10))
    style.configure("TSeparator", background=palette["border"])
    style.configure("Horizontal.TProgressbar", background=palette["blue"], troughcolor=palette["elevated"])
    _paint_native_widgets(root, palette)
    _save_theme(app_key, selected)
    return selected


def toggle_theme(root: tk.Misc, app_key: str) -> str:
    current = getattr(root, "_anatidae_theme", _load_theme(app_key))
    return apply_theme(root, app_key, "dark" if current == "light" else "light")


def apply_ui_theme(root: tk.Misc, mode: str = "system") -> dict[str, str]:
    """Legacy API retained for callers that explicitly choose a theme mode."""
    colors = palette_for(mode)
    apply_theme(root, "reaper-studio", colors["mode"])
    return colors
