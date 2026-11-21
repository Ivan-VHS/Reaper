"""Native CODEX-66 feature browser for Reaper Studio."""
from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, ttk
from pathlib import Path
from typing import Callable, Mapping

from .codex66 import (
    CATEGORIES, CATEGORY_LABELS, FEATURES, STATUS_LABELS,
    export_json, search_features, status_counts,
)


class Codex66Window(tk.Toplevel):
    """Searchable, evidence-based browser for the 66 IDE capability records."""

    def __init__(self, master: tk.Misc, commands: Mapping[str, Callable[[], object]]) -> None:
        super().__init__(master)
        self.master = master
        self.commands = dict(commands)
        self._visible = ()
        self._selected_id: str | None = None
        self.title("CODEX-66 // Reaper Studio IDE")
        self.geometry("1180x760")
        self.minsize(900, 590)
        self.transient(master)
        self._build()
        self._refresh()

        self.bind("<Escape>", lambda _event: self.destroy())
        self.bind("<Control-f>", lambda _event: (self.search_entry.focus_set(), "break")[1])
        self.protocol("WM_DELETE_WINDOW", self.destroy)

    def _build(self) -> None:
        root = ttk.Frame(self, padding=14)
        root.pack(fill="both", expand=True)

        heading = ttk.Frame(root)
        heading.pack(fill="x")
        title = ttk.Label(heading, text="CODEX-66 // IDE SHOWCASE", style="Title.TLabel")
        title.pack(anchor="w")
        ttk.Label(
            heading,
            text="Каталог возможностей Reaper Studio · реализация, ограничения и ближайшие действия",
            style="Muted.TLabel",
        ).pack(anchor="w", pady=(2, 10))

        metrics = ttk.Frame(root)
        metrics.pack(fill="x", pady=(0, 10))
        self.metrics_var = tk.StringVar()
        ttk.Label(metrics, textvariable=self.metrics_var, style="PaneTitle.TLabel").pack(side="left")
        ttk.Label(
            metrics,
            text="Статус отражает код и тесты. Каталог не включает функции и не заявляет AI/Git/Sandbox там, где их нет.",
            style="Muted.TLabel",
        ).pack(side="right")

        filters = ttk.Frame(root)
        filters.pack(fill="x", pady=(0, 10))
        ttk.Label(filters, text="Поиск").pack(side="left", padx=(0, 6))
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(filters, textvariable=self.search_var)
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.search_entry.configure(width=30)
        self.search_var.trace_add("write", lambda *_: self._refresh())

        ttk.Label(filters, text="Категория").pack(side="left", padx=(0, 5))
        self.category_values = {"Все (66)": "all"}
        self.category_values.update({label: key for key, label in CATEGORIES})
        self.category_var = tk.StringVar(value="Все (66)")
        category_box = ttk.Combobox(
            filters, textvariable=self.category_var, state="readonly",
            values=list(self.category_values), width=25,
        )
        category_box.pack(side="left", padx=(0, 10))
        category_box.bind("<<ComboboxSelected>>", lambda _event: self._refresh())

        ttk.Label(filters, text="Статус").pack(side="left", padx=(0, 5))
        self.status_values = {"Все статусы": "all"}
        self.status_values.update({label: key for key, label in STATUS_LABELS.items()})
        self.status_var = tk.StringVar(value="Все статусы")
        status_box = ttk.Combobox(
            filters, textvariable=self.status_var, state="readonly",
            values=list(self.status_values), width=18,
        )
        status_box.pack(side="left", padx=(0, 8))
        status_box.bind("<<ComboboxSelected>>", lambda _event: self._refresh())

        panes = ttk.Panedwindow(root, orient="horizontal")
        panes.pack(fill="both", expand=True)

        list_frame = ttk.Frame(panes)
        detail_frame = ttk.Frame(panes, padding=(14, 4, 4, 4))
        panes.add(list_frame, weight=3)
        panes.add(detail_frame, weight=2)

        columns = ("id", "title", "status")
        self.table = ttk.Treeview(list_frame, columns=columns, show="headings", selectmode="browse")
        self.table.heading("id", text="ID")
        self.table.heading("title", text="Возможность")
        self.table.heading("status", text="Статус")
        self.table.column("id", width=48, minwidth=44, stretch=False, anchor="center")
        self.table.column("title", width=300, minwidth=180, stretch=True)
        self.table.column("status", width=112, minwidth=96, stretch=False)
        scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=scroll.set)
        self.table.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.table.tag_configure("implemented", foreground="#16803c")
        self.table.tag_configure("partial", foreground="#9a6700")
        self.table.tag_configure("planned", foreground="#64748b")
        self.table.tag_configure("not_supported", foreground="#b42318")
        self.table.bind("<<TreeviewSelect>>", self._select)
        self.table.bind("<Double-Button-1>", self._run_selected)

        self.detail_id = tk.StringVar(value="Выберите возможность")
        self.detail_status = tk.StringVar(value="")
        self.detail_category = tk.StringVar(value="")
        ttk.Label(detail_frame, textvariable=self.detail_id, style="Title.TLabel", wraplength=430).pack(anchor="w")
        ttk.Label(detail_frame, textvariable=self.detail_status, style="PaneTitle.TLabel").pack(anchor="w", pady=(7, 2))
        ttk.Label(detail_frame, textvariable=self.detail_category, style="Muted.TLabel").pack(anchor="w", pady=(0, 12))

        ttk.Label(detail_frame, text="Описание", style="PaneTitle.TLabel").pack(anchor="w")
        self.summary = tk.Text(detail_frame, height=5, wrap="word", relief="flat", padx=9, pady=8)
        self.summary.pack(fill="x", pady=(4, 12))
        self.summary.configure(state="disabled")

        ttk.Label(detail_frame, text="Фактическая граница / доказательство", style="PaneTitle.TLabel").pack(anchor="w")
        self.evidence = tk.Text(detail_frame, height=7, wrap="word", relief="flat", padx=9, pady=8)
        self.evidence.pack(fill="x", pady=(4, 12))
        self.evidence.configure(state="disabled")

        ttk.Label(
            detail_frame,
            text="Неподдерживаемые возможности показаны как план или ограничение, а не как активная кнопка.",
            style="Muted.TLabel", wraplength=420,
        ).pack(anchor="w", pady=(0, 12))
        action_row = ttk.Frame(detail_frame)
        action_row.pack(fill="x", side="bottom")
        self.action_button = ttk.Button(action_row, text="Открыть в Studio", style="Primary.TButton",
                                         command=self._run_selected, state="disabled")
        self.action_button.pack(side="left")
        ttk.Button(action_row, text="Экспорт JSON", command=self._export).pack(side="right")

        footer = ttk.Frame(root)
        footer.pack(fill="x", pady=(10, 0))
        self.visible_var = tk.StringVar()
        ttk.Label(footer, textvariable=self.visible_var, style="Muted.TLabel").pack(side="left")
        ttk.Button(footer, text="Сбросить фильтры", command=self._reset_filters).pack(side="right")

    def _refresh(self) -> None:
        category = self.category_values.get(self.category_var.get(), "all")
        status = self.status_values.get(self.status_var.get(), "all")
        self._visible = search_features(self.search_var.get(), category, status)
        self.table.delete(*self.table.get_children())
        for item in self._visible:
            self.table.insert(
                "", "end", iid=item.id,
                values=(item.id, item.title, STATUS_LABELS[item.status]),
                tags=(item.status,),
            )
        counts = status_counts()
        self.metrics_var.set(
            f"66 возможностей  ·  {counts['implemented']} реализовано  ·  "
            f"{counts['partial']} частично  ·  {counts['planned']} в плане  ·  "
            f"{counts['not_supported']} не поддерживается"
        )
        self.visible_var.set(f"Показано: {len(self._visible)} из 66")
        selected = self._selected_id if any(x.id == self._selected_id for x in self._visible) else None
        if selected is None and self._visible:
            selected = self._visible[0].id
        if selected:
            self.table.selection_set(selected)
            self.table.focus(selected)
            self.table.see(selected)
            self._selected_id = selected
            self._show_detail(selected)
        else:
            self._selected_id = None
            self.detail_id.set("Нет совпадений")
            self.detail_status.set("")
            self.detail_category.set("")
            self._set_text(self.summary, "Измените поисковый запрос или фильтры.")
            self._set_text(self.evidence, "")
            self.action_button.configure(state="disabled")

    def _select(self, _event: object = None) -> None:
        selection = self.table.selection()
        if selection:
            self._selected_id = selection[0]
            self._show_detail(self._selected_id)

    def _show_detail(self, feature_id: str) -> None:
        item = next((x for x in self._visible if x.id == feature_id), None)
        if item is None:
            return
        self.detail_id.set(f"#{item.id}  {item.title}")
        self.detail_status.set(STATUS_LABELS[item.status])
        self.detail_category.set(CATEGORY_LABELS[item.category])
        self._set_text(self.summary, item.summary)
        self._set_text(self.evidence, item.evidence)
        available = bool(item.action and self.commands.get(item.action))
        label = "Открыть в Studio" if available else "Нет действия в текущей сборке"
        self.action_button.configure(text=label, state="normal" if available else "disabled")

    @staticmethod
    def _set_text(widget: tk.Text, value: str) -> None:
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", value)
        widget.configure(state="disabled")

    def _run_selected(self, _event: object = None) -> str:
        selection = self.table.selection()
        if not selection:
            return "break"
        item = next((x for x in self._visible if x.id == selection[0]), None)
        if item is None or not item.action:
            return "break"
        callback = self.commands.get(item.action)
        if callback is None:
            return "break"
        self.lift()
        callback()
        return "break"

    def _export(self) -> None:
        filename = filedialog.asksaveasfilename(
            parent=self, title="Экспорт CODEX-66",
            defaultextension=".json",
            initialfile="reaper-codex-66.json",
            filetypes=[("JSON", "*.json"), ("Все файлы", "*.*")],
        )
        if not filename:
            return
        try:
            Path(filename).write_text(export_json(), encoding="utf-8", newline="\n")
        except OSError as error:
            from tkinter import messagebox
            messagebox.showerror("Экспорт CODEX-66", str(error), parent=self)
            return
        from tkinter import messagebox
        messagebox.showinfo("Экспорт CODEX-66", f"Каталог экспортирован:\n{filename}", parent=self)

    def _reset_filters(self) -> None:
        self.search_var.set("")
        self.category_var.set("Все (66)")
        self.status_var.set("Все статусы")
        self._refresh()
