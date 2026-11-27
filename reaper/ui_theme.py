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
        "heading": "#004E98", "blue": "#004E98", "blue_hover": "#1A5FDB", "on_blue": "#FFFFFF",
        "red": "#B5122D", "red_hover": "#9C1026", "on_red": "#FFFFFF",
        "border": "#CAD8E8", "focus": "#1A5FDB",
        "selection": "#D9E8FF", "selection_fg": "#122C45", "disabled": "#6B7C90",
    },
    "dark": {
        "bg": "#071A2D", "surface": "#0F2A45", "elevated": "#173A5E",
        "fg": "#E8EDF2", "secondary": "#D0DCE8", "muted": "#B3C4D6",
        "heading": "#FFFFFF", "blue": "#70A5FF", "blue_hover": "#8AB6FF", "on_blue": "#071A2D",
        "red": "#FF7B86", "red_hover": "#FF9AA2", "on_red": "#071A2D",
        "border": "#31516F", "focus": "#8AB6FF",
        "selection": "#244F82", "selection_fg": "#FFFFFF", "disabled": "#9BAFC4",
    },
    "mora": {
        "bg": "#211913", "surface": "#33261D", "elevated": "#493326",
        "fg": "#FFF3E2", "secondary": "#E7D2B8", "muted": "#C4A98A",
        "heading": "#FFD9A1", "blue": "#D58B3D", "blue_hover": "#EAA653", "on_blue": "#211913",
        "red": "#B64A40", "red_hover": "#C85C50", "on_red": "#FFF3E2",
        "border": "#75543A", "focus": "#F3C16B",
        "selection": "#60442E", "selection_fg": "#FFF3E2", "disabled": "#B09A83",
    },
}

# Preserve the previously shipped atmospheric theme presets alongside the
# 2026 light/dark semantic defaults. They remain selectable via REAPER_UI_THEME.
PALETTES.update({
    "dawn": {
        "bg": "#F3F6FA", "surface": "#FFFFFF", "elevated": "#EAF0F8",
        "fg": "#10243A", "secondary": "#365A83", "muted": "#526A82",
        "heading": "#0039A6", "blue": "#0039A6", "blue_hover": "#0A1E46", "on_blue": "#FFFFFF",
        "red": "#B51A10", "red_hover": "#D52B1E", "on_red": "#FFFFFF",
        "border": "#CBD6E4", "focus": "#D52B1E", "selection": "#0039A6",
        "selection_fg": "#FFFFFF", "disabled": "#74849A",
    },
    "sunset": {
        "bg": "#F5EFE8", "surface": "#FFF9F2", "elevated": "#EDE2D5",
        "fg": "#322B2A", "secondary": "#68564F", "muted": "#78685F",
        "heading": "#0039A6", "blue": "#0039A6", "blue_hover": "#0A1E46", "on_blue": "#FFFFFF",
        "red": "#B51A10", "red_hover": "#D52B1E", "on_red": "#FFFFFF",
        "border": "#D8C5B5", "focus": "#D52B1E", "selection": "#0039A6",
        "selection_fg": "#FFFFFF", "disabled": "#887D74",
    },
    "night": {
        "bg": "#081522", "surface": "#10263B", "elevated": "#17344D",
        "fg": "#EDF4FA", "secondary": "#C4D5E4", "muted": "#A9C0D4",
        "heading": "#EAF3FF", "blue": "#73B7FF", "blue_hover": "#9ACBFF", "on_blue": "#081522",
        "red": "#FF7D78", "red_hover": "#FFA39B", "on_red": "#190B0B",
        "border": "#31536B", "focus": "#FF8E86", "selection": "#174C7D",
        "selection_fg": "#FFFFFF", "disabled": "#71899B",
    },
})



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


