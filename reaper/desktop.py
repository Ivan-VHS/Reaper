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
from tkinter import filedialog, messagebox, simpledialog, ttk
from tkinter.scrolledtext import ScrolledText
from typing import Any

from reaper.noo_tah import Runtime as NooTahRuntime
from reaper.embedded import (
    EmbeddedError,
    build_project as embedded_build_project,
    init_project as embedded_init_project,
    inspect_project as embedded_inspect_project,
)
from reaper.errors import ReaperError
from reaper.parser import parse
from reaper.runtime import Interpreter
from reaper.debugger import DebuggerStopped, RuntimeDebugger
from reaper.plugins import PluginError, PluginManager
from reaper.ide_support import SOURCE_EXTENSIONS, highlight_spans, iter_project_entries
from reaper.ui_motion import MotionController
from reaper.ui_theme import apply_theme, apply_ui_theme, set_dpi_awareness, toggle_theme

APP_TITLE = "Reaper Studio"
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

        self._configure_styles()
        self._build_menu()
        self._build_toolbar()
        self._build_workspace()
        self._build_statusbar()
        self._motion = MotionController(self)
        self._motion.fade_in()
        self._bind_shortcuts()
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
        style.configure("PaneTitle.TLabel", font=("Segoe UI Semibold", 9))
        style.configure("Toolbar.TButton", padding=(9, 5))

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
        edit_menu.add_separator()
        edit_menu.add_command(label="Выделить всё", command=lambda: self.editor.tag_add("sel", "1.0", "end-1c"))
        edit_menu.add_command(label="Отменить", command=lambda: self.editor.edit_undo(), accelerator="Ctrl+Z")
        edit_menu.add_command(label="Повторить", command=lambda: self.editor.edit_redo(), accelerator="Ctrl+Y")
        menu.add_cascade(label="Правка", menu=edit_menu)

        run_menu = tk.Menu(menu, tearoff=False)
        run_menu.add_command(label="Проверить исходный код", command=self.check_source, accelerator="Shift+F5")
        run_menu.add_command(label="Запустить", command=self.run_source, accelerator="F5")
        run_menu.add_command(label="Отладка с первого шага", command=self.debug_source)
        run_menu.add_command(label="Точка останова", command=self.toggle_breakpoint, accelerator="F9")
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
        embedded_menu.add_command(label="Создать проект встроенной C…", command=self.embedded_new_project)
        embedded_menu.add_command(label="Проверить профиль микроконтроллера…", command=self.embedded_inspect_project)
        embedded_menu.add_command(label="Собрать прошивку…", command=self.embedded_build)
        menu.add_cascade(label="Встроенная C", menu=embedded_menu)

        plugin_menu = tk.Menu(menu, tearoff=False)
        plugin_menu.add_command(label="Менеджер плагинов…", command=self.show_plugins)
        menu.add_cascade(label="Плагины", menu=plugin_menu)
        view_menu = tk.Menu(menu, tearoff=False)
        for mode, label in (("system", "Системная"), ("light", "Светлая"), ("dark", "Тёмная")):
            view_menu.add_radiobutton(label=label, variable=self._theme_mode, value=mode, command=self.apply_visual_theme)
        menu.add_cascade(label="Вид", menu=view_menu)
        self.configure(menu=menu)

    def show_plugins(self) -> None:
        """Manage and run built-in plugins provided by the REAPER host."""
        window = tk.Toplevel(self)
        window.title("REAPER — менеджер плагинов")
        window.geometry("1040x620")
        window.minsize(760, 460)
        window.transient(self)
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
        ttk.Button(bar, text="Точка останова", command=self.toggle_breakpoint, style="Toolbar.TButton").pack(side="left", padx=3)
        ttk.Button(bar, text="Тёмная тема", command=self.toggle_ui_theme, style="Toolbar.TButton").pack(side="left", padx=3)
        self.file_label = tk.StringVar(value="Untitled.rpr")
        ttk.Label(bar, textvariable=self.file_label, foreground="#64748b").pack(side="right", padx=8)

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
        self.editor.bind("<<Modified>>", self._on_modified)
        self.editor.bind("<KeyRelease>", self._on_editor_key)
        self.editor.bind("<MouseWheel>", self._redraw_line_numbers)
        self.editor.bind("<ButtonRelease-1>", self._update_cursor_status)
        self.editor.bind("<Configure>", self._redraw_line_numbers)

        header = ttk.Frame(output_frame)
        header.pack(fill="x")
        ttk.Label(header, text="ВЫВОД / ОТЛАДКА", style="PaneTitle.TLabel", padding=(5, 6)).pack(side="left")
        ttk.Button(header, text="Очистить", command=self.clear_output).pack(side="right", padx=4)
        tabs = ttk.Notebook(output_frame)
        tabs.pack(fill="both", expand=True)
        output_page = ttk.Frame(tabs)
        variables_page = ttk.Frame(tabs)
        stack_page = ttk.Frame(tabs)
        tabs.add(output_page, text="Вывод")
        tabs.add(variables_page, text="Переменные")
        tabs.add(stack_page, text="Стек вызовов")
        self.output_tabs = tabs
        self.output = ScrolledText(output_page, height=9, wrap="word", font=("Cascadia Code", 9), state="disabled")
        self.output.pack(fill="both", expand=True)
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
            "<F9>": self.toggle_breakpoint,
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

    def toggle_ui_theme(self) -> None:
        self._theme_name = toggle_theme(self, "reaper-studio")
        self._theme_mode.set(self._theme_name)

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

    def check_source(self) -> None:
        if self.current_file and self.current_file.suffix.lower() in {".js", ".mjs", ".cjs"}:
            self.check_node_source()
            return
        try:
            parse(self._source(), self._source_name())
        except ReaperError as error:
            self._append_output(f"CHECK FAILED: {error}")
            self.status.set("Проверка исходного кода не пройдена")
            return
        self._append_output(f"CHECK OK: {self._source_name()} — синтаксис корректен")
        self.status.set("Проверка пройдена")

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
            self.status.set(f"Точка останова удалена: {line}")
        else:
            self.breakpoints.add(line)
            self.status.set(f"Точка останова добавлена: {line}")
        self._append_output("Точки останова: " + (", ".join(map(str, sorted(self.breakpoints))) or "нет"))

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
                    self._run_queue.put(("line", line.rstrip("\\r\\n")))
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
        self.line_numbers.delete("all")
        try:
            index = self.editor.index("@0,0")
            while True:
                info = self.editor.dlineinfo(index)
                if info is None:
                    break
                self.line_numbers.create_text(40, info[1], anchor="ne", text=index.split(".")[0], fill="#94a3b8", font=("Cascadia Code", 9))
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
        self.destroy()


def main() -> int:
    ReaperStudio().mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
