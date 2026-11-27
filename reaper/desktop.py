"""Reaper Studio desktop IDE.

Tk widgets stay on the UI thread. Normal program execution and embedded builds
run in workers and report through a queue/after bridge. Debug pauses use the
existing runtime debugger's cooperative hook.
"""
from __future__ import annotations

import json
import queue
import re
import subprocess
import threading
from pathlib import Path
import tkinter as tk
from tkinter import font as tkfont
from tkinter import filedialog, messagebox, simpledialog, ttk
from tkinter.scrolledtext import ScrolledText
from typing import Any

from reaper.noo_tah import Runtime as NooTahRuntime
from reaper.embedded import (
    EmbeddedError,
    build_project as embedded_build_project,
    init_project as embedded_init_project,
    inspect_project as embedded_inspect_project,
    list_profiles as list_embedded_profiles,
)
from reaper.errors import ReaperError
from reaper.parser import parse
from reaper.runtime import Interpreter
from reaper.debugger import DebuggerStopped, RuntimeDebugger
from reaper.plugins import PluginError, PluginManager
from reaper.ide_support import SOURCE_EXTENSIONS, highlight_spans, iter_project_entries, normalize_diagnostics
from reaper.language_service import LanguageService
from reaper.codex66 import export_json as export_codex66_json
from reaper.codex66_ui import Codex66Window
from reaper.ui_motion import MotionController, MotionPreferences, fade_in_window
from reaper.ui_theme import apply_theme, apply_ui_theme, set_dpi_awareness, toggle_theme

APP_TITLE = "Reaper Studio · Ivan-VHS"
STARTER = """craft double(value) {
    yield value * 2
}

make values := [1, 2, 3, 4]
emit values :: map(double)
"""