def _install_semantic_status_tokens() -> None:
    """Add high-contrast status roles without changing the product's blue/red identity."""
    for theme_name, palette in PALETTES.items():
        if theme_name == "mora":
            palette.update({
                "success": "#9EC39A", "warning": "#F0BE73",
                "error": "#EF8E7C", "info": "#E8C99F",
                "brand": "#D58B3D", "brand_hover": "#EAA653",
                "on_brand": "#211913", "brand_secondary": "#526347",
                "on_brand_secondary": "#FFF3E2",
            })
            continue

        dark = theme_name in {"dark", "night"}
        palette.update({
            # Status meaning is carried by text/icon; hues stay inside the shared brand canon.
            "success": "#73B7FF" if dark else "#0039A6",
            "warning": "#FF7D78" if dark else "#B51A10",
            "error": "#FF7D78" if dark else "#B51A10",
            "info": "#FFFFFF" if dark else "#0A1E46",
        })
        palette.update({
            "brand": "#A78BFA" if dark else "#5B43B5",
            "brand_hover": "#C1AEFF" if dark else "#49359D",
            "on_brand": "#1D1730" if dark else "#FFFFFF",
            "brand_secondary": "#38D4B7" if dark else "#006F68",
            "on_brand_secondary": "#09231F" if dark else "#FFFFFF",
        })


def palette_contrast_issues(palette: dict[str, str]) -> list[str]:
    """Return WCAG AA text-pair violations for a semantic desktop palette."""
    required_pairs = (
        ("fg", "bg"), ("fg", "surface"), ("muted", "bg"),
        ("heading", "bg"), ("on_blue", "blue"), ("on_red", "red"),
        ("selection_fg", "selection"), ("success", "bg"),
        ("warning", "bg"), ("error", "bg"), ("info", "bg"), ("on_brand", "brand"),
        ("on_brand_secondary", "brand_secondary"),
    )
    issues = []
    for foreground, background in required_pairs:
        if foreground not in palette or background not in palette:
            issues.append(f"missing token: {foreground}/{background}")
        elif contrast_ratio(palette[foreground], palette[background]) < 4.5:
            issues.append(
                f"{foreground}/{background} contrast is below 4.5:1"
            )
    return issues


