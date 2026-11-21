"""Native desktop workbench for the Reaper language."""
from __future__ import annotations

from pathlib import Path
import tkinter as tk
import threading
from tkinter import filedialog, messagebox, ttk

from reaper.embedded import (
    EmbeddedError,
    build_project as embedded_build_project,
    init_project as embedded_init_project,
    inspect_project as embedded_inspect_project,
)
from tkinter.scrolledtext import ScrolledText

from reaper.errors import ReaperError
from reaper.parser import parse
from reaper.runtime import Interpreter
from reaper.debugger import DebuggerStopped, RuntimeDebugger
from reaper.products import list_products
from reaper.ui_motion import MotionController
from reaper.ui_theme import apply_theme, apply_ui_theme, set_dpi_awareness, toggle_theme

STARTER = '''craft double(value) {
    yield value * 2
}

make values := [1, 2, 3, 4]
emit values :: map(double)
'''

class ReaperStudio(tk.Tk):
    def __init__(self) -> None:
        set_dpi_awareness()
        super().__init__()
        self.title("Reaper Studio — редактор программ")
        self.geometry("1120x760")
        self.minsize(780, 560)
        self._theme_name = apply_theme(self, "reaper-studio")
        self._theme_mode = tk.StringVar(value=self._theme_name)
        self.current_file: Path | None = None
        self.breakpoints: set[int] = set()
        self.debugger: RuntimeDebugger | None = None
        self._debug_wait = False
        self._debug_signal = tk.BooleanVar(value=False)

        self._build_menu()
        toolbar = ttk.Frame(self, padding=(10, 8))
        toolbar.pack(fill="x")
        file_actions = ttk.Frame(toolbar)
        file_actions.pack(fill="x")
        run_actions = ttk.Frame(toolbar)
        run_actions.pack(fill="x", pady=(6, 0))
        ttk.Button(file_actions, text="Открыть", command=self.open_file).pack(side="left")
        ttk.Button(file_actions, text="Сохранить", command=self.save_file).pack(side="left", padx=4)
        self.file_label = tk.StringVar(value="Untitled.reaper")
        ttk.Label(file_actions, textvariable=self.file_label, style="Muted.TLabel").pack(side="right")
        self.theme_button = ttk.Button(file_actions, text="Тёмная тема", command=self.toggle_ui_theme)
        self.theme_button.pack(side="right", padx=(8, 10))
        ttk.Separator(run_actions, orient="vertical").pack(side="left", fill="y", padx=8)
        ttk.Button(run_actions, text="Проверить", command=self.check_source).pack(side="left")
        ttk.Button(run_actions, text="Выполнить", command=self.run_source, style="Primary.TButton").pack(side="left", padx=4)
        ttk.Button(run_actions, text="Отладка", command=self.debug_source).pack(side="left")
        ttk.Button(run_actions, text="Точка останова", command=self.toggle_breakpoint).pack(side="left", padx=4)
        ttk.Button(run_actions, text="Продолжить", command=self.continue_debug).pack(side="left")
        ttk.Button(run_actions, text="Шаг", command=self.step_debug).pack(side="left", padx=4)
        ttk.Button(run_actions, text="Остановить", command=self.stop_debug, style="Danger.TButton").pack(side="left")
        ttk.Button(run_actions, text="Очистить вывод", command=self.clear_output).pack(side="left", padx=4)

        panes = ttk.Panedwindow(self, orient="vertical")
        panes.pack(fill="both", expand=True, padx=10, pady=(0, 8))
        editor_frame = ttk.Frame(panes)
        output_frame = ttk.Frame(panes)
        panes.add(editor_frame, weight=3)
        panes.add(output_frame, weight=1)
        ttk.Label(editor_frame, text="ИСХОДНЫЙ КОД", padding=(4, 4), style="Section.TLabel").pack(anchor="w")
        self.editor = ScrolledText(editor_frame, wrap="none", undo=True, font=("Consolas", 11), tabs=("4c",))
        self.editor.pack(fill="both", expand=True)
        self.editor.insert("1.0", STARTER)
        debug_tabs = ttk.Notebook(output_frame)
        debug_tabs.pack(fill="both", expand=True)
        output_page = ttk.Frame(debug_tabs)
        variables_page = ttk.Frame(debug_tabs)
        stack_page = ttk.Frame(debug_tabs)
        debug_tabs.add(output_page, text="Вывод")
        debug_tabs.add(variables_page, text="Переменные")
        debug_tabs.add(stack_page, text="Стек вызовов")
        self.output_tabs = debug_tabs
        self.output = ScrolledText(output_page, height=9, wrap="word", font=("Consolas", 10), state="disabled")
        self.output.pack(fill="both", expand=True)
        self.variables_view = ttk.Treeview(variables_page, columns=("value",), show="tree headings")
        self.variables_view.heading("#0", text="Имя")
        self.variables_view.heading("value", text="Значение")
        self.variables_view.column("#0", width=220, stretch=True)
        self.variables_view.column("value", width=520, stretch=True)
        self.variables_view.pack(fill="both", expand=True)
        self.stack_view = tk.Listbox(stack_page, font=("Consolas", 10))
        self.stack_view.pack(fill="both", expand=True)

        self.status = tk.StringVar(value="Готово — перед запуском проверьте исходный код")
        ttk.Label(self, textvariable=self.status, relief="sunken", anchor="w", padding=(8, 4)).pack(fill="x")
        self._motion = MotionController(self)
        self._motion.fade_in()
        self.bind_all("<Control-o>", lambda _event: self.open_file())
        self.bind_all("<Control-s>", lambda _event: self.save_file())
        self.bind_all("<F5>", lambda _event: self.run_source())
        self.bind_all("<Shift-F5>", lambda _event: self.check_source())
        self.bind_all("<F9>", lambda _event: self.toggle_breakpoint())

    def toggle_ui_theme(self) -> None:
        self._theme_name = toggle_theme(self, "reaper-studio")
        self._theme_mode.set(self._theme_name)
        self.theme_button.configure(text="Светлая тема" if self._theme_name == "dark" else "Тёмная тема")

    def _build_menu(self) -> None:
        menu = tk.Menu(self)
        file_menu = tk.Menu(menu, tearoff=False)
        file_menu.add_command(label="Создать", command=self.new_file, accelerator="Ctrl+N")
        file_menu.add_command(label="Открыть…", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Сохранить", command=self.save_file, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.destroy)
        menu.add_cascade(label="Файл", menu=file_menu)
        run_menu = tk.Menu(menu, tearoff=False)
        run_menu.add_command(label="Проверить исходный код", command=self.check_source, accelerator="Shift+F5")
        run_menu.add_command(label="Запустить программу", command=self.run_source, accelerator="F5")
        run_menu.add_command(label="Очистить вывод", command=self.clear_output)
        menu.add_cascade(label="Выполнение", menu=run_menu)
        embedded_menu = tk.Menu(menu, tearoff=False)
        embedded_menu.add_command(label="Создать проект встроенной C…", command=self.embedded_new_project)
        embedded_menu.add_command(label="Проверить профиль микроконтроллера…", command=self.embedded_inspect_project)
        embedded_menu.add_command(label="Собрать прошивку…", command=self.embedded_build)
        menu.add_cascade(label="Встроенная C", menu=embedded_menu)
        product_menu = tk.Menu(menu, tearoff=False)
        product_menu.add_command(label="Обзор внутренних продуктов…", command=self.show_internal_products)
        menu.add_cascade(label="Внутренние продукты", menu=product_menu)
        view_menu = tk.Menu(menu, tearoff=False)
        for mode, label in (("system", "Системная"), ("light", "Светлая"), ("dark", "Тёмная")):
            view_menu.add_radiobutton(
                label=label, variable=self._theme_mode, value=mode,
                command=self.apply_visual_theme,
            )
        menu.add_cascade(label="Вид", menu=view_menu)
        self.configure(menu=menu)

    def show_internal_products(self) -> None:
        """Show the integrated product registry inside Reaper Studio."""
        window = tk.Toplevel(self)
        window.title("REAPER — внутренние продукты")
        window.geometry("820x560")
        window.minsize(640, 420)
        window.transient(self)
        frame = ttk.Frame(window, padding=12)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Внутренние продукты REAPER", style="Section.TLabel").pack(anchor="w")
        ttk.Label(frame, text="Единая среда · общие API · отдельные зоны ответственности", style="Muted.TLabel").pack(anchor="w", pady=(2, 10))
        table = ttk.Treeview(frame, columns=("domain", "purpose", "service"), show="tree headings")
        table.heading("#0", text="Продукт")
        table.heading("domain", text="Направление")
        table.heading("purpose", text="Назначение")
        table.heading("service", text="Основная операция")
        table.column("#0", width=130, stretch=False)
        table.column("domain", width=150, stretch=False)
        table.column("purpose", width=330, stretch=True)
        table.column("service", width=170, stretch=False)
        for item in list_products():
            table.insert("", "end", text=item["name"], values=(item["domain"], item["purpose"], item["primary_service"]))
        table.pack(fill="both", expand=True)
        ttk.Label(frame, text="Сервисы работают в Python reference runtime; нативная C17-паритетность не заявляется.", style="Muted.TLabel").pack(anchor="w", pady=(8, 0))

    def apply_visual_theme(self) -> None:
        """Apply System, Light or Dark colors without changing editor behavior."""
        mode = self._theme_mode.get()
        if mode == "system":
            colors = apply_ui_theme(self, "system")
            self._theme_name = colors["mode"]
        else:
            self._theme_name = apply_theme(self, "reaper-studio", mode)
        self.theme_button.configure(text="Светлая тема" if self._theme_name == "dark" else "Тёмная тема")

    def embedded_new_project(self) -> None:
        directory = filedialog.askdirectory(parent=self, title="Создать проект встроенной C")
        if not directory:
            return
        try:
            root = embedded_init_project(directory)
        except (EmbeddedError, OSError, ValueError) as error:
            messagebox.showerror("Проект встроенной C", str(error), parent=self)
            return
        self._append_output(f"EMBEDDED: created {root}")
        self._append_output("Review embedded.json and linker.ld against the exact MCU datasheet.")

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
            f"MCU: {profile['id']} | {profile['architecture']} | "
            f"{profile['clock_hz']} Hz | toolchain {'found' if report['toolchain'] else 'missing'}"
        )
        self._append_output(
            f"FLASH: {profile['flash']['size']} bytes | SRAM: {profile['sram']['size']} bytes | "
            f"stack reserve: {profile['stack_bytes']} bytes"
        )

    def embedded_build(self) -> None:
        directory = filedialog.askdirectory(parent=self, title="Выбрать проект встроенной C для сборки")
        if not directory:
            return
        self._append_output(f"EMBEDDED: building {directory} …")
        def worker() -> None:
            try:
                result = embedded_build_project(directory)
            except Exception as error:
                self.after(0, self._finish_embedded_build, None, str(error))
                return
            self.after(0, self._finish_embedded_build, result, None)
        threading.Thread(target=worker, name="reaper-embedded-build", daemon=True).start()

    def _finish_embedded_build(self, result: dict[str, object] | None, error: str | None) -> None:
        if error:
            self._append_output(f"EMBEDDED BUILD FAILED: {error}")
            self.status.set("Сборка встроенного проекта завершилась с ошибкой")
            return
        assert result is not None
        self._append_output(f"EMBEDDED BUILD: {'OVER BUDGET' if result['over_budget'] else 'success'}")
        for kind, path in result["artifacts"].items():
            self._append_output(f"{kind}: {path}")
        budget = result["budget"]
        self._append_output(
            f"FLASH: {budget['flash_used']}/{budget['flash_total']} bytes "
            f"({budget['flash_percent']}%) | SRAM incl. stack: "
            f"{budget['sram_used_with_stack']}/{budget['sram_total']} bytes "
            f"({budget['sram_percent']}%)"
        )
        self.status.set("Сборка встроенного проекта завершена" if not result["over_budget"] else "Образ превышает заданный объём памяти")

    def _source_name(self) -> str:
        return str(self.current_file) if self.current_file else "<editor>"

    def _append_output(self, line: str) -> None:
        self.output.configure(state="normal")
        self.output.insert("end", str(line) + "\n")
        self.output.see("end")
        self.output.configure(state="disabled")

    def clear_output(self) -> None:
        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        self.output.configure(state="disabled")

    def new_file(self) -> None:
        self.current_file = None
        self.file_label.set("Untitled.reaper")
        self.editor.delete("1.0", "end")
        self.status.set("Создан новый файл исходного кода")

    def open_file(self) -> None:
        filename = filedialog.askopenfilename(
            parent=self, filetypes=[("Файлы Reaper", "*.rpr"), ("Все файлы", "*.*")]
        )
        if not filename:
            return
        try:
            content = Path(filename).read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            messagebox.showerror("Не удалось открыть файл", str(error), parent=self)
            return
        self.current_file = Path(filename)
        self.file_label.set(self.current_file.name)
        self.editor.delete("1.0", "end")
        self.editor.insert("1.0", content)
        self.status.set(f"Открыт файл: {self.current_file}")

    def save_file(self) -> None:
        if self.current_file is None:
            filename = filedialog.asksaveasfilename(
                parent=self, defaultextension=".rpr",
                filetypes=[("Reaper source", "*.rpr"), ("All files", "*.*")]
            )
            if not filename:
                return
            self.current_file = Path(filename)
            self.file_label.set(self.current_file.name)
        try:
            self.current_file.write_text(self.editor.get("1.0", "end-1c"), encoding="utf-8")
        except OSError as error:
            messagebox.showerror("Не удалось сохранить файл", str(error), parent=self)
            return
        self.status.set(f"Сохранён файл: {self.current_file}")

    def check_source(self) -> None:
        source = self.editor.get("1.0", "end-1c")
        try:
            parse(source, self._source_name())
        except ReaperError as error:
            self._append_output(f"CHECK FAILED: {error}")
            self.status.set("Проверка исходного кода завершилась с ошибкой")
            return
        self._append_output(f"Проверка пройдена: {self._source_name()} — синтаксис корректен")
        self.status.set("Проверка исходного кода пройдена")

    def toggle_breakpoint(self) -> None:
        line = int(self.editor.index("insert").split(".")[0])
        if line in self.breakpoints:
            self.breakpoints.remove(line)
            self.status.set(f"Точка останова удалена: строка {line}")
        else:
            self.breakpoints.add(line)
            self.status.set(f"Точка останова добавлена: строка {line}")
        self._append_output("Точки останова: " + (", ".join(map(str, sorted(self.breakpoints))) or "нет"))

    def _pause_for_debug(self, snapshot: Any) -> None:
        self.variables_view.delete(*self.variables_view.get_children())
        for name, value in snapshot.variables.items():
            self.variables_view.insert("", "end", text=name, values=(self._debug_value(value),))
        self.stack_view.delete(0, "end")
        for index, name in enumerate(snapshot.call_stack):
            self.stack_view.insert("end", f"{index}: {name}")
        if not snapshot.call_stack:
            self.stack_view.insert("end", "<module>")
        self.output_tabs.select(1)
        self.status.set(f"Paused at {snapshot.filename}:{snapshot.line}:{snapshot.column}")
        self._debug_wait = True
        self._debug_signal.set(False)
        while self._debug_wait:
            self.wait_variable(self._debug_signal)

    @staticmethod
    def _debug_value(value: Any) -> str:
        rendered = repr(value)
        return rendered if len(rendered) <= 240 else rendered[:237] + "..."

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
        source = self.editor.get("1.0", "end-1c")
        self.clear_output()
        debugger = RuntimeDebugger(self.breakpoints, self._pause_for_debug)
        if first_step:
            debugger.step()
        self.debugger = debugger
        try:
            Interpreter(output=self._append_output, debugger=debugger).run(source, self._source_name())
        except DebuggerStopped:
            self.status.set("Debug session stopped")
        except ReaperError as error:
            self._append_output(f"RUNTIME ERROR: {error}")
            self.status.set("Execution failed")
            return
        finally:
            self.debugger = None
            self._debug_wait = False
        if not debugger.stop_requested:
            self.status.set("Execution completed")

    def debug_source(self) -> None:
        self._run_with_debugger(first_step=True)

    def run_source(self) -> None:
        if self.breakpoints:
            self._run_with_debugger()
            return
        source = self.editor.get("1.0", "end-1c")
        self.clear_output()
        try:
            Interpreter(output=self._append_output).run(source, self._source_name())
        except ReaperError as error:
            self._append_output(f"RUNTIME ERROR: {error}")
            self.status.set("Execution failed")
            return
        self.status.set("Execution completed")


def main() -> int:
    ReaperStudio().mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
