"""Native desktop workbench for the Reaper language."""
from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

from reaper.errors import ReaperError
from reaper.parser import parse
from reaper.runtime import Interpreter

STARTER = '''craft double(value) {
    yield value * 2
}

make values := [1, 2, 3, 4]
emit values ~> map(double)
'''

class ReaperStudio(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Reaper Studio")
        self.geometry("1120x760")
        self.minsize(780, 560)
        self.option_add("*Font", ("Segoe UI", 10))
        self.current_file: Path | None = None

        self._build_menu()
        toolbar = ttk.Frame(self, padding=(10, 8))
        toolbar.pack(fill="x")
        ttk.Button(toolbar, text="Open", command=self.open_file).pack(side="left")
        ttk.Button(toolbar, text="Save", command=self.save_file).pack(side="left", padx=4)
        ttk.Separator(toolbar, orient="vertical").pack(side="left", fill="y", padx=8)
        ttk.Button(toolbar, text="Check", command=self.check_source).pack(side="left")
        ttk.Button(toolbar, text="Run", command=self.run_source).pack(side="left", padx=4)
        ttk.Button(toolbar, text="Clear output", command=self.clear_output).pack(side="left", padx=4)
        self.file_label = tk.StringVar(value="Untitled.reaper")
        ttk.Label(toolbar, textvariable=self.file_label, foreground="#526174").pack(side="right")

        panes = ttk.Panedwindow(self, orient="vertical")
        panes.pack(fill="both", expand=True, padx=10, pady=(0, 8))
        editor_frame = ttk.Frame(panes)
        output_frame = ttk.Frame(panes)
        panes.add(editor_frame, weight=3)
        panes.add(output_frame, weight=1)
        ttk.Label(editor_frame, text="SOURCE", padding=(4, 4)).pack(anchor="w")
        self.editor = ScrolledText(editor_frame, wrap="none", undo=True, font=("Consolas", 11), tabs=("4c",))
        self.editor.pack(fill="both", expand=True)
        self.editor.insert("1.0", STARTER)
        ttk.Label(output_frame, text="OUTPUT", padding=(4, 4)).pack(anchor="w")
        self.output = ScrolledText(output_frame, height=9, wrap="word", font=("Consolas", 10), state="disabled")
        self.output.pack(fill="both", expand=True)

        self.status = tk.StringVar(value="Ready — check the source before running it")
        ttk.Label(self, textvariable=self.status, relief="sunken", anchor="w", padding=(8, 4)).pack(fill="x")
        self.bind_all("<Control-o>", lambda _event: self.open_file())
        self.bind_all("<Control-s>", lambda _event: self.save_file())
        self.bind_all("<F5>", lambda _event: self.run_source())
        self.bind_all("<Shift-F5>", lambda _event: self.check_source())

    def _build_menu(self) -> None:
        menu = tk.Menu(self)
        file_menu = tk.Menu(menu, tearoff=False)
        file_menu.add_command(label="New", command=self.new_file, accelerator="Ctrl+N")
        file_menu.add_command(label="Open…", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Save", command=self.save_file, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.destroy)
        menu.add_cascade(label="File", menu=file_menu)
        run_menu = tk.Menu(menu, tearoff=False)
        run_menu.add_command(label="Check source", command=self.check_source, accelerator="Shift+F5")
        run_menu.add_command(label="Run program", command=self.run_source, accelerator="F5")
        run_menu.add_command(label="Clear output", command=self.clear_output)
        menu.add_cascade(label="Run", menu=run_menu)
        self.configure(menu=menu)

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
        self.status.set("New source file")

    def open_file(self) -> None:
        filename = filedialog.askopenfilename(
            parent=self, filetypes=[("Reaper source", "*.rpr"), ("All files", "*.*")]
        )
        if not filename:
            return
        try:
            content = Path(filename).read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            messagebox.showerror("Open failed", str(error), parent=self)
            return
        self.current_file = Path(filename)
        self.file_label.set(self.current_file.name)
        self.editor.delete("1.0", "end")
        self.editor.insert("1.0", content)
        self.status.set(f"Opened {self.current_file}")

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
            messagebox.showerror("Save failed", str(error), parent=self)
            return
        self.status.set(f"Saved {self.current_file}")

    def check_source(self) -> None:
        source = self.editor.get("1.0", "end-1c")
        try:
            parse(source, self._source_name())
        except ReaperError as error:
            self._append_output(f"CHECK FAILED: {error}")
            self.status.set("Source check failed")
            return
        self._append_output(f"CHECK OK: {self._source_name()} parsed successfully")
        self.status.set("Source check passed")

    def run_source(self) -> None:
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