_install_semantic_status_tokens()


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
        return theme if theme in PALETTES else "mora"
    except (OSError, ValueError, TypeError):
        return "mora"


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
        raise ValueError("Theme must be 'system', 'light', 'dark', 'mora', 'dawn', 'sunset' or 'night'")
    result = dict(PALETTES[requested])
    issues = palette_contrast_issues(result)
    if issues:
        raise ValueError("Theme palette fails UI/UX 40026 contrast contract: " + "; ".join(issues))
    result.update({
        "mode": requested, "page": result["bg"], "surface_alt": result["elevated"],
        "text": result["fg"], "accent": result["brand"], "accent_hover": result["brand_hover"],
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
        root.option_add("*Font", ("Segoe UI", 10))
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
    style.configure(".", font=("Segoe UI", 10), background=palette["bg"], foreground=palette["fg"])
    style.configure("TFrame", background=palette["bg"])
    style.configure("Pane.TFrame", background=palette["surface"])
    style.configure("TLabel", background=palette["bg"], foreground=palette["fg"])
    style.configure("Title.TLabel", background=palette["bg"], foreground=palette["heading"], font=("Georgia", 18, "bold"))
    style.configure("Section.TLabel", background=palette["bg"], foreground=palette["heading"], font=("Georgia", 11, "bold"), padding=(4, 5))
    style.configure("Muted.TLabel", background=palette["bg"], foreground=palette["muted"])
    # Semantic status styles are text-first and remain readable in every theme.
    for status_name in ("Success", "Warning", "Error", "Info"):
        token = status_name.lower()
        style.configure(
            f"Status.{status_name}.TLabel",
            background=palette["bg"],
            foreground=palette[token],
            padding=(6, 3),
        )
    style.configure(
        "TButton", background=palette["surface"], foreground=palette["fg"],
        bordercolor=palette["border"], lightcolor=palette["surface"], darkcolor=palette["border"],
        borderwidth=1, relief="flat", focusthickness=2, focuscolor=palette["focus"],
        padding=(14, 13),
    )
    style.map(
        "TButton",
        background=[("disabled", palette["elevated"]), ("pressed", palette["selection"]), ("active", palette["elevated"])],
        foreground=[("disabled", palette["disabled"]), ("pressed", palette["selection_fg"]), ("active", palette["fg"])],
    )
    style.configure(
        "Primary.TButton", background=palette["brand"], foreground=palette["on_brand"],
        bordercolor=palette["brand"], lightcolor=palette["brand"], darkcolor=palette["brand"],
        padding=(15, 13),
    )
    style.map(
        "Primary.TButton",
        background=[("disabled", palette["elevated"]), ("pressed", palette["brand"]), ("active", palette["brand_hover"])],
        foreground=[("disabled", palette["disabled"]), ("!disabled", palette["on_brand"])],
    )
    style.configure(
        "Danger.TButton", background=palette["surface"], foreground=palette["fg"],
        bordercolor=palette["red"], lightcolor=palette["surface"], darkcolor=palette["red"],
        padding=(14, 13),
    )
    style.map(
        "Danger.TButton",
        background=[("disabled", palette["elevated"]), ("pressed", palette["selection"]), ("active", palette["surface"])],
        foreground=[("disabled", palette["disabled"]), ("!disabled", palette["fg"])],
    )
    style.configure("TEntry", fieldbackground=palette["surface"], foreground=palette["fg"], bordercolor=palette["border"], padding=(8, 7))
    style.map("TEntry", fieldbackground=[("focus", palette["surface"])], bordercolor=[("focus", palette["focus"])])
    style.configure("TNotebook", background=palette["bg"], borderwidth=0, tabmargins=(0, 3, 0, 0))
    style.configure("TNotebook.Tab", background=palette["elevated"], foreground=palette["secondary"], padding=(16, 13))
    style.map(
        "TNotebook.Tab",
        background=[("selected", palette["surface"]), ("active", palette["selection"])],
        foreground=[("selected", palette["fg"]), ("active", palette["fg"])],
    )
    style.configure(
        "Treeview", background=palette["surface"], fieldbackground=palette["surface"],
        foreground=palette["fg"], rowheight=42, bordercolor=palette["border"], relief="flat",
    )
    style.configure("Treeview.Heading", background=palette["elevated"], foreground=palette["fg"], font=("Georgia", 10, "bold"), padding=(9, 9))
    style.map("Treeview", background=[("selected", palette["selection"])], foreground=[("selected", palette["selection_fg"])])
    style.configure("TLabelFrame", background=palette["bg"], foreground=palette["fg"], bordercolor=palette["border"])
    style.configure("TLabelFrame.Label", background=palette["bg"], foreground=palette["heading"], font=("Georgia", 10, "bold"))
    style.configure("TSeparator", background=palette["border"])
    style.configure("Horizontal.TProgressbar", background=palette["brand"], troughcolor=palette["elevated"])
    _paint_native_widgets(root, palette)
    root._anatidae_native_backdrop = apply_native_backdrop(root)  # type: ignore[attr-defined]
    _save_theme(app_key, selected)
    return selected


def toggle_theme(root: tk.Misc, app_key: str) -> str:
    current = getattr(root, "_anatidae_theme", _load_theme(app_key))
    order = ("mora", "dawn", "sunset", "night")
    if current in {"light", "dark"}:
        current = "night" if current == "dark" else "dawn"
    next_mode = order[(order.index(current) + 1) % len(order)] if current in order else order[0]
    return apply_theme(root, app_key, next_mode)


def apply_ui_theme(root: tk.Misc, mode: str = "system") -> dict[str, str]:
    """Legacy API retained for callers that explicitly choose a theme mode."""
    colors = palette_for(mode)
    apply_theme(root, "reaper-studio", colors["mode"])
    return colors


def native_backdrop_policy(platform_name: str | None = None) -> str:
    """Choose Windows 11 Mica when available; keep a solid cross-platform fallback."""
    return "mica" if (platform_name or sys.platform) == "win32" else "opaque"


def apply_native_backdrop(root: tk.Misc) -> bool:
    """Request the Windows system Mica backdrop without making it a runtime dependency."""
    if native_backdrop_policy() != "mica":
        return False
    try:
        root.update_idletasks()
        handle = root.winfo_id()
        dwmapi = ctypes.WinDLL("dwmapi", use_last_error=True)
        set_attribute = dwmapi.DwmSetWindowAttribute
        set_attribute.argtypes = (
            ctypes.c_void_p, ctypes.c_uint, ctypes.c_void_p, ctypes.c_uint,
        )
        set_attribute.restype = ctypes.c_long
        backdrop_type = ctypes.c_int(2)  # DWMSBT_MAINWINDOW
        result = set_attribute(
            ctypes.c_void_p(handle), 38, ctypes.byref(backdrop_type),
            ctypes.sizeof(backdrop_type),
        )
        return result == 0
    except (AttributeError, OSError, tk.TclError, TypeError, ValueError):
        return False