class ReaperStudio(tk.Tk):
    def __init__(self) -> None:
        set_dpi_awareness()
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1320x860")
        self.minsize(920, 640)
        self._theme_name = apply_theme(self, "reaper-studio")
        self.plugin_manager = PluginManager()
        self._theme_mode = tk.StringVar(value=self._theme_name)
        self.current_file: Path | None = None
        self.project_root: Path | None = None
        self.breakpoints: set[int] = set()
        self.debugger: RuntimeDebugger | None = None
        self._debug_wait = False
        self._debug_signal = tk.BooleanVar(value=False)
        self._run_queue: queue.Queue[tuple[str, object]] = queue.Queue()
        self._running = False
        self._node_process: subprocess.Popen[str] | None = None
        self._closing = False
        self._dirty = False
        self._highlight_job: str | None = None
        self._language_service = LanguageService(workers=1)
        self._language_version = 0
        self._completion_window: tk.Toplevel | None = None
        self._completion_list: tk.Listbox | None = None
        self._completion_items: list[dict[str, str]] = []
        self._completion_prefix = ""

        self._configure_styles()
        self._build_brand_strip()
        self._build_menu()
        self._build_toolbar()
        self._build_workspace()
        self._apply_editor_visuals()
        self._build_statusbar()
        self._motion = MotionController(self, app_key="reaper-studio")
        self._motion.fade_in()
        self._bind_shortcuts()
        self.bind_all("<Control-k>", self._command_palette_shortcut, add="+")
        self.editor.bind("<Control-k>", self._command_palette_shortcut, add="+")
        self._insert_starter()
        self.after(50, self._drain_run_queue)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _configure_styles(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Treeview", rowheight=24)
        try:
            installed = {family.casefold(): family for family in tkfont.families(self)}
        except tk.TclError:
            installed = {}
        heading_font = next(
            (installed[name.casefold()] for name in ("Caveat", "Marck Script", "Lobster") if name.casefold() in installed),
            "Segoe UI Semibold",
        )
        style.configure("PaneTitle.TLabel", font=(heading_font, 12))
        style.configure("Toolbar.TButton", padding=(9, 5))

    def _build_brand_strip(self) -> None:
        """Paint the shared white-blue-red identity without changing editor layout."""
        strip = tk.Frame(self, height=5, bd=0, highlightthickness=0)
        strip.pack(fill="x")
        strip.pack_propagate(False)
        for color in ("#0039A6", "#FFFFFF", "#D52B1E"):
            tk.Frame(strip, background=color, bd=0, highlightthickness=0).pack(
                side="left", fill="both", expand=True
            )

    def _build_menu(self) -> None:
        menu = tk.Menu(self)
        file_menu = tk.Menu(menu, tearoff=False)
        file_menu.add_command(label="Создать", command=self.new_file, accelerator="Ctrl+N")
        file_menu.add_command(label="Открыть…", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Открыть папку проекта…", command=self.open_folder)
        file_menu.add_command(label="Сохранить", command=self.save_file, accelerator="Ctrl+S")
        file_menu.add_command(label="Сохранить как…", command=self.save_as, accelerator="Ctrl+Shift+S")
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self._on_close)
        menu.add_cascade(label="Файл", menu=file_menu)

        edit_menu = tk.Menu(menu, tearoff=False)
        edit_menu.add_command(label="Найти…", command=self.find_text, accelerator="Ctrl+F")
        edit_menu.add_command(label="Перейти к строке…", command=self.goto_line, accelerator="Ctrl+G")
        edit_menu.add_command(label="Автодополнение…", command=self.show_completion, accelerator="Ctrl+Space")
        edit_menu.add_command(label="Перейти к определению", command=self.go_to_definition, accelerator="F12")
        edit_menu.add_command(label="Найти ссылки на символ", command=self.find_references)
        edit_menu.add_command(label="Переименовать символ…", command=self.rename_symbol, accelerator="Ctrl+Shift+R")
        edit_menu.add_command(label="Палитра команд…", command=self.show_command_palette, accelerator="Ctrl+K")
        edit_menu.add_separator()
        edit_menu.add_command(label="Выделить всё", command=lambda: self.editor.tag_add("sel", "1.0", "end-1c"))
        edit_menu.add_command(label="Отменить", command=lambda: self.editor.edit_undo(), accelerator="Ctrl+Z")
        edit_menu.add_command(label="Повторить", command=lambda: self.editor.edit_redo(), accelerator="Ctrl+Y")
        menu.add_cascade(label="Правка", menu=edit_menu)

        run_menu = tk.Menu(menu, tearoff=False)
        run_menu.add_command(label="Проверить синтаксис и типы", command=self.check_source, accelerator="Shift+F5")
        run_menu.add_command(label="Запустить", command=self.run_source, accelerator="F5")
        run_menu.add_command(label="Отладка с первого шага", command=self.debug_source)
        run_menu.add_command(label="Точка остановки", command=self.toggle_breakpoint, accelerator="F9")
        run_menu.add_command(label="Продолжить", command=self.continue_debug)
        run_menu.add_command(label="Шаг", command=self.step_debug)
        run_menu.add_command(label="Остановить отладку", command=self.stop_debug)
        run_menu.add_command(label="Очистить вывод", command=self.clear_output)
        menu.add_cascade(label="Выполнение", menu=run_menu)
        node_menu = tk.Menu(menu, tearoff=False)
        node_menu.add_command(label="Run JavaScript (NOO TAH)", command=self.run_node_source)
        node_menu.add_command(label="Check JavaScript", command=self.check_node_source)
        node_menu.add_command(label="Debug JavaScript (Node Inspector)", command=lambda: self.run_node_source(inspect=True))
        node_menu.add_command(label="Run npm command…", command=self.run_noo_tah_npm)
        node_menu.add_command(label="Node.js Runtime Diagnostics", command=self.noo_tah_doctor)
        node_menu.add_command(label="Stop Node.js Process", command=self.stop_node_source)
        menu.add_cascade(label="NOO TAH / Node.js", menu=node_menu)

        embedded_menu = tk.Menu(menu, tearoff=False)
        embedded_menu.add_command(label="Обзор системного языка и MMIO…", command=self.show_hardware_overview)
        embedded_menu.add_separator()
        embedded_menu.add_command(label="Создать embedded-проект…", command=self.embedded_new_project)
        embedded_menu.add_command(label="Проверить профиль микроконтроллера…", command=self.embedded_inspect_project)
        embedded_menu.add_command(label="Собрать прошивку…", command=self.embedded_build)
        menu.add_cascade(label="Системы / Hardware", menu=embedded_menu)

        plugin_menu = tk.Menu(menu, tearoff=False)
        plugin_menu.add_command(label="Менеджер плагинов…", command=self.show_plugins)
        menu.add_cascade(label="Плагины", menu=plugin_menu)
        view_menu = tk.Menu(menu, tearoff=False)
        for mode, label in (
            ("system", "Системная"), ("light", "Светлая"), ("dark", "Тёмная"),
            ("dawn", "Рассвет"), ("sunset", "Закат"), ("night", "Ночь"),
        ):
            view_menu.add_radiobutton(label=label, variable=self._theme_mode, value=mode, command=self.apply_visual_theme)
        view_menu.add_separator()
        view_menu.add_command(label="Настройки движения…", command=self.show_motion_settings)
        view_menu.add_separator()
        view_menu.add_command(label="CODEX-66 — каталог возможностей…", command=self.show_codex66, accelerator="Ctrl+Alt+K")
        menu.add_cascade(label="Вид", menu=view_menu)
        self.configure(menu=menu)

    def _command_palette_shortcut(self, _event: tk.Event | None = None) -> str:
        self.show_command_palette()
        return "break"

    def show_command_palette(self) -> None:
        """Open a searchable, keyboard-first palette for frequent Studio actions."""
        existing = getattr(self, "_command_palette", None)
        if existing is not None and existing.winfo_exists():
            existing.lift()
            existing.focus_force()
            return
        window = tk.Toplevel(self)
        self._command_palette = window
        window.title("Палитра команд · Reaper Studio")
        window.transient(self)
        window.resizable(False, False)
        frame = ttk.Frame(window, padding=14)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Быстрые команды", style="PaneTitle.TLabel").pack(anchor="w", pady=(0, 8))
        query_var = tk.StringVar()
        search = ttk.Entry(frame, textvariable=query_var, width=62)
        search.pack(fill="x", pady=(0, 8))
        results = tk.Listbox(frame, height=10, activestyle="none", exportselection=False)
        results.pack(fill="both", expand=True)
        empty = ttk.Label(frame, text="Команды не найдены. Измените поисковый запрос.")
        empty.pack(anchor="w", pady=(6, 0))
        commands = [
            ("Создать файл", self.new_file),
            ("Открыть файл", self.open_file),
            ("Открыть папку проекта", self.open_folder),
            ("Сохранить файл", self.save_file),
            ("Проверить исходный код", self.check_source),
            ("Запустить программу", self.run_source),
            ("Запустить отладку", self.debug_source),
            ("Системный язык и MMIO", self.show_hardware_overview),
            ("Создать embedded-проект", self.embedded_new_project),
            ("Проверить профиль MCU", self.embedded_inspect_project),
            ("Менеджер плагинов", self.show_plugins),
            ("Настройки движения", self.show_motion_settings),
            ("CODEX-66 — каталог возможностей", self.show_codex66),
            ("Автодополнение REAPER", self.show_completion),
            ("Перейти к определению", self.go_to_definition),
            ("Найти ссылки на символ", self.find_references),
            ("Переименовать символ", self.rename_symbol),
            ("Переключить атмосферу", self.toggle_ui_theme),
        ]
        visible: list[tuple[str, Any]] = []

        def refresh(*_args: object) -> None:
            query = query_var.get().strip().casefold()
            visible.clear()
            visible.extend(item for item in commands if not query or query in item[0].casefold())
            results.delete(0, "end")
            for label, _action in visible:
                results.insert("end", label)
            if visible:
                results.selection_set(0)
                results.activate(0)
            empty.configure(text="" if visible else "Команды не найдены. Измените поисковый запрос.")

        def close() -> None:
            if window.winfo_exists():
                window.destroy()
            self._command_palette = None
            try:
                self.editor.focus_set()
            except tk.TclError:
                pass

        def execute(_event: tk.Event | None = None) -> str:
            selection = results.curselection()
            if not selection or selection[0] >= len(visible):
                return "break"
            action = visible[selection[0]][1]
            close()
            self.after_idle(action)
            return "break"

        def move_selection(delta: int) -> str:
            if not visible:
                return "break"
            current = results.curselection()
            index = current[0] if current else 0
            next_index = max(0, min(len(visible) - 1, index + delta))
            results.selection_clear(0, "end")
            results.selection_set(next_index)
            results.activate(next_index)
            results.see(next_index)
            return "break"

        query_var.trace_add("write", refresh)
        results.bind("<Double-Button-1>", execute)
        search.bind("<Return>", execute)
        results.bind("<Return>", execute)
        search.bind("<Down>", lambda _event: move_selection(1))
        search.bind("<Up>", lambda _event: move_selection(-1))
        results.bind("<Up>", lambda _event: move_selection(-1))
        results.bind("<Down>", lambda _event: move_selection(1))
        window.bind("<Escape>", lambda _event: (close(), "break")[1])
        window.protocol("WM_DELETE_WINDOW", close)
        refresh()
        window.update_idletasks()
        width, height = 560, 390
        x = self.winfo_rootx() + max(20, (self.winfo_width() - width) // 2)
        y = self.winfo_rooty() + 70
        window.geometry(f"{width}x{height}+{x}+{y}")
        window.grab_set()
        search.focus_set()

    def _language_snapshot(self) -> tuple[str, object]:
        """Refresh the local, single-document language-service snapshot."""
        uri = self._source_name()
        self._language_version += 1
        self._language_service.open(uri, self._source(), self._language_version)
        return uri, self._language_service.analyze(uri)

    def _symbol_at_cursor(self) -> str | None:
        """Return the identifier touching the caret, without parsing editor markup."""
        try:
            row, column = map(int, self.editor.index("insert").split("."))
            line = self.editor.get(f"{row}.0", f"{row}.end")
        except (tk.TclError, ValueError):
            return None
        matches = list(re.finditer(r"[\wА-Яа-яЁё]+", line, re.UNICODE))
        match = next((item for item in matches if item.start() <= column <= item.end()), None)
        if match is None:
            match = next((item for item in reversed(matches) if item.end() <= column), None)
        return match.group() if match else None

    def _completion_shortcut(self, _event: tk.Event | None = None) -> str:
        self.show_completion()
        return "break"

    def show_completion(self) -> None:
        """Show local REAPER keyword/symbol completion; this is not a cloud AI feature."""
        if self.current_file and self.current_file.suffix.lower() in {".js", ".mjs", ".cjs"}:
            self.status.set("Для JavaScript используйте NOO TAH / Node.js")
            return
        try:
            uri, _analysis = self._language_snapshot()
            row, column = map(int, self.editor.index("insert").split("."))
            line = self.editor.get(f"{row}.0", f"{row}.end")
        except (tk.TclError, ValueError, KeyError) as error:
            self.status.set(f"Автодополнение недоступно: {error}")
            return
        prefix_match = re.search(r"[\wА-Яа-яЁё]+$", line[:column], re.UNICODE)
        prefix = prefix_match.group() if prefix_match else ""
        try:
            candidates = self._language_service.completion(uri, prefix)
        except (KeyError, ValueError) as error:
            self.status.set(f"Автодополнение недоступно: {error}")
            return
        if prefix:
            candidates = [item for item in candidates if item["label"].casefold().startswith(prefix.casefold())]
        candidates = candidates[:24]
        if not candidates:
            self.status.set(f"Нет локальных подсказок для: {prefix or 'текущей позиции'}")
            self._close_completion()
            return

        self._close_completion()
        window = tk.Toplevel(self)
        self._completion_window = window
        window.title("REAPER IntelliSense")
        window.transient(self)
        window.resizable(False, False)
        panel = ttk.Frame(window, padding=8)
        panel.pack(fill="both", expand=True)
        ttk.Label(panel, text="Локальные подсказки REAPER · ↑ ↓ · Enter / Tab · Esc",
                  style="PaneTitle.TLabel").pack(anchor="w", pady=(0, 5))
        items = tk.Listbox(panel, height=min(12, len(candidates)), width=48,
                           activestyle="none", exportselection=False)
        items.pack(fill="both", expand=True)
        for candidate in candidates:
            items.insert("end", f"{candidate['label']}    ·    {candidate['kind']}")
        items.selection_set(0)
        items.activate(0)
        self._completion_list = items
        self._completion_items = candidates
        self._completion_prefix = prefix
        items.bind("<Return>", self._accept_completion)
        items.bind("<Tab>", self._accept_completion)
        items.bind("<Double-Button-1>", self._accept_completion)
        window.bind("<Escape>", lambda _event: (self._close_completion(), "break")[1])
        window.protocol("WM_DELETE_WINDOW", self._close_completion)
        box = self.editor.bbox("insert")
        window.update_idletasks()
        if box:
            x = self.editor.winfo_rootx() + box[0]
            y = self.editor.winfo_rooty() + box[1] + box[3] + 3
        else:
            x = self.winfo_rootx() + 180
            y = self.winfo_rooty() + 120
        window.geometry(f"+{x}+{y}")
        window.grab_set()
        items.focus_set()
        self.status.set(f"IntelliSense: {len(candidates)} локальных кандидатов")

    def _accept_completion(self, _event: tk.Event | None = None) -> str:
        if self._completion_list is None:
            return "break"
        selection = self._completion_list.curselection()
        index = selection[0] if selection else 0
        if index >= len(self._completion_items):
            return "break"
        label = self._completion_items[index]["label"]
        prefix = self._completion_prefix
        try:
            start = self.editor.index(f"insert - {len(prefix)} chars")
            self.editor.edit_separator()
            self.editor.delete(start, "insert")
            self.editor.insert(start, label)
            self.editor.edit_separator()
            self.editor.mark_set("insert", f"{start}+{len(label)}c")
            self.editor.see("insert")
            self.editor.focus_set()
            self._schedule_highlight()
            self._update_cursor_status()
            self.status.set(f"Вставлено: {label}")
        except tk.TclError as error:
            self.status.set(f"Не удалось вставить подсказку: {error}")
        self._close_completion()
        return "break"

    def _close_completion(self) -> None:
        window = self._completion_window
        self._completion_window = None
        self._completion_list = None
        self._completion_items = []
        self._completion_prefix = ""
        if window is not None:
            try:
                if window.winfo_exists():
                    window.grab_release()
                    window.destroy()
            except tk.TclError:
                pass

    def go_to_definition(self) -> None:
        name = self._symbol_at_cursor()
        if not name:
            self.status.set("Поставьте курсор на имя символа")
            return
        uri, _analysis = self._language_snapshot()
        symbol = self._language_service.definition(uri, name)
        if symbol is None:
            self.status.set(f"Определение не найдено в текущем документе: {name}")
            return
        target = f"{symbol.span.line + 1}.{symbol.span.start}"
        self.editor.mark_set("insert", target)
        self.editor.see("insert")
        self.editor.focus_set()
        self._update_cursor_status()
        self.status.set(f"Определение {name}: строка {symbol.span.line + 1}")

    def find_references(self) -> None:
        name = self._symbol_at_cursor()
        if not name:
            self.status.set("Поставьте курсор на имя символа")
            return
        uri, _analysis = self._language_snapshot()
        spans = self._language_service.references(uri, name)
        self.editor.tag_remove("reference", "1.0", "end")
        self.output_tabs.select(0)
        self._append_output(f"REFERENCES · {name} · текущий документ: {len(spans)}")
        for span in spans:
            self.editor.tag_add("reference", f"{span.line + 1}.{span.start}", f"{span.line + 1}.{span.end}")
            self._append_output(f"  {span.line + 1}:{span.start + 1}")
        if spans:
            self.editor.see(f"{spans[0].line + 1}.{spans[0].start}")
        self.status.set(f"Найдено ссылок: {len(spans)} · {name}")

    def rename_symbol(self) -> None:
        name = self._symbol_at_cursor()
        if not name:
            self.status.set("Поставьте курсор на имя символа")
            return
        replacement = simpledialog.askstring(
            "Переименование символа",
            f"Новое имя для {name} (только текущий документ):",
            initialvalue=name,
            parent=self,
        )
        if not replacement or replacement == name:
            return
        uri, _analysis = self._language_snapshot()
        try:
            edits = self._language_service.rename(uri, name, replacement)
        except ValueError as error:
            messagebox.showerror("Переименование символа", str(error), parent=self)
            return
        self.editor.edit_separator()
        for span, value in reversed(edits):
            start = f"{span.line + 1}.{span.start}"
            end = f"{span.line + 1}.{span.end}"
            self.editor.delete(start, end)
            self.editor.insert(start, value)
        self.editor.edit_separator()
        self._schedule_highlight()
        self._update_cursor_status()
        self.status.set(f"Переименовано в текущем документе: {len(edits)} вхождений · {replacement}")

    def show_codex66(self) -> None:
        """Open the native CODEX-66 evidence catalogue."""
        existing = getattr(self, "_codex66_window", None)
        if existing is not None:
            try:
                if existing.winfo_exists():
                    existing.lift()
                    existing.focus_force()
                    return
            except tk.TclError:
                self._codex66_window = None
        commands = {
            "completion": self.show_completion,
            "command_palette": self.show_command_palette,
            "go_to_definition": self.go_to_definition,
            "find_references": self.find_references,
            "rename_symbol": self.rename_symbol,
            "check_source": self.check_source,
            "debug_source": self.debug_source,
            "show_variables": lambda: self.output_tabs.select(1),
            "show_call_stack": lambda: self.output_tabs.select(2),
            "show_plugins": self.show_plugins,
            "run_noo_tah_npm": self.run_noo_tah_npm,
            "show_motion_settings": self.show_motion_settings,
            "toggle_ui_theme": self.toggle_ui_theme,
            "open_folder": self.open_folder,
            "export_catalog": self.export_codex66,
            "show_codex66": self.show_codex66,
        }
        window = Codex66Window(self, commands)
        self._codex66_window = window

    def export_codex66(self) -> None:
        filename = filedialog.asksaveasfilename(
            parent=self, title="Экспорт CODEX-66", defaultextension=".json",
            initialfile="reaper-codex-66.json",
            filetypes=[("JSON", "*.json"), ("Все файлы", "*.*")],
        )
        if not filename:
            return
        try:
            Path(filename).write_text(export_codex66_json(), encoding="utf-8", newline="\n")
        except OSError as error:
            messagebox.showerror("Экспорт CODEX-66", str(error), parent=self)
            return
        self.status.set(f"Экспорт CODEX-66: {filename}")

    def show_motion_settings(self) -> None:
        """Configure persisted motion and low-CPU visual preferences."""
        window = tk.Toplevel(self)
        window.title("Настройки движения интерфейса")
        window.resizable(False, False)
        window.transient(self)
        current = self._motion.preferences
        fade_in_window(window, current, app_key="reaper-studio")
        reduce_var = tk.BooleanVar(value=current.reduce_motion)
        eco_var = tk.BooleanVar(value=current.eco_visuals)
        expressive_var = tk.BooleanVar(value=current.expressive_motion)
        frame = ttk.Frame(window, padding=16)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Кинетика интерфейса", style="PaneTitle.TLabel").pack(anchor="w", pady=(0, 8))
        ttk.Checkbutton(frame, text="Reduce Motion — убрать пространственное движение", variable=reduce_var).pack(anchor="w", pady=4)
        ttk.Checkbutton(frame, text="Eco / Low-CPU Visuals — отключить необязательные эффекты", variable=eco_var).pack(anchor="w", pady=4)
        ttk.Checkbutton(frame, text="Expressive Motion — усиленная пружинная кинетика", variable=expressive_var).pack(anchor="w", pady=4)
        ttk.Checkbutton(frame, text="Sync to Transport / BPM", state="disabled").pack(anchor="w", pady=4)
        ttk.Label(frame, text="REAPER Studio сейчас не содержит аудиотранспорта или мастер-BPM. Синхронизация станет доступна после подключения транспортного API.", wraplength=460).pack(anchor="w", pady=(4, 12))
        buttons = ttk.Frame(frame)
        buttons.pack(fill="x")
        def apply() -> None:
            self._motion.update_preferences(MotionPreferences(reduce_var.get(), eco_var.get(), False, expressive_var.get()))
            window.destroy()
        ttk.Button(buttons, text="Сохранить", style="Primary.TButton", command=apply).pack(side="right")
        ttk.Button(buttons, text="Отмена", command=window.destroy).pack(side="right", padx=(0, 8))
        window.grab_set()
        window.update_idletasks()
        window.geometry(f"+{self.winfo_rootx() + 120}+{self.winfo_rooty() + 100}")

    def show_plugins(self) -> None:
        """Manage and run built-in plugins provided by the REAPER host."""
        window = tk.Toplevel(self)
        window.title("REAPER — менеджер плагинов")
        window.geometry("1040x620")
        window.minsize(760, 460)
        window.transient(self)
        fade_in_window(window, self._motion.preferences, app_key="reaper-studio")
        frame = ttk.Frame(window, padding=12)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Плагины REAPER", style="PaneTitle.TLabel").pack(anchor="w")
        ttk.Label(frame, text="18 встроенных модулей · единый host API · явное включение и запуск").pack(anchor="w", pady=(2, 10))

        table = ttk.Treeview(frame, columns=("domain", "operation", "status"),
                             show="tree headings", selectmode="browse")
        table.heading("#0", text="Плагин")
        table.heading("domain", text="Направление")
        table.heading("operation", text="Основная операция")
        table.heading("status", text="Состояние")
        table.column("#0", width=145, stretch=False)
        table.column("domain", width=175, stretch=False)
        table.column("operation", width=200, stretch=False)
        table.column("status", width=100, stretch=False)
        for item in self.plugin_manager.list_plugins():
            table.insert("", "end", iid=item["plugin_id"], text=item["name"],
                         values=(item["domain"], item["operation"], item["status"]))
        table.pack(fill="both", expand=True)

        footer = ttk.Frame(frame)
        footer.pack(fill="x", pady=(10, 0))
        description = tk.StringVar(value="Выберите плагин, чтобы увидеть его назначение и возможности.")
        ttk.Label(footer, textvariable=description, wraplength=700).pack(side="left", fill="x", expand=True)

        def selected_id() -> str | None:
            selection = table.selection()
            return selection[0] if selection else None

        def update_description(_event: object = None) -> None:
            plugin_id = selected_id()
            if plugin_id is None:
                description.set("Выберите плагин.")
                return
            plugin = self.plugin_manager.get_plugin(plugin_id)
            description.set(f"{plugin.name} · {plugin.version} · {plugin.description} "
                             f"Возможности: {', '.join(plugin.capabilities)}")

        def toggle_plugin() -> None:
            plugin_id = selected_id()
            if plugin_id is None:
                messagebox.showinfo("Плагины", "Сначала выберите плагин.", parent=window)
                return
            enabled = not self.plugin_manager.is_enabled(plugin_id)
            self.plugin_manager.set_enabled(plugin_id, enabled)
            values = list(table.item(plugin_id)["values"])
            values[-1] = "enabled" if enabled else "disabled"
            table.item(plugin_id, values=values)
            update_description()

        def run_plugin() -> None:
            plugin_id = selected_id()
            if plugin_id is None:
                messagebox.showinfo("Плагины", "Сначала выберите плагин.", parent=window)
                return
            raw = simpledialog.askstring(
                "Запуск плагина",
                "Аргументы операции в формате JSON object (для операции без аргументов — {}):",
                initialvalue="{}",
                parent=window,
            )
            if raw is None:
                return
            try:
                arguments = json.loads(raw)
                if not isinstance(arguments, dict):
                    raise PluginError("Аргументы должны быть JSON-объектом.")
                result = self.plugin_manager.run(plugin_id, **arguments)
            except (json.JSONDecodeError, PluginError, ValueError, TypeError) as error:
                messagebox.showerror("Ошибка плагина", str(error), parent=window)
                return
            messagebox.showinfo(f"Плагин {self.plugin_manager.get_plugin(plugin_id).name}",
                                json.dumps(result, ensure_ascii=False, indent=2, default=str),
                                parent=window)

        table.bind("<<TreeviewSelect>>", update_description)
        ttk.Button(footer, text="Включить / отключить", command=toggle_plugin).pack(side="right", padx=(6, 0))
        ttk.Button(footer, text="Запустить…", command=run_plugin).pack(side="right")
        table.selection_set("operandu")
        update_description()

    def _build_toolbar(self) -> None:
        bar = ttk.Frame(self, padding=(10, 8))
        bar.pack(fill="x")
        for label, command in (
            ("Создать", self.new_file), ("Открыть", self.open_file),
            ("Папка", self.open_folder), ("Сохранить", self.save_file),
        ):
            ttk.Button(bar, text=label, command=command, style="Toolbar.TButton").pack(side="left", padx=(0, 4))
        ttk.Separator(bar, orient="vertical").pack(side="left", fill="y", padx=7)
        ttk.Button(bar, text="Проверить", command=self.check_source, style="Toolbar.TButton").pack(side="left", padx=3)
        ttk.Button(bar, text="▶ Запустить", command=self.run_source, style="Toolbar.TButton").pack(side="left", padx=3)
        ttk.Button(bar, text="JS Run", command=self.run_node_source, style="Toolbar.TButton").pack(side="left", padx=3)
        ttk.Button(bar, text="JS Check", command=self.check_node_source, style="Toolbar.TButton").pack(side="left", padx=3)
        ttk.Button(bar, text="JS Debug", command=lambda: self.run_node_source(inspect=True), style="Toolbar.TButton").pack(side="left", padx=3)
        ttk.Button(bar, text="JS Stop", command=self.stop_node_source, style="Toolbar.TButton").pack(side="left", padx=3)
        ttk.Button(bar, text="Отладка", command=self.debug_source, style="Toolbar.TButton").pack(side="left", padx=3)
        ttk.Button(bar, text="Точка остановки", command=self.toggle_breakpoint, style="Toolbar.TButton").pack(side="left", padx=3)
        ttk.Button(bar, text="Атмосфера", command=self.toggle_ui_theme, style="Toolbar.TButton").pack(side="left", padx=3)
        ttk.Button(bar, text="CODEX-66", command=self.show_codex66, style="Toolbar.TButton").pack(side="left", padx=(7, 3))
        self.file_label = tk.StringVar(value="Untitled.rpr")
        ttk.Label(bar, textvariable=self.file_label, style="Muted.TLabel").pack(side="right", padx=8)

    def _build_workspace(self) -> None:
        outer = ttk.Panedwindow(self, orient="horizontal")
        outer.pack(fill="both", expand=True, padx=10, pady=(0, 8))
        project = ttk.Frame(outer, width=245)
        main = ttk.Frame(outer)
        outer.add(project, weight=1)
        outer.add(main, weight=4)

        ttk.Label(project, text="ПРОЕКТ", style="PaneTitle.TLabel", padding=(5, 7)).pack(anchor="w")
        self.project_tree = ttk.Treeview(project, show="tree", selectmode="browse")
        self.project_tree.pack(fill="both", expand=True)
        self.project_tree.bind("<Double-1>", self._open_tree_selection)
        self.project_tree.bind("<Return>", self._open_tree_selection)

        panes = ttk.Panedwindow(main, orient="vertical")
        panes.pack(fill="both", expand=True)
        editor_frame = ttk.Frame(panes)
        output_frame = ttk.Frame(panes)
        panes.add(editor_frame, weight=4)
        panes.add(output_frame, weight=1)
        ttk.Label(editor_frame, text="ИСХОДНЫЙ КОД", style="PaneTitle.TLabel", padding=(4, 5)).pack(anchor="w")

        editor_shell = ttk.Frame(editor_frame)
        editor_shell.pack(fill="both", expand=True)
        self.line_numbers = tk.Canvas(editor_shell, width=48, highlightthickness=0, background="#f1f5f9")
        self.line_numbers.pack(side="left", fill="y")
        self.editor = ScrolledText(
            editor_shell, wrap="none", undo=True, maxundo=-1,
            font=("Cascadia Code", 11), tabs=("4c",), padx=10, pady=8,
        )
        self.editor.pack(side="left", fill="both", expand=True)
        self.editor.tag_configure("keyword", foreground="#7c3aed")
        self.editor.tag_configure("string", foreground="#0f766e")
        self.editor.tag_configure("number", foreground="#b45309")
        self.editor.tag_configure("comment", foreground="#64748b", font=("Cascadia Code", 10, "italic"))
        self.editor.tag_configure("reference", background="#FDE68A", foreground="#0A1E46")
        self.editor.bind("<<Modified>>", self._on_modified)
        self.editor.bind("<KeyRelease>", self._on_editor_key)
        self.editor.bind("<MouseWheel>", self._redraw_line_numbers)
        self.editor.bind("<ButtonRelease-1>", self._update_cursor_status)
        self.editor.bind("<Configure>", self._redraw_line_numbers)
        self.editor.bind("<Control-space>", self._completion_shortcut)

        header = ttk.Frame(output_frame)
        header.pack(fill="x")
        ttk.Label(header, text="ВЫВОД / ОТЛАДКА", style="PaneTitle.TLabel", padding=(5, 6)).pack(side="left")
        ttk.Button(header, text="Очистить", command=self.clear_output).pack(side="right", padx=4)
        tabs = ttk.Notebook(output_frame)
        tabs.pack(fill="both", expand=True)
        output_page = ttk.Frame(tabs)
        variables_page = ttk.Frame(tabs)
        stack_page = ttk.Frame(tabs)
        types_page = ttk.Frame(tabs)
        tabs.add(output_page, text="Вывод")
        tabs.add(variables_page, text="Переменные")
        tabs.add(stack_page, text="Стек вызовов")
        tabs.add(types_page, text="Типы / Диагностика")
        self.output_tabs = tabs
        self.output = ScrolledText(output_page, height=9, wrap="word", font=("Cascadia Code", 9), state="disabled")
        self.output.pack(fill="both", expand=True)
        self.type_view = ttk.Treeview(
            types_page,
            columns=("file", "line", "column", "severity", "code", "message"),
            show="headings",
            selectmode="browse",
        )
        for column, heading, width, stretch in (
            ("file", "Файл", 190, False),
            ("line", "Строка", 65, False),
            ("column", "Колонка", 70, False),
            ("severity", "Уровень", 95, False),
            ("code", "Код", 110, False),
            ("message", "Диагностика", 550, True),
        ):
            self.type_view.heading(column, text=heading)
            self.type_view.column(
                column, width=width,
                anchor="w" if column in {"file", "code", "message"} else "center",
                stretch=stretch,
            )
        self.type_view.pack(fill="both", expand=True)
        self.type_view.bind("<Double-1>", self._open_type_diagnostic)
        self.variables_view = ttk.Treeview(variables_page, columns=("value",), show="tree headings")
        self.variables_view.heading("#0", text="Имя")
        self.variables_view.heading("value", text="Значение")
        self.variables_view.column("#0", width=220, stretch=True)
        self.variables_view.column("value", width=520, stretch=True)
        self.variables_view.pack(fill="both", expand=True)
        self.stack_view = tk.Listbox(stack_page, font=("Cascadia Code", 10))
        self.stack_view.pack(fill="both", expand=True)

    def _build_statusbar(self) -> None:
        self.status = tk.StringVar(value="Готово · Reaper Studio")
        self.cursor_status = tk.StringVar(value="Стр. 1, Столб. 1")
        bar = ttk.Frame(self, padding=(8, 4))
        bar.pack(fill="x")
        ttk.Label(bar, textvariable=self.status, anchor="w").pack(side="left", fill="x", expand=True)
        ttk.Label(bar, textvariable=self.cursor_status, anchor="e").pack(side="right")

    def _bind_shortcuts(self) -> None:
        bindings = {
            "<Control-n>": self.new_file, "<Control-o>": self.open_file,
            "<Control-s>": self.save_file, "<Control-Shift-S>": self.save_as,
            "<Control-f>": self.find_text, "<Control-g>": self.goto_line,
            "<F5>": self.run_source, "<Shift-F5>": self.check_source,
            "<F9>": self.toggle_breakpoint, "<F12>": self.go_to_definition,
            "<Control-Shift-R>": self.rename_symbol,
            "<Control-Alt-k>": self.show_codex66,
        }
        for sequence, callback in bindings.items():
            self.bind_all(sequence, lambda _event, fn=callback: (fn(), "break")[1])

    def _insert_starter(self) -> None:
        self.editor.insert("1.0", STARTER)
        self.editor.edit_modified(False)
        self._dirty = False
        self._refresh_title()
        self._schedule_highlight()
        self._redraw_line_numbers()

    def apply_visual_theme(self) -> None:
        mode = self._theme_mode.get()
        if mode == "system":
            colors = apply_ui_theme(self, "system")
            self._theme_name = colors["mode"]
        else:
            self._theme_name = apply_theme(self, "reaper-studio", mode)
        self._apply_editor_visuals()

    def _apply_editor_visuals(self) -> None:
        """Keep the code editor, syntax colors and line gutter in the active theme."""
        palette = getattr(self, "_anatidae_palette", {})
        theme_name = getattr(self, "_anatidae_theme", self._theme_name)
        dark = theme_name in {"dark", "night"}

        editor_bg = palette.get("surface", "#0F2A45" if dark else "#FFFFFF")
        editor_fg = palette.get("fg", "#E8EDF2" if dark else "#122C45")
        gutter_bg = palette.get("elevated", "#173A5E" if dark else "#EAF1FA")
        border = palette.get("border", "#31516F" if dark else "#CAD8E8")
        focus = palette.get("focus", palette.get("blue", "#70A5FF" if dark else "#004E98"))
        selection = palette.get("selection", "#244F82" if dark else "#D9E8FF")
        selection_fg = palette.get("selection_fg", editor_fg)

        self.editor.configure(
            background=editor_bg,
            foreground=editor_fg,
            insertbackground=editor_fg,
            selectbackground=selection,
            selectforeground=selection_fg,
            highlightbackground=border,
            highlightcolor=focus,
            highlightthickness=1,
            borderwidth=0,
        )
        self.line_numbers.configure(
            background=gutter_bg,
            highlightbackground=border,
            highlightcolor=focus,
            highlightthickness=1,
        )

        syntax = (
            {"keyword": "#C4B5FD", "string": "#5EEAD4",
             "number": "#FCD34D", "comment": "#A7B4C7"}
            if dark else
            {"keyword": "#6D28D9", "string": "#0F766E",
             "number": "#92400E", "comment": "#64748B"}
        )
        for token, color in syntax.items():
            self.editor.tag_configure(token, foreground=color)
        self.editor.tag_configure(
            "comment", foreground=syntax["comment"],
            font=("Cascadia Code", 10, "italic")
        )
        self.editor.tag_configure(
            "reference", background=selection, foreground=selection_fg
        )
        self._redraw_line_numbers()

    def toggle_ui_theme(self) -> None:
        self._theme_name = toggle_theme(self, "reaper-studio")
        self._theme_mode.set(self._theme_name)
        self._apply_editor_visuals()

    def _source_name(self) -> str:
        return str(self.current_file) if self.current_file else "<editor>"

    def _source(self) -> str:
        return self.editor.get("1.0", "end-1c")

    def _refresh_title(self) -> None:
        name = self.current_file.name if self.current_file else "Untitled.rpr"
        marker = " •" if self._dirty else ""
        self.file_label.set(name + marker)
        self.title(f"{APP_TITLE} — {name}{marker}")

    def _on_modified(self, _event: tk.Event | None = None) -> None:
        if self.editor.edit_modified():
            self._dirty = True
            self.editor.edit_modified(False)
            self._refresh_title()
            self._redraw_line_numbers()

    def _on_editor_key(self, _event: tk.Event | None = None) -> None:
        self._schedule_highlight()
        self._update_cursor_status()

    def _confirm_discard(self) -> bool:
        if not self._dirty:
            return True
        answer = messagebox.askyesnocancel("Несохранённые изменения", "Сохранить изменения перед продолжением?", parent=self)
        if answer is None:
            return False
        return self.save_file() if answer else True

    def new_file(self) -> None:
        if not self._confirm_discard():
            return
        self.current_file = None
        self.editor.delete("1.0", "end")
        self._dirty = False
        self._refresh_title()
        self.clear_output()
        self.status.set("Создан новый файл")
        self._schedule_highlight()

    def open_file(self) -> None:
        if not self._confirm_discard():
            return
        filename = filedialog.askopenfilename(
            parent=self, filetypes=[("Reaper / JavaScript", "*.rpr *.most *.js *.mjs *.cjs"), ("Reaper / MOST", "*.rpr *.most"), ("JavaScript", "*.js *.mjs *.cjs"), ("Все файлы", "*.*")]
        )
        if filename:
            self._load_file(Path(filename))

    def _load_file(self, path: Path) -> None:
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            messagebox.showerror("Не удалось открыть файл", str(error), parent=self)
            return
        self.current_file = path
        self.editor.delete("1.0", "end")
        self.editor.insert("1.0", content)
        self.editor.edit_modified(False)
        self._dirty = False
        self._refresh_title()
        self.status.set(f"Открыт: {path}")
        self._schedule_highlight()

    def save_file(self) -> bool:
        return self.save_as() if self.current_file is None else self._write_file(self.current_file)

    def save_as(self) -> bool:
        filename = filedialog.asksaveasfilename(
            parent=self, defaultextension=".rpr",
            filetypes=[("Reaper source", "*.rpr"), ("MOST source", "*.most"), ("Все файлы", "*.*")]
        )
        if not filename:
            return False
        path = Path(filename)
        if path.suffix.lower() not in SOURCE_EXTENSIONS and path.suffix.lower() not in {".js", ".mjs", ".cjs"}:
            path = path.with_suffix(".rpr")
        if not self._write_file(path):
            return False
        self.current_file = path
        self._refresh_title()
        return True

    def _write_file(self, path: Path) -> bool:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(self._source(), encoding="utf-8", newline="\n")
        except OSError as error:
            messagebox.showerror("Не удалось сохранить файл", str(error), parent=self)
            return False
        self._dirty = False
        self.editor.edit_modified(False)
        self._refresh_title()
        self.status.set(f"Сохранено: {path}")
        return True

    def open_folder(self) -> None:
        folder = filedialog.askdirectory(parent=self, title="Открыть папку проекта")
        if not folder:
            return
        self.project_root = Path(folder)
        self._populate_project_tree()
        self.status.set(f"Проект: {self.project_root}")

    def _populate_project_tree(self) -> None:
        self.project_tree.delete(*self.project_tree.get_children())
        if self.project_root is None:
            return
        root_id = self.project_tree.insert("", "end", text=self.project_root.name, values=(str(self.project_root),), open=True)
        self._project_entries_remaining = 2000
        self._add_project_children(root_id, self.project_root, 0)

    def _add_project_children(self, parent: str, folder: Path, depth: int) -> None:
        if depth >= 4 or self._project_entries_remaining <= 0:
            return
        for entry in iter_project_entries(folder, max_depth=1, max_entries=self._project_entries_remaining):
            self._project_entries_remaining -= 1
            item = self.project_tree.insert(
                parent, "end",
                text=("▸ " if entry.is_directory else "  ") + entry.path.name,
                values=(str(entry.path),),
            )
            if entry.is_directory:
                self._add_project_children(item, entry.path, depth + 1)

    def _open_tree_selection(self, _event: tk.Event | None = None) -> None:
        selected = self.project_tree.selection()
        if not selected:
            return
        values = self.project_tree.item(selected[0], "values")
        if values:
            path = Path(values[0])
            if path.is_file() and self._confirm_discard():
                self._load_file(path)

    def _append_output(self, line: str) -> None:
        self.output.configure(state="normal")
        self.output.insert("end", str(line) + "\n")
        self.output.see("end")
        self.output.configure(state="disabled")

    def clear_output(self) -> None:
        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        self.output.configure(state="disabled")

    def _open_type_diagnostic(self, _event: tk.Event | None = None) -> None:
        selected = self.type_view.selection()
        if not selected:
            return
        values = self.type_view.item(selected[0], "values")
        if not values:
            return
        try:
            line = max(1, int(values[1]))
            column = max(1, int(values[2]))
            location = f"{line}.{column - 1}"
            self.editor.mark_set("insert", location)
            self.editor.see(location)
            self.editor.focus_set()
            self._update_cursor_status()
        except (tk.TclError, ValueError, IndexError):
            return

    def _show_type_diagnostics(
        self,
        diagnostics: list[Any],
        *,
        source_file: str | Path | None = None,
    ) -> int:
        self.type_view.delete(*self.type_view.get_children())
        errors = 0
        records = normalize_diagnostics(
            source_file if source_file is not None else self._source_name(),
            diagnostics,
        )
        for index, item in enumerate(records):
            if item.severity == "error":
                errors += 1
            self.type_view.insert(
                "",
                "end",
                iid=f"type-{index}",
                values=(
                    item.file,
                    item.start_line,
                    item.start_column,
                    item.severity.upper(),
                    item.code,
                    item.message,
                ),
            )
        return errors

    def check_source(self) -> None:
        if self.current_file and self.current_file.suffix.lower() in {".js", ".mjs", ".cjs"}:
            self.check_node_source()
            return
        try:
            tree = parse(self._source(), self._source_name())
            from reaper.typecheck import TypeChecker

            checked = TypeChecker(self._source_name()).check(tree)
        except ReaperError as error:
            self.type_view.delete(*self.type_view.get_children())
            self._append_output(f"CHECK FAILED: {error}")
            self.status.set("Проверка исходного кода не пройдена")
            self.output_tabs.select(0)
            return

        error_count = self._show_type_diagnostics(list(checked.diagnostics), source_file=self._source_name())
        self._append_output(
            f"CHECK: {self._source_name()} — синтаксис корректен; "
            f"типовых ошибок: {error_count}; диагностик: {len(checked.diagnostics)}"
        )
        if error_count:
            for item in checked.diagnostics:
                if item.severity == "error":
                    self._append_output(
                        f"{item.code} ({item.line}:{item.column}): {item.message}"
                    )
            self.output_tabs.select(3)
            self.status.set(f"Проверка типов не пройдена · {error_count} ошибок")
            return

        self.output_tabs.select(0)
        self.status.set("Синтаксис и поддерживаемые типы проверены")

    def run_source(self) -> None:
        if self.current_file and self.current_file.suffix.lower() in {".js", ".mjs", ".cjs"}:
            self.run_node_source()
            return
        if self._running:
            self.status.set("Программа уже выполняется")
            return
        source, filename = self._source(), self._source_name()
        self.clear_output()
        self._running = True
        self.status.set("Выполнение в фоновом потоке…")

        def worker() -> None:
            try:
                Interpreter(output=lambda line: self._run_queue.put(("line", str(line)))).run(source, filename)
            except ReaperError as error:
                self._run_queue.put(("error", str(error)))
            except Exception as error:
                self._run_queue.put(("error", f"{type(error).__name__}: {error}"))
            else:
                self._run_queue.put(("done", "Выполнение завершено"))
        threading.Thread(target=worker, name="reaper-studio-runner", daemon=True).start()

    def _drain_run_queue(self) -> None:
        try:
            while True:
                kind, payload = self._run_queue.get_nowait()
                if kind == "line":
                    self._append_output(str(payload))
                elif kind == "error":
                    self._append_output(f"RUNTIME ERROR: {payload}")
                    self._running = False
                    self.status.set("Ошибка выполнения")
                elif kind == "done":
                    self._running = False
                    self.status.set(str(payload))
                elif kind == "node-error":
                    self._running = False
                    self._node_process = None
                    self._append_output(f"NOO TAH ERROR: {payload}")
                    self.status.set("Node.js process failed")
                elif kind == "embedded":
                    self._finish_embedded_build(payload if isinstance(payload, dict) else None, None)
                elif kind == "embedded-error":
                    self._finish_embedded_build(None, str(payload))
        except queue.Empty:
            pass
        if not self._closing:
            self.after(50, self._drain_run_queue)

    def toggle_breakpoint(self) -> None:
        line = int(self.editor.index("insert").split(".")[0])
        if line in self.breakpoints:
            self.breakpoints.remove(line)
            self.status.set(f"Точка остановки удалена: {line}")
        else:
            self.breakpoints.add(line)
            self.status.set(f"Точка остановки добавлена: {line}")
        self._append_output("Точки остановки: " + (", ".join(map(str, sorted(self.breakpoints))) or "нет"))

    def _pause_for_debug(self, snapshot: Any) -> None:
        self.variables_view.delete(*self.variables_view.get_children())
        for name, value in snapshot.variables.items():
            rendered = repr(value)
            self.variables_view.insert("", "end", text=name, values=(rendered[:237] + "..." if len(rendered) > 240 else rendered,))
        self.stack_view.delete(0, "end")
        for index, name in enumerate(snapshot.call_stack):
            self.stack_view.insert("end", f"{index}: {name}")
        if not snapshot.call_stack:
            self.stack_view.insert("end", "<module>")
        self.output_tabs.select(1)
        self.status.set(f"Пауза: {snapshot.filename}:{snapshot.line}:{snapshot.column}")
        self._debug_wait = True
        self._debug_signal.set(False)
        while self._debug_wait:
            self.wait_variable(self._debug_signal)

    def _release_debugger(self, step: bool = False, stop: bool = False) -> None:
        if self.debugger is None or not self._debug_wait:
            return
        if stop:
            self.debugger.stop()
        elif step:
            self.debugger.step()
        else:
            self.debugger.continue_execution()
        self._debug_wait = False
        self._debug_signal.set(True)

    def continue_debug(self) -> None:
        self._release_debugger()

    def step_debug(self) -> None:
        self._release_debugger(step=True)

    def stop_debug(self) -> None:
        self._release_debugger(stop=True)

    def _run_with_debugger(self, first_step: bool = False) -> None:
        if self._running:
            self.status.set("Другая программа уже выполняется")
            return
        self.clear_output()
        debugger = RuntimeDebugger(self.breakpoints, self._pause_for_debug)
        if first_step:
            debugger.step()
        self.debugger = debugger
        try:
            Interpreter(output=self._append_output, debugger=debugger).run(self._source(), self._source_name())
        except DebuggerStopped:
            self.status.set("Отладка остановлена")
        except ReaperError as error:
            self._append_output(f"RUNTIME ERROR: {error}")
            self.status.set("Ошибка выполнения")
            return
        finally:
            self.debugger = None
            self._debug_wait = False
        if not debugger.stop_requested:
            self.status.set("Выполнение завершено")

    def debug_source(self) -> None:
        if self.current_file and self.current_file.suffix.lower() in {".js", ".mjs", ".cjs"}:
            self.run_node_source(inspect=True)
            return
        self._run_with_debugger(first_step=True)


    def _node_file(self) -> Path | None:
        if self.current_file and self.current_file.suffix.lower() in {".js", ".mjs", ".cjs"}:
            return self.current_file
        filename = filedialog.askopenfilename(
            parent=self, filetypes=[("JavaScript", "*.js *.mjs *.cjs"), ("All files", "*.*")]
        )
        return Path(filename) if filename else None

    def check_node_source(self) -> None:
        file = self._node_file()
        if file is None:
            return
        if self._dirty and self.current_file == file and not self.save_file():
            return
        try:
            runtime = NooTahRuntime.discover()
            result = runtime.command(["--check", str(file)], cwd=file.parent)
        except (RuntimeError, OSError) as error:
            self._append_output(f"NOO TAH: {error}")
            self.status.set("Node.js runtime unavailable")
            return
        if result.stdout:
            self._append_output(result.stdout.rstrip())
        if result.stderr:
            self._append_output(result.stderr.rstrip())
        self._append_output("NOO TAH CHECK: passed" if result.returncode == 0 else f"NOO TAH CHECK: failed ({result.returncode})")
        self.status.set("JavaScript syntax check passed" if result.returncode == 0 else "JavaScript syntax check failed")

    def run_node_source(self, inspect: bool = False) -> None:
        file = self._node_file()
        if file is None:
            return
        if self._running:
            self.status.set("Другая программа уже выполняется")
            return
        if self._dirty and self.current_file == file and not self.save_file():
            return
        try:
            runtime = NooTahRuntime.discover()
            command = [runtime.node]
            if inspect:
                command.append("--inspect-brk=127.0.0.1:9229")
            command.append(str(file))
            process = subprocess.Popen(
                command, cwd=str(file.parent),
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace", bufsize=1,
            )
        except (RuntimeError, OSError) as error:
            self._append_output(f"NOO TAH: {error}")
            self.status.set("Node.js process could not start")
            return
        self._node_process = process
        self._running = True
        self.clear_output()
        self.status.set(f"NOO TAH running: {file.name}")
        self._append_output(f"NOO TAH START: {file}")
        if inspect:
            self._append_output("Node Inspector: open chrome://inspect and attach to 127.0.0.1:9229")
        def pump() -> None:
            try:
                assert process.stdout is not None
                for line in process.stdout:
                    self._run_queue.put(("line", line.rstrip("\r\n")))
                code = process.wait()
                self._run_queue.put(("done", f"Node.js process exited ({code})"))
            except Exception as error:
                self._run_queue.put(("node-error", f"{type(error).__name__}: {error}"))
        threading.Thread(target=pump, name="noo-tah-process", daemon=True).start()


    def run_noo_tah_npm(self) -> None:
        command_text = simpledialog.askstring(
            "NOO TAH / npm", "npm arguments (example: run build):",
            initialvalue="run build", parent=self,
        )
        if not command_text:
            return
        if self._running:
            self.status.set("Другая программа уже выполняется")
            return
        import shlex
        try:
            runtime = NooTahRuntime.discover()
            if not runtime.npm_cli:
                raise RuntimeError("npm CLI was not found in this Node.js installation")
            cwd = self.project_root or (self.current_file.parent if self.current_file else Path.cwd())
            process = subprocess.Popen(
                [runtime.node, runtime.npm_cli, *shlex.split(command_text)],
                cwd=str(cwd), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace", bufsize=1,
            )
        except (RuntimeError, OSError, ValueError) as error:
            self._append_output(f"NOO TAH npm: {error}")
            self.status.set("npm command could not start")
            return
        self._node_process = process
        self._running = True
        self.status.set(f"npm: {command_text}")
        self._append_output(f"NOO TAH npm START: {command_text} ({cwd})")
        def pump() -> None:
            try:
                assert process.stdout is not None
                for line in process.stdout:
                    self._run_queue.put(("line", line.rstrip()))
                code = process.wait()
                self._run_queue.put(("done", f"npm exited ({code})"))
            except Exception as error:
                self._run_queue.put(("node-error", f"{type(error).__name__}: {error}"))
        threading.Thread(target=pump, name="noo-tah-npm", daemon=True).start()

    def stop_node_source(self) -> None:
        process = self._node_process
        if process is None or process.poll() is not None:
            self.status.set("No active NOO TAH process")
            return
        process.terminate()
        self._append_output("NOO TAH: termination requested")
        self.status.set("Stopping Node.js process")

    def noo_tah_doctor(self) -> None:
        def worker() -> None:
            try:
                report = NooTahRuntime.discover().doctor()
                import json
                self._run_queue.put(("line", json.dumps(report, indent=2)))
                self._run_queue.put(("done", "NOO TAH runtime diagnostics completed"))
            except Exception as error:
                self._run_queue.put(("node-error", str(error)))
        if self._running:
            self.status.set("Другая программа уже выполняется")
            return
        self._running = True
        threading.Thread(target=worker, name="noo-tah-doctor", daemon=True).start()

    def find_text(self) -> None:
        needle = simpledialog.askstring("Найти", "Текст для поиска:", parent=self)
        if not needle:
            return
        self.editor.tag_remove("sel", "1.0", "end")
        start = self.editor.index("insert")
        found = self.editor.search(needle, start, stopindex="end", nocase=True)
        if not found:
            found = self.editor.search(needle, "1.0", stopindex=start, nocase=True)
        if found:
            end = f"{found}+{len(needle)}c"
            self.editor.tag_add("sel", found, end)
            self.editor.mark_set("insert", end)
            self.editor.see(found)
            self.editor.focus_set()
        else:
            self.status.set(f"Не найдено: {needle}")

    def goto_line(self) -> None:
        line = simpledialog.askinteger("Перейти к строке", "Номер строки:", parent=self, minvalue=1)
        if line is None:
            return
        self.editor.mark_set("insert", f"{line}.0")
        self.editor.see("insert")
        self.editor.focus_set()
        self._update_cursor_status()

    def _schedule_highlight(self, _event: tk.Event | None = None) -> None:
        if self._highlight_job is not None:
            try:
                self.after_cancel(self._highlight_job)
            except tk.TclError:
                pass
        self._highlight_job = self.after(120, self._highlight_source)

    def _highlight_source(self) -> None:
        self._highlight_job = None
        for tag in ("keyword", "string", "number", "comment"):
            self.editor.tag_remove(tag, "1.0", "end")
        source = self._source()
        for span in highlight_spans(source):
            self.editor.tag_add(
                span.kind,
                f"1.0+{span.start}c",
                f"1.0+{span.end}c",
            )
        self._redraw_line_numbers()

    def _redraw_line_numbers(self, _event: tk.Event | None = None) -> None:
        if not hasattr(self, "line_numbers"):
            return
        palette = getattr(self, "_anatidae_palette", {})
        line_number_color = palette.get("muted", "#94a3b8")
        self.line_numbers.delete("all")
        try:
            index = self.editor.index("@0,0")
            while True:
                info = self.editor.dlineinfo(index)
                if info is None:
                    break
                self.line_numbers.create_text(
                    40,
                    info[1],
                    anchor="ne",
                    text=index.split(".")[0],
                    fill=line_number_color,
                    font=("Cascadia Code", 9),
                )
                index = self.editor.index(f"{index}+1line")
                if self.editor.compare(index, ">", "end-1c"):
                    break
        except tk.TclError:
            return

    def _update_cursor_status(self, _event: tk.Event | None = None) -> None:
        try:
            line, column = self.editor.index("insert").split(".")
            self.cursor_status.set(f"Стр. {line}, Столб. {int(column) + 1}")
        except (tk.TclError, ValueError):
            pass
        self._redraw_line_numbers()

    def show_hardware_overview(self) -> None:
        """Show supported embedded profiles and the current hardware boundary."""
        window = tk.Toplevel(self)
        window.title("Reaper — Systems & Hardware")
        window.geometry("880x560")
        window.minsize(720, 440)
        window.transient(self)

        frame = ttk.Frame(window, padding=16)
        frame.pack(fill="both", expand=True)
        ttk.Label(
            frame,
            text="Системное программирование и аппаратные цели",
            style="PaneTitle.TLabel",
        ).pack(anchor="w", pady=(0, 6))
        ttk.Label(
            frame,
            text=(
                "Reaper развивается как системный язык для firmware, embedded и платформенного ПО. "
                "Текущие профили помогают подготовить проект и linker layout; они не означают, "
                "что плата подключена или физическое устройство доступно."
            ),
            wraplength=820,
            justify="left",
        ).pack(anchor="w", pady=(0, 14))

        columns = ("target", "architecture", "clock", "flash", "sram", "compiler")
        table = ttk.Treeview(frame, columns=columns, show="headings", height=6)
        headings = {
            "target": ("Профиль", 170),
            "architecture": ("Архитектура", 130),
            "clock": ("Частота", 110),
            "flash": ("FLASH", 160),
            "sram": ("SRAM", 150),
            "compiler": ("Компилятор", 150),
        }
        for column, (label, width) in headings.items():
            table.heading(column, text=label)
            table.column(column, width=width, anchor="w")
        table.pack(fill="x", expand=False)

        for profile in list_embedded_profiles():
            flash = profile["flash"]
            sram = profile["sram"]
            table.insert("", "end", values=(
                profile["id"],
                profile["architecture"],
                f"{profile['clock_hz']:,} Hz",
                f"0x{flash['base']:08X} · {flash['size']:,} B",
                f"0x{sram['base']:08X} · {sram['size']:,} B",
                profile["compiler"],
            ))

        ttk.Separator(frame).pack(fill="x", pady=14)
        status = (
            "ДОСТУПНО: MCU-профили, проверка Flash/SRAM, генерация linker.ld и вызов "
            "установленного cross-compiler; MMIO descriptor API с проверкой границ, "
            "выравнивания, доступа и capabilities через host adapter.\n\n"
            "ОГРАНИЧЕНИЯ: Studio пока не читает физические регистры в реальном времени, "
            "не регистрирует IRQ, не выделяет DMA-буферы, не устанавливает драйверы "
            "и не прошивает платы автоматически. Текущий MMIO API сам по себе не "
            "отображает физическую память."
        )
        details = ScrolledText(frame, height=7, wrap="word", padx=10, pady=8)
        details.pack(fill="both", expand=True)
        details.insert("1.0", status)
        details.configure(state="disabled")

        buttons = ttk.Frame(frame)
        buttons.pack(fill="x", pady=(12, 0))
        ttk.Button(
            buttons, text="Создать embedded-проект",
            command=lambda: (window.destroy(), self.embedded_new_project()),
        ).pack(side="left")
        ttk.Button(
            buttons, text="Проверить существующий профиль",
            command=lambda: (window.destroy(), self.embedded_inspect_project()),
        ).pack(side="left", padx=(8, 0))
        ttk.Button(buttons, text="Закрыть", command=window.destroy).pack(side="right")
        window.grab_set()

    def embedded_new_project(self) -> None:
        directory = filedialog.askdirectory(parent=self, title="Создать проект встроенной C")
        if not directory:
            return
        try:
            root = embedded_init_project(directory)
        except (EmbeddedError, OSError, ValueError) as error:
            messagebox.showerror("Проект встроенной C", str(error), parent=self)
            return
        self._append_output(f"EMBEDDED: создан проект {root}")
        self._append_output("Проверьте embedded.json и linker.ld по документации конкретного MCU.")

    def embedded_inspect_project(self) -> None:
        directory = filedialog.askdirectory(parent=self, title="Выбрать проект встроенной C")
        if not directory:
            return
        try:
            report = embedded_inspect_project(directory)
        except (EmbeddedError, OSError, ValueError) as error:
            messagebox.showerror("Профиль встроенной C", str(error), parent=self)
            return
        profile = report["profile"]
        self._append_output(
            f"MCU: {profile['id']} | {profile['architecture']} | {profile['clock_hz']} Hz | "
            f"toolchain {'найден' if report['toolchain'] else 'не найден'}"
        )
        self._append_output(
            f"FLASH: {profile['flash']['size']} bytes | SRAM: {profile['sram']['size']} bytes | "
            f"stack reserve: {profile['stack_bytes']} bytes"
        )

    def embedded_build(self) -> None:
        directory = filedialog.askdirectory(parent=self, title="Выбрать проект встроенной C для сборки")
        if not directory:
            return
        self._append_output(f"EMBEDDED: сборка {directory}…")
        def worker() -> None:
            try:
                result = embedded_build_project(directory)
            except Exception as error:
                self._run_queue.put(("embedded-error", str(error)))
            else:
                self._run_queue.put(("embedded", result))
        threading.Thread(target=worker, name="reaper-embedded-build", daemon=True).start()

    def _finish_embedded_build(self, result: dict[str, object] | None, error: str | None) -> None:
        if error:
            self._append_output(f"EMBEDDED BUILD FAILED: {error}")
            self.status.set("Сборка встроенного проекта завершилась с ошибкой")
            return
        if result is None:
            return
        self._append_output(f"EMBEDDED BUILD: {'OVER BUDGET' if result['over_budget'] else 'success'}")
        for kind, path in result["artifacts"].items():
            self._append_output(f"{kind}: {path}")
        budget = result["budget"]
        self._append_output(
            f"FLASH: {budget['flash_used']}/{budget['flash_total']} bytes ({budget['flash_percent']}%) | "
            f"SRAM incl. stack: {budget['sram_used_with_stack']}/{budget['sram_total']} bytes ({budget['sram_percent']}%)"
        )
        self.status.set("Сборка встроенного проекта завершена" if not result["over_budget"] else "Образ превышает заданный объём памяти")

    def _on_close(self) -> None:
        if not self._confirm_discard():
            return
        if self._running and not messagebox.askyesno("Программа выполняется", "Закрыть IDE во время выполнения?", parent=self):
            return
        if self._debug_wait:
            self.stop_debug()
        if self._node_process and self._node_process.poll() is None:
            self._node_process.terminate()
        self._closing = True
        self._close_completion()
        self._language_service.shutdown()
        self.destroy()


def main() -> int:
    ReaperStudio().mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
