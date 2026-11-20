"""Adaptive desktop theme for REAPER_UI_THEME; keeps data surfaces opaque and readable."""
from __future__ import annotations
import os
import subprocess
import sys
import tkinter as tk
from tkinter import ttk
from typing import Iterator

THEME_ENV = "REAPER_UI_THEME"
_PALETTES = {
    "light": {
        "page": "#F3F6FA", "surface": "#FFFFFF", "surface_alt": "#EAF0F7",
        "text": "#172337", "muted": "#5C6B80", "border": "#D7E0EB",
        "accent": "#2563EB", "accent_hover": "#1D4ED8", "danger": "#DC2626",
        "success": "#15803D", "editor": "#FFFFFF", "editor_text": "#172337",
        "selection": "#CFE0FF", "log": "#111C2E", "log_text": "#E5EDF7", "mode": "light",
    },
    "dark": {
        "page": "#101827", "surface": "#172337", "surface_alt": "#202F45",
        "text": "#EEF3FA", "muted": "#A7B4C7", "border": "#304158",
        "accent": "#6EA8FE", "accent_hover": "#91BCFF", "danger": "#F87171",
        "success": "#4ADE80", "editor": "#111C2E", "editor_text": "#E5EDF7",
        "selection": "#294B78", "log": "#0B1422", "log_text": "#E5EDF7", "mode": "dark",
    },
}

def _system_dark() -> bool:
    if sys.platform == "win32":
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                "Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize",
            )
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            winreg.CloseKey(key)
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
    requested = str(mode or "system").casefold()
    override = os.environ.get(THEME_ENV, "").casefold()
    if requested == "system" and override in _PALETTES:
        requested = override
    if requested == "system":
        requested = "dark" if (_system_dark() if system_dark is None else system_dark) else "light"
    if requested not in _PALETTES:
        raise ValueError("Theme must be 'system', 'light' or 'dark'")
    return dict(_PALETTES[requested])

def _walk(widget: tk.Misc) -> Iterator[tk.Misc]:
    for child in widget.winfo_children():
        yield child
        yield from _walk(child)

def apply_ui_theme(root: tk.Misc, mode: str = "system") -> dict[str, str]:
    colors = palette_for(mode)
    style = ttk.Style(root)
    available = style.theme_names()
    if colors["mode"] == "dark":
        target = "clam"
    elif sys.platform == "win32" and "vista" in available:
        target = "vista"
    elif sys.platform == "darwin" and "aqua" in available:
        target = "aqua"
    else:
        target = "clam"
    if target in available and style.theme_use() != target:
        style.theme_use(target)
    root.configure(background=colors["page"])
    style.configure(".", font=("Segoe UI", 10), foreground=colors["text"])
    style.configure("TFrame", background=colors["page"])
    style.configure("Panel.TFrame", background=colors["surface"])
    style.configure("TLabel", background=colors["page"], foreground=colors["text"])
    style.configure("Muted.TLabel", background=colors["page"], foreground=colors["muted"])
    style.configure("TButton", padding=(12, 7), focuscolor=colors["accent"])
    style.map("TButton", foreground=[("disabled", colors["muted"]), ("active", colors["text"])],
              background=[("active", colors["surface_alt"])])
    style.configure("TNotebook", background=colors["page"], borderwidth=0)
    style.configure("TNotebook.Tab", padding=(14, 8), background=colors["surface_alt"],
                    foreground=colors["muted"])
    style.map("TNotebook.Tab", background=[("selected", colors["surface"]),
              ("active", colors["surface_alt"])],
              foreground=[("selected", colors["text"]), ("active", colors["text"])])
    style.configure("TLabelframe", background=colors["surface"], bordercolor=colors["border"])
    style.configure("TLabelframe.Label", background=colors["surface"], foreground=colors["text"])
    style.configure("Treeview", rowheight=30, background=colors["surface"],
                    fieldbackground=colors["surface"], foreground=colors["text"],
                    bordercolor=colors["border"])
    style.map("Treeview", background=[("selected", colors["accent"])],
              foreground=[("selected", "#FFFFFF")])
    style.configure("Treeview.Heading", padding=(8, 7), background=colors["surface_alt"],
                    foreground=colors["muted"], relief="flat")
    for widget in _walk(root):
        if isinstance(widget, tk.Text):
            widget.configure(background=colors["editor"], foreground=colors["editor_text"],
                insertbackground=colors["editor_text"], selectbackground=colors["selection"],
                selectforeground=colors["editor_text"], highlightbackground=colors["border"],
                highlightcolor=colors["accent"], relief="flat", borderwidth=0)
        elif isinstance(widget, tk.Listbox):
            widget.configure(background=colors["surface"], foreground=colors["text"],
                selectbackground=colors["accent"], selectforeground="#FFFFFF",
                highlightbackground=colors["border"], relief="flat", borderwidth=0)
        elif isinstance(widget, tk.Entry):
            widget.configure(background=colors["editor"], foreground=colors["editor_text"],
                insertbackground=colors["editor_text"], selectbackground=colors["selection"],
                relief="flat", highlightbackground=colors["border"])
    return colors
