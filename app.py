from __future__ import annotations

import os
import json
import re
import threading
import urllib.error
import urllib.request
import uuid
from datetime import date
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

from minmol.core import (
    MONTHS,
    DataStore,
    calculate_target,
    classify_event,
    event_in_reporting_month,
    event_is_complete,
    parse_event_date,
    reporting_period,
    reporting_period_bounds,
    safe_int,
)
from minmol.reports import (
    export_all,
    export_appendix_1,
    export_appendix_2,
    export_monthly_summary,
    export_press_release,
    preview_appendix_1,
    preview_appendix_2,
)
from minmol.security import delete_secret, load_secret, save_secret


BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "данные" / "данные.json"
REPORTS_PATH = BASE_DIR / "отчеты"
API_KEY_PATH = BASE_DIR / "данные" / "api_key.bin"


class MinMolApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.store = DataStore(DATA_PATH)
        self.selected_event_id = None
        self.report_month_initialized = False
        self.title("МИН МОЛ | Учет мероприятий и отчетность | версия 22.09.2026")
        self.geometry("1420x850")
        self.minsize(1080, 700)
        self.configure(bg="#edf2f5")
        self._configure_styles()
        self._build_header()
        self.notebook = ttk.Notebook(self, style="App.TNotebook")
        self.notebook.pack(fill="both", expand=True, padx=18, pady=(0, 12))
        self._build_dashboard()
        self._build_targets()
        self._build_events()
        self._build_reports()
        self._build_form_settings()
        self._build_press_releases()
        self._build_status()
        self._install_clipboard_support()
        self.refresh_all()
        self.protocol("WM_DELETE_WINDOW", self._close)

    def _configure_styles(self):
        style = ttk.Style(self)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure(".", font=("Segoe UI", 10), background="#edf2f5", foreground="#17324d")
        style.configure("TFrame", background="#edf2f5")
        style.configure("Card.TFrame", background="#ffffff", relief="flat")
        style.configure("TLabel", background="#edf2f5")
        style.configure("Card.TLabel", background="#ffffff")
        style.configure("Title.TLabel", background="#17324d", foreground="#ffffff", font=("Segoe UI Semibold", 18))
        style.configure("Subtitle.TLabel", background="#17324d", foreground="#c8d8e6", font=("Segoe UI", 9))
        style.configure("Section.TLabel", font=("Segoe UI Semibold", 13), foreground="#17324d")
        style.configure("Metric.TLabel", background="#ffffff", font=("Segoe UI Semibold", 23), foreground="#17324d")
        style.configure("MetricCaption.TLabel", background="#ffffff", foreground="#597084")
        style.configure("Accent.TButton", background="#d4a72c", foreground="#13283a", font=("Segoe UI Semibold", 10), padding=(14, 8))
        style.map("Accent.TButton", background=[("active", "#e1b83e")])
        style.configure("Primary.TButton", background="#17324d", foreground="#ffffff", padding=(12, 7))
        style.map("Primary.TButton", background=[("active", "#244b6b")])
        style.configure("Danger.TButton", foreground="#9f2f2f", padding=(10, 7))
        style.configure("Treeview", rowheight=30, background="#ffffff", fieldbackground="#ffffff", borderwidth=0)
        style.configure("Treeview.Heading", background="#dce8f2", foreground="#17324d", font=("Segoe UI Semibold", 9), padding=6)
        style.map("Treeview", background=[("selected", "#c9ddec")], foreground=[("selected", "#13283a")])
        style.configure("App.TNotebook", background="#edf2f5", borderwidth=0)
        style.configure("App.TNotebook.Tab", padding=(18, 9), font=("Segoe UI Semibold", 10))

    def _install_clipboard_support(self):
        self.edit_menu = tk.Menu(self, tearoff=False)
        self.edit_menu.add_command(label="Вырезать", command=lambda: self._edit_action("<<Cut>>"))
        self.edit_menu.add_command(label="Копировать", command=lambda: self._edit_action("<<Copy>>"))
        self.edit_menu.add_command(label="Вставить", command=lambda: self._edit_action("<<Paste>>"))
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label="Выделить все", command=self._select_all)
        for widget_class in ("Entry", "TEntry", "Text", "TCombobox", "TSpinbox"):
            self.bind_class(widget_class, "<Button-3>", self._show_edit_menu, add="+")
        self.bind_class("Treeview", "<Control-c>", self.copy_tree_selection, add="+")
        self.bind_class("Treeview", "<Button-3>", self.show_tree_menu, add="+")

    def _show_edit_menu(self, event):
        event.widget.focus_set()
        try:
            self.edit_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.edit_menu.grab_release()

    def _edit_action(self, virtual_event):
        widget = self.focus_get()
        if widget:
            widget.event_generate(virtual_event)

    def _select_all(self):
        widget = self.focus_get()
        if isinstance(widget, tk.Text):
            widget.tag_add("sel", "1.0", "end-1c")
        elif widget:
            try:
                widget.selection_range(0, "end")
            except tk.TclError:
                pass

    def show_tree_menu(self, event):
        tree = event.widget
        row = tree.identify_row(event.y)
        if row:
            tree.selection_set(row)
            tree.focus(row)
        menu = tk.Menu(self, tearoff=False)
        menu.add_command(label="Копировать строку", command=lambda: self.copy_tree_selection(widget=tree))
        menu.tk_popup(event.x_root, event.y_root)

    def copy_tree_selection(self, _event=None, widget=None):
        tree = widget or self.focus_get()
        if not isinstance(tree, ttk.Treeview):
            return
        rows = []
        for item_id in tree.selection():
            rows.append("\t".join(str(value) for value in tree.item(item_id, "values")))
        if rows:
            self.clipboard_clear()
            self.clipboard_append("\n".join(rows))
            self.set_status("Выбранная строка скопирована")
        return "break"

    def _build_header(self):
        header = tk.Frame(self, bg="#17324d", height=92)
        header.pack(fill="x")
        header.pack_propagate(False)
        left = tk.Frame(header, bg="#17324d")
        left.pack(side="left", padx=22, pady=15)
        ttk.Label(left, text="МИН МОЛ", style="Title.TLabel").pack(anchor="w")
        ttk.Label(left, text="Целевые показатели, мероприятия и ежемесячная отчетность", style="Subtitle.TLabel").pack(anchor="w")
        self.header_year = tk.StringVar()
        year_box = tk.Frame(header, bg="#17324d")
        year_box.pack(side="right", padx=22)
        tk.Label(year_box, text="ОТЧЕТНЫЙ ГОД", bg="#17324d", fg="#c8d8e6", font=("Segoe UI", 8)).pack(anchor="e")
        tk.Label(year_box, textvariable=self.header_year, bg="#17324d", fg="#d4a72c", font=("Segoe UI Semibold", 22)).pack(anchor="e")

    def _build_dashboard(self):
        self.dashboard = ttk.Frame(self.notebook, padding=18)
        self.notebook.add(self.dashboard, text="Обзор")
        ttk.Label(self.dashboard, text="Состояние отчетности", style="Section.TLabel").pack(anchor="w", pady=(0, 12))
        cards = ttk.Frame(self.dashboard)
        cards.pack(fill="x")
        cards.columnconfigure((0, 1, 2, 3), weight=1, uniform="card")
        self.metric_events = tk.StringVar()
        self.metric_people = tk.StringVar()
        self.metric_filled = tk.StringVar()
        self.metric_ready = tk.StringVar()
        metrics = (
            ("Мероприятий за год", self.metric_events),
            ("Суммарный охват", self.metric_people),
            ("Заполнено месяцев", self.metric_filled),
            ("Показателей настроено", self.metric_ready),
        )
        for index, (caption, variable) in enumerate(metrics):
            card = ttk.Frame(cards, style="Card.TFrame", padding=18)
            card.grid(row=0, column=index, sticky="nsew", padx=(0 if index == 0 else 6, 0 if index == 3 else 6))
            ttk.Label(card, textvariable=variable, style="Metric.TLabel").pack(anchor="w")
            ttk.Label(card, text=caption, style="MetricCaption.TLabel").pack(anchor="w")

        settings = ttk.LabelFrame(self.dashboard, text=" Реквизиты отчетности ", padding=16)
        settings.pack(fill="x", pady=20)
        settings.columnconfigure(1, weight=1)
        ttk.Label(settings, text="Организация").grid(row=0, column=0, sticky="w", padx=(0, 10), pady=5)
        self.organization_var = tk.StringVar()
        ttk.Entry(settings, textvariable=self.organization_var).grid(row=0, column=1, sticky="ew", pady=5)
        ttk.Label(settings, text="Отчетный год").grid(row=1, column=0, sticky="w", padx=(0, 10), pady=5)
        self.year_var = tk.StringVar()
        ttk.Spinbox(settings, from_=2020, to=2100, textvariable=self.year_var, width=10).grid(row=1, column=1, sticky="w", pady=5)
        ttk.Button(settings, text="Сохранить реквизиты", style="Primary.TButton", command=self.save_settings).grid(row=2, column=1, sticky="w", pady=(10, 0))

        guide = ttk.LabelFrame(self.dashboard, text=" Как работать с программой ", padding=16)
        guide.pack(fill="both", expand=True)
        text = (
            "1. В разделе «Целевые показатели» внесите плановые значения нарастающим итогом для каждого месяца.\n\n"
            "2. Карточку мероприятия можно сохранить заранее только с датой и названием, а описание, участников и ссылку дополнить после проведения.\n\n"
            "3. Проверяйте рассчитанный факт, остаток и необходимый охват. Отрицательный остаток означает опережение плана.\n\n"
            "4. Отчетный месяц идет с 25-го числа предыдущего месяца по 24-е число выбранного. Перед выгрузкой приложения можно просмотреть."
        )
        ttk.Label(guide, text=text, wraplength=1100, justify="left").pack(anchor="nw")

    def _build_targets(self):
        self.targets_tab = ttk.Frame(self.notebook, padding=18)
        self.notebook.add(self.targets_tab, text="Целевые показатели")
        editor = ttk.LabelFrame(self.targets_tab, text=" План нарастающим итогом ", padding=12)
        editor.pack(fill="x", pady=(0, 12))
        self.plan_target_var = tk.StringVar()
        self.plan_name_var = tk.StringVar()
        self.plan_month_var = tk.StringVar(value=MONTHS[0])
        self.plan_value_var = tk.StringVar(value="0")
        ttk.Label(editor, text="Направление").grid(row=0, column=0, sticky="w")
        self.plan_target_combo = ttk.Combobox(editor, textvariable=self.plan_target_var, state="readonly", width=72)
        self.plan_target_combo.grid(row=1, column=0, sticky="ew", padx=(0, 10))
        ttk.Label(editor, text="Название показателя (можно изменить)").grid(row=2, column=0, sticky="w", pady=(8, 0))
        ttk.Entry(editor, textvariable=self.plan_name_var).grid(row=3, column=0, columnspan=4, sticky="ew", pady=(0, 5))
        ttk.Label(editor, text="Месяц").grid(row=0, column=1, sticky="w")
        month_combo = ttk.Combobox(editor, textvariable=self.plan_month_var, values=MONTHS, state="readonly", width=14)
        month_combo.grid(row=1, column=1, padx=(0, 10))
        ttk.Label(editor, text="План нарастающим").grid(row=0, column=2, sticky="w")
        ttk.Entry(editor, textvariable=self.plan_value_var, width=18).grid(row=1, column=2, padx=(0, 10))
        ttk.Button(editor, text="Записать план", style="Accent.TButton", command=self.save_plan).grid(row=1, column=3)
        editor.columnconfigure(0, weight=1)
        self.plan_target_combo.bind("<<ComboboxSelected>>", self.load_plan_value)
        month_combo.bind("<<ComboboxSelected>>", self.load_plan_value)

        table_frame = ttk.Frame(self.targets_tab)
        table_frame.pack(fill="both", expand=True)
        columns = ("target", "month", "cumulative", "monthly", "actual", "actual_cum", "balance", "required")
        self.targets_tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        headings = {
            "target": "Направление", "month": "Месяц", "cumulative": "План нарастающим",
            "monthly": "Разница планов", "actual": "Факт за месяц", "actual_cum": "Факт нарастающим",
            "balance": "Необходимо - сделано", "required": "Нужно с остатком",
        }
        widths = {"target": 350, "month": 100, "cumulative": 125, "monthly": 115, "actual": 110, "actual_cum": 125, "balance": 145, "required": 130}
        for column in columns:
            self.targets_tree.heading(column, text=headings[column])
            self.targets_tree.column(column, width=widths[column], anchor="w" if column == "target" else "center")
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.targets_tree.yview)
        self.targets_tree.configure(yscrollcommand=scrollbar.set)
        self.targets_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.targets_tree.bind("<<TreeviewSelect>>", self.select_plan_row)

    def _build_events(self):
        self.events_tab = ttk.Frame(self.notebook, padding=18)
        self.notebook.add(self.events_tab, text="Мероприятия")
        filters = ttk.Frame(self.events_tab)
        filters.pack(fill="x", pady=(0, 10))
        ttk.Label(filters, text="Отчетный месяц:").pack(side="left")
        self.event_filter_var = tk.StringVar(value="Все месяцы")
        filter_combo = ttk.Combobox(filters, textvariable=self.event_filter_var, values=("Все месяцы",) + MONTHS, state="readonly", width=18)
        filter_combo.pack(side="left", padx=8)
        filter_combo.bind("<<ComboboxSelected>>", lambda _event: self.refresh_events())
        ttk.Label(filters, text="Поиск по дате или названию:").pack(side="left", padx=(16, 4))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(filters, textvariable=self.search_var, width=28)
        search_entry.pack(side="left")
        search_entry.bind("<Return>", lambda _event: self.search_event())
        ttk.Button(filters, text="Найти", command=self.search_event).pack(side="left", padx=4)
        ttk.Button(filters, text="Сбросить", command=self.clear_search).pack(side="left")
        ttk.Button(filters, text="Новое мероприятие", style="Accent.TButton", command=self.new_event).pack(side="right")

        paned = ttk.Panedwindow(self.events_tab, orient="horizontal")
        paned.pack(fill="both", expand=True)
        list_panel = ttk.Frame(paned)
        form_panel = ttk.LabelFrame(paned, text=" Карточка мероприятия ", padding=12)
        paned.add(list_panel, weight=3)
        paned.add(form_panel, weight=2)
        columns = ("date", "period", "name", "targets", "participants", "status")
        self.events_tree = ttk.Treeview(list_panel, columns=columns, show="headings", selectmode="browse")
        for column, title, width in (
            ("date", "Дата", 90), ("period", "Отчет", 85), ("name", "Название", 280),
            ("targets", "ЦП", 100), ("participants", "Участники", 80), ("status", "Состояние", 90)
        ):
            self.events_tree.heading(column, text=title)
            self.events_tree.column(column, width=width, anchor="center" if column != "name" else "w")
        event_scroll = ttk.Scrollbar(list_panel, orient="vertical", command=self.events_tree.yview)
        self.events_tree.configure(yscrollcommand=event_scroll.set)
        self.event_summary_var = tk.StringVar(value="Выберите мероприятие — здесь появится краткая информация")
        summary = ttk.Label(list_panel, textvariable=self.event_summary_var, wraplength=650, justify="left", padding=(8, 8))
        summary.pack(side="bottom", fill="x")
        event_scroll.pack(side="right", fill="y")
        self.events_tree.pack(side="left", fill="both", expand=True)
        self.events_tree.bind("<<TreeviewSelect>>", self.load_selected_event)

        form_panel.columnconfigure(1, weight=1)
        self.event_vars = {key: tk.StringVar() for key in ("date", "time", "place", "name", "participants", "link")}
        self.card_label_widgets = {}
        self.custom_field_vars = {}
        self.event_period_var = tk.StringVar(value="Укажите дату — программа определит отчетный месяц")
        self.event_vars["date"].trace_add("write", self.update_event_period_hint)
        row = 0
        for key, label, width in (
            ("date", "Дата (ДД.ММ.ГГГГ)", 18), ("time", "Время", 18), ("place", "Место", 45), ("name", "Название", 45),
        ):
            label_widget = ttk.Label(form_panel, text=label)
            label_widget.grid(row=row, column=0, sticky="nw", padx=(0, 8), pady=4)
            self.card_label_widgets[key] = label_widget
            entry = ttk.Entry(form_panel, textvariable=self.event_vars[key], width=width)
            entry.grid(row=row, column=1, sticky="ew", pady=4)
            row += 1
            if key == "date":
                ttk.Label(form_panel, textvariable=self.event_period_var, foreground="#8a6418").grid(row=row, column=1, sticky="w", pady=(0, 4))
                row += 1
        self.card_label_widgets["description"] = ttk.Label(form_panel, text="Краткое описание")
        self.card_label_widgets["description"].grid(row=row, column=0, sticky="nw", padx=(0, 8), pady=4)
        self.description_text = tk.Text(form_panel, height=7, wrap="word", font=("Segoe UI", 9), relief="solid", borderwidth=1)
        self.description_text.grid(row=row, column=1, sticky="nsew", pady=4)
        form_panel.rowconfigure(row, weight=1)
        row += 1
        self.card_label_widgets["participants"] = ttk.Label(form_panel, text="Участники / семьи")
        self.card_label_widgets["participants"].grid(row=row, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(form_panel, textvariable=self.event_vars["participants"], width=18).grid(row=row, column=1, sticky="w", pady=4)
        row += 1
        self.card_label_widgets["link"] = ttk.Label(form_panel, text="Ссылка")
        self.card_label_widgets["link"].grid(row=row, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(form_panel, textvariable=self.event_vars["link"]).grid(row=row, column=1, sticky="ew", pady=4)
        row += 1
        self.custom_fields_frame = ttk.Frame(form_panel)
        self.custom_fields_frame.grid(row=row, column=0, columnspan=2, sticky="ew")
        self.custom_fields_frame.columnconfigure(1, weight=1)
        row += 1
        ttk.Label(form_panel, text="Целевые показатели").grid(row=row, column=0, sticky="nw", padx=(0, 8), pady=4)
        target_box = ttk.Frame(form_panel)
        target_box.grid(row=row, column=1, sticky="ew", pady=4)
        self.event_targets = tk.Listbox(target_box, selectmode="multiple", exportselection=False, height=5, font=("Segoe UI", 9), activestyle="none")
        for target in self.store.data["targets"]:
            self.event_targets.insert("end", f"{target['code']}  {target['name']}")
        self.event_targets.pack(fill="x")
        self.auto_classify_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(target_box, text="Определять автоматически по методическим рекомендациям", variable=self.auto_classify_var).pack(anchor="w", pady=(5, 0))
        ttk.Button(target_box, text="Определить сейчас", command=self.suggest_targets).pack(anchor="w", pady=(4, 0))
        row += 1
        buttons = ttk.Frame(form_panel)
        buttons.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        ttk.Button(buttons, text="Сохранить", style="Primary.TButton", command=self.save_event).pack(side="left")
        ttk.Button(buttons, text="Очистить", command=self.new_event).pack(side="left", padx=8)
        ttk.Button(buttons, text="Удалить", style="Danger.TButton", command=self.delete_event).pack(side="right")

    def _build_reports(self):
        self.reports_tab = ttk.Frame(self.notebook, padding=18)
        self.notebook.add(self.reports_tab, text="Отчеты")
        card = ttk.LabelFrame(self.reports_tab, text=" Формирование отчетов ", padding=18)
        card.pack(fill="x")
        card.columnconfigure(1, weight=1)
        current_report_month = reporting_period(date.today())[1]
        self.report_month_var = tk.StringVar(value=MONTHS[current_report_month])
        self.report_folder_var = tk.StringVar(value=str(REPORTS_PATH))
        ttk.Label(card, text="Отчетный месяц").grid(row=0, column=0, sticky="w", padx=(0, 10), pady=6)
        ttk.Combobox(card, textvariable=self.report_month_var, values=MONTHS, state="readonly", width=18).grid(row=0, column=1, sticky="w", pady=6)
        ttk.Label(card, text="Период: с 25-го предыдущего месяца по 24-е число выбранного", foreground="#597084").grid(row=0, column=2, sticky="w", padx=(8, 0))
        ttk.Label(card, text="Папка выгрузки").grid(row=1, column=0, sticky="w", padx=(0, 10), pady=6)
        ttk.Entry(card, textvariable=self.report_folder_var).grid(row=1, column=1, sticky="ew", pady=6)
        ttk.Button(card, text="Выбрать", command=self.choose_report_folder).grid(row=1, column=2, padx=(8, 0))
        actions = ttk.Frame(card)
        actions.grid(row=2, column=0, columnspan=3, sticky="w", pady=(14, 0))
        ttk.Button(actions, text="Выгрузить все 3 отчета", style="Accent.TButton", command=self.export_everything).pack(side="left")
        ttk.Button(actions, text="Приложение 1", command=lambda: self.export_one("app1")).pack(side="left", padx=(10, 0))
        ttk.Button(actions, text="Приложение 2", command=lambda: self.export_one("app2")).pack(side="left", padx=(8, 0))
        ttk.Button(actions, text="Сводка Excel", command=lambda: self.export_one("summary")).pack(side="left", padx=(8, 0))
        ttk.Button(actions, text="Открыть папку", command=self.open_report_folder).pack(side="left", padx=(8, 0))

        previews = ttk.Frame(card)
        previews.grid(row=3, column=0, columnspan=3, sticky="w", pady=(10, 0))
        ttk.Button(previews, text="Предпросмотр приложения 1", command=lambda: self.preview_report("app1")).pack(side="left")
        ttk.Button(previews, text="Предпросмотр приложения 2", command=lambda: self.preview_report("app2")).pack(side="left", padx=(8, 0))

        info = ttk.LabelFrame(self.reports_tab, text=" Состав выгрузки ", padding=16)
        info.pack(fill="both", expand=True, pady=(18, 0))
        text = (
            "Приложение 1 (.docx)\nНарастающие фактические значения по пяти строкам федеральной формы на конец выбранного месяца.\n\n"
            "Приложение 2 (.docx)\nЖурнал за период с 25-го предыдущего месяца по 24-е число выбранного, автоматически сгруппированный по целевым показателям.\n\n"
            "Сводные данные (.xlsx)\nОтдельный лист на каждый месяц и общий лист расчетов: план нарастающим, разница планов, факт за месяц и нарастающим, остаток и требуемый охват с переносом."
        )
        ttk.Label(info, text=text, wraplength=1100, justify="left").pack(anchor="nw")

    def _build_form_settings(self):
        self.forms_tab = ttk.Frame(self.notebook, padding=12)
        self.notebook.add(self.forms_tab, text="Настройка форм")
        tabs = ttk.Notebook(self.forms_tab)
        tabs.pack(fill="both", expand=True)

        targets_page = ttk.Frame(tabs, padding=12)
        reports_page = ttk.Frame(tabs, padding=12)
        cards_page = ttk.Frame(tabs, padding=12)
        tabs.add(targets_page, text="Показатели")
        tabs.add(reports_page, text="Отчетные формы")
        tabs.add(cards_page, text="Карточка мероприятия")

        targets_page.columnconfigure(1, weight=1)
        targets_page.rowconfigure(0, weight=1)
        left = ttk.Frame(targets_page)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        self.config_targets_tree = ttk.Treeview(left, columns=("code", "row", "name"), show="headings", height=18)
        for column, title, width in (("code", "Код", 80), ("row", "Строка", 70), ("name", "Название", 300)):
            self.config_targets_tree.heading(column, text=title)
            self.config_targets_tree.column(column, width=width, anchor="w")
        self.config_targets_tree.pack(fill="both", expand=True)
        self.config_targets_tree.bind("<<TreeviewSelect>>", self.load_target_settings)
        target_buttons = ttk.Frame(left)
        target_buttons.pack(fill="x", pady=(8, 0))
        ttk.Button(target_buttons, text="Добавить", command=self.new_target).pack(side="left")
        ttk.Button(target_buttons, text="Удалить", style="Danger.TButton", command=self.delete_target).pack(side="left", padx=6)

        editor = ttk.LabelFrame(targets_page, text=" Параметры показателя ", padding=12)
        editor.grid(row=0, column=1, sticky="nsew")
        editor.columnconfigure(1, weight=1)
        self.target_edit_id = None
        self.target_edit_vars = {key: tk.StringVar() for key in ("code", "report_row", "name")}
        for row, (key, label) in enumerate((("code", "Код"), ("report_row", "№ строки в приложении 1"), ("name", "Рабочее название"))):
            ttk.Label(editor, text=label).grid(row=row, column=0, sticky="nw", padx=(0, 8), pady=4)
            ttk.Entry(editor, textvariable=self.target_edit_vars[key]).grid(row=row, column=1, sticky="ew", pady=4)
        ttk.Label(editor, text="Официальное описание строки приложения 1").grid(row=3, column=0, sticky="nw", padx=(0, 8), pady=4)
        self.target_report_name_text = tk.Text(editor, height=5, wrap="word")
        self.target_report_name_text.grid(row=3, column=1, sticky="nsew", pady=4)
        ttk.Label(editor, text="Заголовок раздела приложения 2").grid(row=4, column=0, sticky="nw", padx=(0, 8), pady=4)
        self.target_section_text = tk.Text(editor, height=4, wrap="word")
        self.target_section_text.grid(row=4, column=1, sticky="nsew", pady=4)
        ttk.Label(editor, text="Ключевые слова через запятую").grid(row=5, column=0, sticky="nw", padx=(0, 8), pady=4)
        self.target_keywords_text = tk.Text(editor, height=4, wrap="word")
        self.target_keywords_text.grid(row=5, column=1, sticky="nsew", pady=4)
        editor.rowconfigure((3, 4, 5), weight=1)
        ttk.Button(editor, text="Сохранить показатель", style="Primary.TButton", command=self.save_target_settings).grid(row=6, column=1, sticky="w", pady=(10, 0))

        self.report_setting_vars = {
            "appendix_1_title": tk.StringVar(), "appendix_1_subtitle": tk.StringVar(),
            "appendix_2_title": tk.StringVar(),
        }
        self.report_column_vars = {
            "appendix_1_columns": [tk.StringVar() for _ in range(3)],
            "appendix_2_columns": [tk.StringVar() for _ in range(5)],
        }
        app1 = ttk.LabelFrame(reports_page, text=" Приложение 1 ", padding=12)
        app1.pack(fill="x", pady=(0, 12))
        app1.columnconfigure(1, weight=1)
        ttk.Label(app1, text="Заголовок").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(app1, textvariable=self.report_setting_vars["appendix_1_title"]).grid(row=0, column=1, sticky="ew", pady=4)
        ttk.Label(app1, text="Подзаголовок").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(app1, textvariable=self.report_setting_vars["appendix_1_subtitle"]).grid(row=1, column=1, sticky="ew", pady=4)
        for index, variable in enumerate(self.report_column_vars["appendix_1_columns"]):
            ttk.Label(app1, text=f"Столбец {index + 1}").grid(row=index + 2, column=0, sticky="w", padx=(0, 8), pady=4)
            ttk.Entry(app1, textvariable=variable).grid(row=index + 2, column=1, sticky="ew", pady=4)

        app2 = ttk.LabelFrame(reports_page, text=" Приложение 2 ", padding=12)
        app2.pack(fill="x")
        app2.columnconfigure(1, weight=1)
        ttk.Label(app2, text="Заголовок").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(app2, textvariable=self.report_setting_vars["appendix_2_title"]).grid(row=0, column=1, sticky="ew", pady=4)
        for index, variable in enumerate(self.report_column_vars["appendix_2_columns"]):
            ttk.Label(app2, text=f"Столбец {index + 1}").grid(row=index + 1, column=0, sticky="w", padx=(0, 8), pady=4)
            ttk.Entry(app2, textvariable=variable).grid(row=index + 1, column=1, sticky="ew", pady=4)
        ttk.Button(reports_page, text="Сохранить формы отчетов", style="Primary.TButton", command=self.save_report_settings).pack(anchor="w", pady=12)

        labels = ttk.LabelFrame(cards_page, text=" Названия стандартных полей ", padding=12)
        labels.pack(fill="x")
        labels.columnconfigure(1, weight=1)
        self.card_label_vars = {}
        for row, key in enumerate(("date", "time", "place", "name", "description", "participants", "link")):
            variable = tk.StringVar()
            self.card_label_vars[key] = variable
            ttk.Label(labels, text=key).grid(row=row, column=0, sticky="w", padx=(0, 8), pady=3)
            ttk.Entry(labels, textvariable=variable).grid(row=row, column=1, sticky="ew", pady=3)
        ttk.Button(labels, text="Сохранить названия полей", style="Primary.TButton", command=self.save_card_labels).grid(row=7, column=1, sticky="w", pady=(8, 0))

        custom = ttk.LabelFrame(cards_page, text=" Дополнительные поля карточки ", padding=12)
        custom.pack(fill="both", expand=True, pady=(12, 0))
        self.custom_fields_tree = ttk.Treeview(custom, columns=("label",), show="headings", height=7)
        self.custom_fields_tree.heading("label", text="Название поля")
        self.custom_fields_tree.column("label", width=500)
        self.custom_fields_tree.pack(fill="both", expand=True)
        custom_buttons = ttk.Frame(custom)
        custom_buttons.pack(fill="x", pady=(8, 0))
        ttk.Button(custom_buttons, text="Добавить поле", command=self.add_custom_field).pack(side="left")
        ttk.Button(custom_buttons, text="Переименовать", command=self.rename_custom_field).pack(side="left", padx=6)
        ttk.Button(custom_buttons, text="Удалить", style="Danger.TButton", command=self.delete_custom_field).pack(side="left")

    def _build_press_releases(self):
        self.press_tab = ttk.Frame(self.notebook, padding=16)
        self.notebook.add(self.press_tab, text="Пресс-релизы")
        settings = ttk.LabelFrame(self.press_tab, text=" Подключение к DeepSeek ", padding=8)
        settings.pack(fill="x")
        settings.columnconfigure(1, weight=1)
        settings.columnconfigure(3, weight=1)
        self.api_url_var = tk.StringVar()
        self.api_model_var = tk.StringVar()
        self.api_key_var = tk.StringVar()
        ttk.Label(settings, text="URL API").grid(row=0, column=0, sticky="w", padx=(0, 6), pady=3)
        ttk.Entry(settings, textvariable=self.api_url_var).grid(row=0, column=1, sticky="ew", padx=(0, 12), pady=3)
        ttk.Label(settings, text="Модель").grid(row=0, column=2, sticky="w", padx=(0, 6), pady=3)
        ttk.Entry(settings, textvariable=self.api_model_var, width=20).grid(row=0, column=3, sticky="ew", pady=3)
        ttk.Label(settings, text="API-ключ").grid(row=1, column=0, sticky="w", padx=(0, 6), pady=3)
        ttk.Entry(settings, textvariable=self.api_key_var, show="•").grid(row=1, column=1, sticky="ew", padx=(0, 12), pady=3)
        self.remember_api_key_var = tk.BooleanVar(value=True)
        key_actions = ttk.Frame(settings)
        key_actions.grid(row=1, column=2, columnspan=2, sticky="w", pady=3)
        ttk.Checkbutton(
            key_actions,
            text="Запомнить зашифрованно",
            variable=self.remember_api_key_var,
        ).pack(side="left")
        ttk.Button(key_actions, text="Удалить ключ", command=self.forget_api_key).pack(side="left", padx=8)

        selector = ttk.Frame(self.press_tab)
        selector.pack(fill="x", pady=12)
        ttk.Label(selector, text="Мероприятие").pack(side="left")
        self.press_event_var = tk.StringVar()
        self.press_event_combo = ttk.Combobox(selector, textvariable=self.press_event_var, state="readonly", width=80)
        self.press_event_combo.pack(side="left", fill="x", expand=True, padx=8)
        self.press_event_combo.bind("<<ComboboxSelected>>", self.load_press_event)
        self.press_event_ids = []
        self.press_context_var = tk.StringVar(value="Выберите мероприятие")
        ttk.Label(self.press_tab, textvariable=self.press_context_var, wraplength=1200, justify="left").pack(fill="x", pady=(0, 8))
        description_frame = ttk.LabelFrame(self.press_tab, text=" Краткое описание выбранного мероприятия ", padding=8)
        description_frame.pack(fill="x", pady=(0, 8))
        self.press_description_text = tk.Text(description_frame, height=3, wrap="word", font=("Segoe UI", 10), padx=8, pady=6)
        self.press_description_text.pack(fill="x")
        self.press_description_text.configure(state="disabled")
        ttk.Label(self.press_tab, text="Инструкция для модели").pack(anchor="w")
        self.press_instruction_text = tk.Text(self.press_tab, height=2, wrap="word")
        self.press_instruction_text.pack(fill="x", pady=(3, 8))
        buttons = ttk.Frame(self.press_tab)
        buttons.pack(fill="x", pady=(0, 8))
        self.generate_press_button = ttk.Button(
            buttons,
            text="Сгенерировать пресс-релиз",
            style="Accent.TButton",
            command=self.generate_press_release,
        )
        self.generate_press_button.pack(side="left")
        ttk.Button(buttons, text="Сохранить текст", command=self.save_press_release).pack(side="left", padx=8)
        ttk.Button(buttons, text="Копировать", command=self.copy_press_release).pack(side="left")
        ttk.Button(buttons, text="Выгрузить в Word", command=self.export_press_release_word).pack(side="left", padx=8)
        ttk.Label(self.press_tab, text="Текст пресс-релиза").pack(anchor="w")
        self.press_release_text = tk.Text(self.press_tab, height=10, wrap="word", font=("Segoe UI", 10), undo=True)
        self.press_release_text.pack(fill="both", expand=True, pady=(3, 0))
        self.load_saved_api_key()

    def _build_status(self):
        self.status_var = tk.StringVar(value="Готово")
        status = tk.Label(self, textvariable=self.status_var, anchor="w", bg="#dce8f2", fg="#3d596f", padx=18, pady=6, font=("Segoe UI", 9))
        status.pack(fill="x", side="bottom")

    def refresh_all(self):
        data = self.store.data
        self.organization_var.set(data["organization"])
        self.year_var.set(str(data["year"]))
        self.header_year.set(str(data["year"]))
        current_target_id = self.target_id_from_combo()
        names = [f"{item['id']} | {item['name']}" for item in data["targets"]]
        self.plan_target_combo["values"] = names
        matching_name = next((name for name in names if name.startswith(f"{current_target_id} | ")), None)
        self.plan_target_var.set(matching_name or names[0])
        self.refresh_targets()
        self.refresh_event_target_list()
        self.refresh_card_fields()
        self.refresh_events()
        self.refresh_dashboard()
        self.load_plan_value()
        self.refresh_form_settings()
        self.refresh_press_events()
        self.select_latest_report_month()

    def refresh_dashboard(self):
        events = []
        months = set()
        for event in self.store.data["events"]:
            parsed = parse_event_date(event.get("date", ""))
            if parsed and reporting_period(parsed)[0] == int(self.store.data["year"]):
                events.append(event)
                months.add(reporting_period(parsed)[1])
        self.metric_events.set(str(len(events)))
        self.metric_people.set(f"{sum(safe_int(event['participants']) for event in events):,}".replace(",", " "))
        self.metric_filled.set(f"{len(months)} / 12")
        configured = sum(1 for target in self.store.data["targets"] if any(target["plan"]))
        self.metric_ready.set(f"{configured} / {len(self.store.data['targets'])}")

    def report_months_with_events(self):
        report_year = int(self.store.data["year"])
        return sorted({
            reporting_period(parsed)[1]
            for event in self.store.data["events"]
            if (parsed := parse_event_date(event.get("date", "")))
            and reporting_period(parsed)[0] == report_year
        })

    def select_latest_report_month(self):
        if self.report_month_initialized:
            return
        months = self.report_months_with_events()
        if months:
            self.report_month_var.set(MONTHS[months[-1]])
        self.report_month_initialized = True

    def save_settings(self):
        year = safe_int(self.year_var.get())
        if not 2020 <= year <= 2100:
            messagebox.showerror("Некорректный год", "Укажите год от 2020 до 2100.")
            return
        organization = self.organization_var.get().strip()
        if not organization:
            messagebox.showerror("Не заполнено", "Укажите наименование организации.")
            return
        self.store.data["year"] = year
        self.store.data["organization"] = organization
        self.store.save()
        self.header_year.set(str(year))
        self.report_month_initialized = False
        self.refresh_all()
        self.set_status("Реквизиты сохранены")

    def refresh_form_settings(self):
        selected = self.config_targets_tree.selection()
        self.config_targets_tree.delete(*self.config_targets_tree.get_children())
        for target in self.store.data["targets"]:
            self.config_targets_tree.insert("", "end", iid=target["id"], values=(target["code"], target["report_row"], target["name"]))
        if selected and self.config_targets_tree.exists(selected[0]):
            self.config_targets_tree.selection_set(selected[0])
        report_settings = self.store.data["report_settings"]
        for key, variable in self.report_setting_vars.items():
            variable.set(report_settings[key])
        for key, variables in self.report_column_vars.items():
            for variable, value in zip(variables, report_settings[key]):
                variable.set(value)
        for key, variable in self.card_label_vars.items():
            variable.set(self.store.data["card_labels"][key])
        selected_custom = self.custom_fields_tree.selection()
        self.custom_fields_tree.delete(*self.custom_fields_tree.get_children())
        for field in self.store.data.get("custom_fields", []):
            self.custom_fields_tree.insert("", "end", iid=field["id"], values=(field["label"],))
        if selected_custom and self.custom_fields_tree.exists(selected_custom[0]):
            self.custom_fields_tree.selection_set(selected_custom[0])

    def load_target_settings(self, _event=None):
        selection = self.config_targets_tree.selection()
        if not selection:
            return
        target = next((item for item in self.store.data["targets"] if item["id"] == selection[0]), None)
        if not target:
            return
        self.target_edit_id = target["id"]
        for key, variable in self.target_edit_vars.items():
            variable.set(target[key])
        for widget, value in (
            (self.target_report_name_text, target["report_name"]),
            (self.target_section_text, target["section"]),
            (self.target_keywords_text, ", ".join(target.get("keywords", []))),
        ):
            widget.delete("1.0", "end")
            widget.insert("1.0", value)

    def new_target(self):
        self.target_edit_id = None
        self.config_targets_tree.selection_remove(self.config_targets_tree.selection())
        number = len(self.store.data["targets"]) + 1
        self.target_edit_vars["code"].set(f"ЦП{number}")
        self.target_edit_vars["report_row"].set(str(number).zfill(2))
        self.target_edit_vars["name"].set("Новый целевой показатель")
        for widget in (self.target_report_name_text, self.target_section_text, self.target_keywords_text):
            widget.delete("1.0", "end")

    def save_target_settings(self):
        values = {key: variable.get().strip() for key, variable in self.target_edit_vars.items()}
        report_name = self.target_report_name_text.get("1.0", "end").strip()
        section = self.target_section_text.get("1.0", "end").strip()
        keywords = [item.strip().lower() for item in self.target_keywords_text.get("1.0", "end").split(",") if item.strip()]
        if not all(values.values()) or not report_name or not section:
            messagebox.showerror("Не заполнено", "Заполните код, номер строки, рабочее название и описания обеих форм.")
            return
        if self.target_edit_id:
            target = next(item for item in self.store.data["targets"] if item["id"] == self.target_edit_id)
            target.update(values)
            target.update({"report_name": report_name, "section": section, "keywords": keywords})
        else:
            self.target_edit_id = f"custom-{uuid.uuid4().hex[:10]}"
            self.store.data["targets"].append({
                "id": self.target_edit_id, **values, "report_name": report_name, "section": section,
                "keywords": keywords, "plan": [0] * 12,
            })
        self.store.save()
        self.refresh_all()
        self.config_targets_tree.selection_set(self.target_edit_id)
        self.set_status("Параметры целевого показателя сохранены")

    def delete_target(self):
        selection = self.config_targets_tree.selection()
        if not selection:
            messagebox.showinfo("Удаление", "Выберите показатель.")
            return
        if len(self.store.data["targets"]) == 1:
            messagebox.showerror("Удаление", "В программе должен остаться хотя бы один показатель.")
            return
        target_id = selection[0]
        if not messagebox.askyesno("Удалить показатель", "Показатель будет удален из планов и карточек мероприятий. Продолжить?"):
            return
        self.store.data["targets"] = [item for item in self.store.data["targets"] if item["id"] != target_id]
        for event in self.store.data["events"]:
            event["target_ids"] = [item for item in event.get("target_ids", []) if item != target_id]
        self.target_edit_id = None
        self.store.save()
        self.refresh_all()
        self.new_target()
        self.set_status("Целевой показатель удален")

    def save_report_settings(self):
        settings = self.store.data["report_settings"]
        for key, variable in self.report_setting_vars.items():
            value = variable.get().strip()
            if not value:
                messagebox.showerror("Не заполнено", "Заголовки форм не могут быть пустыми.")
                return
            settings[key] = value
        for key, variables in self.report_column_vars.items():
            values = [variable.get().strip() for variable in variables]
            if not all(values):
                messagebox.showerror("Не заполнено", "Названия столбцов форм не могут быть пустыми.")
                return
            settings[key] = values
        self.store.save()
        self.set_status("Настройки приложений 1 и 2 сохранены")

    def save_card_labels(self):
        values = {key: variable.get().strip() for key, variable in self.card_label_vars.items()}
        if not all(values.values()):
            messagebox.showerror("Не заполнено", "Названия полей карточки не могут быть пустыми.")
            return
        self.store.data["card_labels"].update(values)
        self.store.save()
        self.refresh_card_fields()
        self.set_status("Названия полей карточки обновлены")

    def add_custom_field(self):
        label = simpledialog.askstring("Новое поле", "Название дополнительного поля:", parent=self)
        if not label or not label.strip():
            return
        self.store.data["custom_fields"].append({"id": f"field-{uuid.uuid4().hex[:10]}", "label": label.strip()})
        self.store.save()
        self.refresh_form_settings()
        self.refresh_card_fields()

    def rename_custom_field(self):
        selection = self.custom_fields_tree.selection()
        if not selection:
            messagebox.showinfo("Переименование", "Выберите дополнительное поле.")
            return
        field = next(item for item in self.store.data["custom_fields"] if item["id"] == selection[0])
        label = simpledialog.askstring("Переименовать поле", "Новое название:", initialvalue=field["label"], parent=self)
        if not label or not label.strip():
            return
        field["label"] = label.strip()
        self.store.save()
        self.refresh_form_settings()
        self.refresh_card_fields()

    def delete_custom_field(self):
        selection = self.custom_fields_tree.selection()
        if not selection:
            messagebox.showinfo("Удаление", "Выберите дополнительное поле.")
            return
        field_id = selection[0]
        if not messagebox.askyesno("Удалить поле", "Поле и введенные в него данные будут удалены из всех карточек. Продолжить?"):
            return
        self.store.data["custom_fields"] = [item for item in self.store.data["custom_fields"] if item["id"] != field_id]
        for event in self.store.data["events"]:
            event.get("custom_fields", {}).pop(field_id, None)
        self.store.save()
        self.refresh_form_settings()
        self.refresh_card_fields()

    def target_id_from_combo(self):
        return self.plan_target_var.get().split(" | ", 1)[0]

    def load_plan_value(self, _event=None):
        target_id = self.target_id_from_combo()
        if not target_id:
            return
        month = MONTHS.index(self.plan_month_var.get())
        target = next(item for item in self.store.data["targets"] if item["id"] == target_id)
        self.plan_value_var.set(str(target["plan"][month]))
        self.plan_name_var.set(target["name"])

    def save_plan(self):
        value_text = self.plan_value_var.get().strip()
        if not value_text.isdigit():
            messagebox.showerror("Некорректное значение", "План должен быть целым неотрицательным числом.")
            return
        target_id = self.target_id_from_combo()
        month = MONTHS.index(self.plan_month_var.get())
        target = next(item for item in self.store.data["targets"] if item["id"] == target_id)
        name = self.plan_name_var.get().strip()
        if not name:
            messagebox.showerror("Не заполнено", "Укажите название целевого показателя.")
            return
        value = int(value_text)
        if month and value < target["plan"][month - 1]:
            if not messagebox.askyesno("Уменьшение плана", "Нарастающий план меньше предыдущего месяца. Все равно сохранить?"):
                return
        target["name"] = name
        target["plan"][month] = value
        self.store.save()
        self.refresh_all()
        self.set_status(f"План за {MONTHS[month].lower()} сохранен")

    def refresh_targets(self):
        selected = self.targets_tree.selection()
        self.targets_tree.delete(*self.targets_tree.get_children())
        names = {item["id"]: item["name"] for item in self.store.data["targets"]}
        for target in self.store.data["targets"]:
            for row in calculate_target(self.store.data, target["id"]):
                item_id = f"{target['id']}::{row['month']}"
                self.targets_tree.insert("", "end", iid=item_id, values=(
                    names[target["id"]], MONTHS[row["month"]], row["cumulative_plan"], row["monthly_plan"],
                    row["actual"], row["actual_cumulative"], row["balance"], row["required"],
                ))
        if selected and self.targets_tree.exists(selected[0]):
            self.targets_tree.selection_set(selected[0])

    def select_plan_row(self, _event=None):
        selection = self.targets_tree.selection()
        if not selection:
            return
        target_id, month = selection[0].rsplit("::", 1)
        target = next(item for item in self.store.data["targets"] if item["id"] == target_id)
        self.plan_target_var.set(f"{target_id} | {target['name']}")
        self.plan_month_var.set(MONTHS[int(month)])
        self.load_plan_value()

    def refresh_event_target_list(self):
        selected_ids = []
        if self.selected_event_id:
            event = next((item for item in self.store.data["events"] if item["id"] == self.selected_event_id), None)
            if event:
                selected_ids = event.get("target_ids", [])
        self.event_targets.delete(0, "end")
        for index, target in enumerate(self.store.data["targets"]):
            self.event_targets.insert("end", f"{target['code']}  {target['name']}")
            if target["id"] in selected_ids:
                self.event_targets.selection_set(index)

    def refresh_card_fields(self):
        for key, widget in self.card_label_widgets.items():
            widget.configure(text=self.store.data["card_labels"][key])
        existing_values = {key: variable.get() for key, variable in self.custom_field_vars.items()}
        if self.selected_event_id:
            event = next((item for item in self.store.data["events"] if item["id"] == self.selected_event_id), None)
            if event:
                existing_values.update(event.get("custom_fields", {}))
        for widget in self.custom_fields_frame.winfo_children():
            widget.destroy()
        self.custom_field_vars = {}
        for row, field in enumerate(self.store.data.get("custom_fields", [])):
            variable = tk.StringVar(value=existing_values.get(field["id"], ""))
            self.custom_field_vars[field["id"]] = variable
            ttk.Label(self.custom_fields_frame, text=field["label"]).grid(row=row, column=0, sticky="w", padx=(0, 8), pady=4)
            ttk.Entry(self.custom_fields_frame, textvariable=variable).grid(row=row, column=1, sticky="ew", pady=4)

    def search_event(self):
        query = self.search_var.get().strip()
        if not query:
            return
        self.event_filter_var.set("Все месяцы")
        self.refresh_events()
        matches = self.events_tree.get_children()
        if not matches:
            messagebox.showinfo("Поиск", "Мероприятия по указанной дате или названию не найдены.")
            return
        first = matches[0]
        self.events_tree.selection_set(first)
        self.events_tree.focus(first)
        self.events_tree.see(first)
        self.load_selected_event()
        self.set_status(f"Найдено мероприятий: {len(matches)}")

    def clear_search(self):
        self.search_var.set("")
        self.refresh_events()
        self.set_status("Поиск сброшен")

    def refresh_events(self):
        current = self.selected_event_id
        self.events_tree.delete(*self.events_tree.get_children())
        code_map = {item["id"]: item["code"] for item in self.store.data["targets"]}
        filter_value = self.event_filter_var.get()
        events = []
        report_year = int(self.store.data["year"])
        for event in self.store.data["events"]:
            parsed = parse_event_date(event.get("date", ""))
            period = reporting_period(parsed) if parsed else None
            if not period or period[0] != report_year:
                continue
            if filter_value != "Все месяцы" and period[1] != MONTHS.index(filter_value):
                continue
            query = self.search_var.get().strip().lower()
            if query and query not in event.get("date", "").lower() and query not in event.get("name", "").lower():
                continue
            events.append((parsed, period, event))
        events.sort(key=lambda item: (item[0], item[2].get("time", ""), item[2].get("name", "")))
        for _parsed, period, event in events:
            codes = ", ".join(code_map[x] for x in event.get("target_ids", []) if x in code_map)
            participants = "" if event.get("participants") is None else event["participants"]
            status = "Готово" if event_is_complete(event) else "Черновик"
            self.events_tree.insert("", "end", iid=event["id"], values=(
                event["date"], MONTHS[period[1]], event["name"], codes or "—", participants, status,
            ))
        if current and self.events_tree.exists(current):
            self.events_tree.selection_set(current)

    def new_event(self):
        self.selected_event_id = None
        for variable in self.event_vars.values():
            variable.set("")
        self.description_text.delete("1.0", "end")
        self.event_targets.selection_clear(0, "end")
        for variable in self.custom_field_vars.values():
            variable.set("")
        self.auto_classify_var.set(True)
        self.events_tree.selection_remove(self.events_tree.selection())
        self.event_summary_var.set("Новая карточка мероприятия")
        self.set_status("Новая карточка мероприятия")

    def update_event_period_hint(self, *_args):
        parsed = parse_event_date(self.event_vars["date"].get())
        if not parsed:
            self.event_period_var.set("Укажите дату — программа определит отчетный месяц")
            return
        year, month = reporting_period(parsed)
        start, end = reporting_period_bounds(year, month)
        self.event_period_var.set(f"Отчет: {MONTHS[month]} {year} ({start:%d.%m.%Y}–{end:%d.%m.%Y})")

    def load_selected_event(self, _event=None):
        selection = self.events_tree.selection()
        if not selection:
            return
        event_id = selection[0]
        event = next((item for item in self.store.data["events"] if item["id"] == event_id), None)
        if not event:
            return
        self.selected_event_id = event_id
        for key in self.event_vars:
            value = event.get(key, "")
            self.event_vars[key].set("" if value is None else str(value))
        self.description_text.delete("1.0", "end")
        self.description_text.insert("1.0", event.get("description", ""))
        custom_values = event.get("custom_fields", {})
        for field_id, variable in self.custom_field_vars.items():
            variable.set(custom_values.get(field_id, ""))
        self.event_targets.selection_clear(0, "end")
        ids = [item["id"] for item in self.store.data["targets"]]
        for target_id in event.get("target_ids", []):
            if target_id in ids:
                self.event_targets.selection_set(ids.index(target_id))
        self.auto_classify_var.set(bool(event.get("auto_classify", False)))
        description = event.get("description", "").replace("\n", " ")
        if len(description) > 180:
            description = description[:177] + "..."
        self.event_summary_var.set(
            f"{event.get('date', '')} {event.get('time', '')} | {event.get('place', '')}\n"
            f"{event.get('name', '')}\n{description or 'Описание пока не заполнено'}"
        )

    def suggest_targets(self):
        selected = classify_event(
            self.event_vars["name"].get(),
            self.description_text.get("1.0", "end").strip(),
            self.event_vars["place"].get(),
            self.store.data["targets"],
        )
        self.event_targets.selection_clear(0, "end")
        ids = [item["id"] for item in self.store.data["targets"]]
        for target_id in selected:
            self.event_targets.selection_set(ids.index(target_id))
        codes = ", ".join(item["code"] for item in self.store.data["targets"] if item["id"] in selected)
        self.set_status(f"Автоматически определено: {codes or 'нет совпадений'}")
        return selected

    def save_event(self):
        parsed = parse_event_date(self.event_vars["date"].get())
        if not parsed:
            messagebox.showerror("Некорректная дата", "Введите дату в формате ДД.ММ.ГГГГ, например 15.03.2026.")
            return
        event_report_year, event_report_month = reporting_period(parsed)
        if event_report_year != int(self.store.data["year"]):
            if not messagebox.askyesno(
                "Другой отчетный год",
                f"Мероприятие относится к отчету за {MONTHS[event_report_month].lower()} {event_report_year} года, "
                f"а в программе выбран {self.store.data['year']} год. Все равно сохранить?",
            ):
                return
        if not self.event_vars["name"].get().strip():
            messagebox.showerror("Не заполнено", "Укажите название мероприятия.")
            return
        participants_text = self.event_vars["participants"].get().strip()
        if participants_text and not participants_text.isdigit():
            messagebox.showerror("Некорректное количество", "Количество участников должно быть пустым или целым неотрицательным числом.")
            return
        if self.auto_classify_var.get():
            target_ids = self.suggest_targets()
        else:
            targets = self.store.data["targets"]
            target_ids = [targets[index]["id"] for index in self.event_targets.curselection()]
        event = {
            "id": self.selected_event_id or str(uuid.uuid4()),
            "date": parsed.strftime("%d.%m.%Y"),
            "time": self.event_vars["time"].get().strip(),
            "place": self.event_vars["place"].get().strip(),
            "name": self.event_vars["name"].get().strip(),
            "description": self.description_text.get("1.0", "end").strip(),
            "target_ids": target_ids,
            "auto_classify": self.auto_classify_var.get(),
            "participants": int(participants_text) if participants_text else None,
            "link": self.event_vars["link"].get().strip(),
            "custom_fields": {field_id: variable.get().strip() for field_id, variable in self.custom_field_vars.items()},
            "press_release": next(
                (item.get("press_release", "") for item in self.store.data["events"] if item["id"] == self.selected_event_id),
                "",
            ),
        }
        if self.selected_event_id:
            index = next(i for i, item in enumerate(self.store.data["events"]) if item["id"] == self.selected_event_id)
            self.store.data["events"][index] = event
        else:
            self.store.data["events"].append(event)
        self.selected_event_id = event["id"]
        self.store.save()
        self.refresh_events()
        self.refresh_targets()
        self.refresh_dashboard()
        self.refresh_press_events()
        state = "готово" if event_is_complete(event) else "сохранено как черновик"
        self.set_status(f"Мероприятие {state}; отчетный месяц — {MONTHS[event_report_month]}")

    def delete_event(self):
        if not self.selected_event_id:
            messagebox.showinfo("Удаление", "Сначала выберите мероприятие.")
            return
        if not messagebox.askyesno("Удалить мероприятие", "Удалить выбранное мероприятие без возможности отмены?"):
            return
        self.store.data["events"] = [item for item in self.store.data["events"] if item["id"] != self.selected_event_id]
        self.store.save()
        self.new_event()
        self.refresh_events()
        self.refresh_targets()
        self.refresh_dashboard()
        self.refresh_press_events()
        self.set_status("Мероприятие удалено, показатели пересчитаны")

    def refresh_press_events(self):
        current_id = self._selected_press_event_id()
        events = sorted(
            self.store.data["events"],
            key=lambda item: (parse_event_date(item.get("date", "")) or date.max, item.get("name", "")),
        )
        self.press_event_ids = [event["id"] for event in events]
        values = [f"{event.get('date', '')} | {event.get('name', '')}" for event in events]
        self.press_event_combo["values"] = values
        settings = self.store.data["press_release_settings"]
        self.api_url_var.set(settings["base_url"])
        self.api_model_var.set(settings["model"])
        self.press_instruction_text.delete("1.0", "end")
        self.press_instruction_text.insert("1.0", settings["instruction"])
        if current_id in self.press_event_ids:
            index = self.press_event_ids.index(current_id)
            self.press_event_combo.current(index)
        elif values:
            self.press_event_combo.current(0)
        else:
            self.press_event_var.set("")
        self.load_press_event()

    def _selected_press_event_id(self):
        if not hasattr(self, "press_event_combo"):
            return None
        index = self.press_event_combo.current()
        return self.press_event_ids[index] if 0 <= index < len(self.press_event_ids) else None

    def _selected_press_event(self):
        event_id = self._selected_press_event_id()
        return next((item for item in self.store.data["events"] if item["id"] == event_id), None)

    def load_saved_api_key(self):
        try:
            saved = load_secret(API_KEY_PATH)
        except OSError:
            saved = ""
        if saved:
            self.api_key_var.set(saved)

    def remember_api_key(self):
        key = self.api_key_var.get().strip()
        if not key or not self.remember_api_key_var.get():
            return
        try:
            save_secret(key, API_KEY_PATH)
        except OSError as error:
            messagebox.showerror("Сохранение ключа", f"Не удалось зашифровать API-ключ:\n{error}")

    def forget_api_key(self):
        if not messagebox.askyesno("Удалить ключ", "Удалить зашифрованный API-ключ с этого компьютера?"):
            return
        delete_secret(API_KEY_PATH)
        self.api_key_var.set("")
        self.remember_api_key_var.set(False)
        self.set_status("Сохраненный API-ключ удален")

    def load_press_event(self, _event=None):
        event = self._selected_press_event()
        self.press_release_text.delete("1.0", "end")
        self.press_description_text.configure(state="normal")
        self.press_description_text.delete("1.0", "end")
        if not event:
            self.press_context_var.set("Сначала добавьте мероприятие")
            self.press_description_text.insert("1.0", "Краткое описание не выбрано")
            self.press_description_text.configure(state="disabled")
            return
        target_codes = [
            target["code"] for target in self.store.data["targets"] if target["id"] in event.get("target_ids", [])
        ]
        self.press_context_var.set(
            f"{event.get('date', '')} {event.get('time', '')} | {event.get('name', '')} | "
            f"ЦП: {', '.join(target_codes) or 'не определен'}"
        )
        self.press_description_text.insert(
            "1.0",
            event.get("description", "").strip() or "Краткое описание в карточке мероприятия пока не заполнено",
        )
        self.press_description_text.configure(state="disabled")
        self.press_release_text.insert("1.0", event.get("press_release", ""))

    def _press_prompt(self, event):
        labels = self.store.data["card_labels"]
        lines = [
            f"{labels['date']}: {event.get('date', '')}",
            f"{labels['time']}: {event.get('time', '')}",
            f"{labels['place']}: {event.get('place', '')}",
            f"{labels['name']}: {event.get('name', '')}",
            f"{labels['description']}: {event.get('description', '')}",
            f"{labels['participants']}: {'' if event.get('participants') is None else event.get('participants')}",
            f"{labels['link']}: {event.get('link', '')}",
        ]
        custom_values = event.get("custom_fields", {})
        for field in self.store.data.get("custom_fields", []):
            lines.append(f"{field['label']}: {custom_values.get(field['id'], '')}")
        return "Сформируй пресс-релиз только на основании следующих данных:\n" + "\n".join(lines)

    def _apply_press_release(self, event, content, status):
        event["press_release"] = content
        self.store.save()
        if self._selected_press_event_id() == event["id"]:
            self.press_release_text.delete("1.0", "end")
            self.press_release_text.insert("1.0", content)
        self.set_status(status)

    def generate_press_release(self):
        event = self._selected_press_event()
        if not event:
            messagebox.showinfo("Пресс-релиз", "Выберите мероприятие.")
            return
        api_key = self.api_key_var.get().strip() or os.environ.get("DEEPSEEK_API_KEY", "").strip()
        if not api_key:
            messagebox.showerror("Нет API-ключа", "Введите API-ключ DeepSeek или включите загрузку сохраненного ключа.")
            return
        self.remember_api_key()
        url = self.api_url_var.get().strip()
        model = self.api_model_var.get().strip()
        instruction = self.press_instruction_text.get("1.0", "end").strip()
        if not url.startswith("https://") or not model or not instruction:
            messagebox.showerror("Настройки API", "Укажите HTTPS URL API, модель и инструкцию.")
            return
        self.store.data["press_release_settings"].update({"base_url": url, "model": model, "instruction": instruction})
        self.store.save()
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": instruction},
                {"role": "user", "content": self._press_prompt(event)},
            ],
            "stream": False,
            "temperature": 0.5,
        }
        self.generate_press_button.configure(state="disabled", text="Формирование...")
        self.set_status("Формируется пресс-релиз через API...")

        def request_release():
            request = urllib.request.Request(
                url,
                data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                method="POST",
            )
            try:
                with urllib.request.urlopen(request, timeout=90) as response:
                    result = json.loads(response.read().decode("utf-8"))
                content = result["choices"][0]["message"]["content"].strip()
                self.after(0, lambda: self._finish_press_release(event["id"], content, None))
            except urllib.error.HTTPError as error:
                try:
                    details = error.read().decode("utf-8")[:1000]
                except Exception:
                    details = str(error)
                message = f"HTTP {error.code}: {details}"
                self.after(0, lambda message=message: self._finish_press_release(event["id"], None, message))
            except Exception as error:
                message = str(error)
                self.after(0, lambda message=message: self._finish_press_release(event["id"], None, message))

        threading.Thread(target=request_release, daemon=True).start()

    def _finish_press_release(self, event_id, content, error):
        self.generate_press_button.configure(state="normal", text="Сгенерировать пресс-релиз")
        event = next((item for item in self.store.data["events"] if item["id"] == event_id), None)
        if not event:
            return
        if error:
            self.set_status("Ошибка формирования пресс-релиза через DeepSeek")
            messagebox.showerror("Ошибка DeepSeek", f"Не удалось сформировать пресс-релиз:\n{error}")
            return
        self._apply_press_release(event, content, "Пресс-релиз сформирован через DeepSeek и сохранен")

    def save_press_release(self):
        event = self._selected_press_event()
        if not event:
            messagebox.showinfo("Пресс-релиз", "Выберите мероприятие.")
            return
        event["press_release"] = self.press_release_text.get("1.0", "end").strip()
        self.store.save()
        self.set_status("Текст пресс-релиза сохранен")

    def copy_press_release(self):
        text = self.press_release_text.get("1.0", "end").strip()
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)
            self.set_status("Пресс-релиз скопирован")

    def export_press_release_word(self):
        event = self._selected_press_event()
        if not event:
            messagebox.showinfo("Пресс-релиз", "Выберите мероприятие.")
            return
        text = self.press_release_text.get("1.0", "end").strip()
        if not text:
            messagebox.showerror("Нет текста", "Сначала сформируйте или введите текст пресс-релиза.")
            return
        event["press_release"] = text
        self.store.save()
        safe_name = re.sub(r'[<>:"/\\|?*]+', "_", event.get("name", "Пресс-релиз")).strip(" ._")[:80]
        initial = f"Пресс-релиз_{safe_name or 'мероприятие'}.docx"
        selected = filedialog.asksaveasfilename(
            parent=self,
            title="Сохранить пресс-релиз в Word",
            initialdir=self.report_folder_var.get() or str(REPORTS_PATH),
            initialfile=initial,
            defaultextension=".docx",
            filetypes=(("Документ Word", "*.docx"),),
        )
        if not selected:
            return
        try:
            path = export_press_release(self.store.snapshot(), event, text, Path(selected))
        except Exception as error:
            messagebox.showerror("Ошибка выгрузки", f"Не удалось создать документ Word:\n{error}")
            return
        self.set_status(f"Пресс-релиз сохранен: {path}")
        messagebox.showinfo("Пресс-релиз готов", f"Документ Word сохранен:\n{path}")

    def choose_report_folder(self):
        selected = filedialog.askdirectory(initialdir=self.report_folder_var.get() or str(BASE_DIR))
        if selected:
            self.report_folder_var.set(selected)

    def _report_context(self):
        folder = Path(self.report_folder_var.get().strip() or REPORTS_PATH)
        folder.mkdir(parents=True, exist_ok=True)
        month = MONTHS.index(self.report_month_var.get())
        return folder, month

    def resolve_appendix_2_month(self, month):
        year = int(self.store.data["year"])
        selected_events = [
            event for event in self.store.data["events"]
            if event_in_reporting_month(event, year, month) and event.get("target_ids")
        ]
        if selected_events:
            return month
        available = sorted({
            reporting_period(parsed)[1]
            for event in self.store.data["events"]
            if event.get("target_ids")
            and (parsed := parse_event_date(event.get("date", "")))
            and reporting_period(parsed)[0] == year
        })
        if not available:
            messagebox.showwarning(
                "Нет мероприятий для приложения 2",
                "Нет карточек, распределенных по целевым показателям. Проверьте целевые показатели в карточках мероприятий.",
            )
            return None
        latest = available[-1]
        if messagebox.askyesno(
            "Выбран пустой отчетный месяц",
            f"За {MONTHS[month].lower()} нет мероприятий для приложения 2. "
            f"Последний заполненный месяц — {MONTHS[latest].lower()}. Сформировать отчет за него?",
        ):
            self.report_month_var.set(MONTHS[latest])
            return latest
        return None

    def export_everything(self):
        try:
            folder, month = self._report_context()
            month = self.resolve_appendix_2_month(month)
            if month is None:
                return
            paths = export_all(self.store.snapshot(), folder, month)
        except Exception as error:
            messagebox.showerror("Ошибка выгрузки", f"Не удалось сформировать отчеты:\n{error}")
            return
        self.set_status(f"Сформировано файлов: {len(paths)}. Папка: {folder}")
        messagebox.showinfo("Отчеты готовы", "Сформированы:\n" + "\n".join(path.name for path in paths))

    def export_one(self, kind):
        try:
            folder, month = self._report_context()
            suffix = f"{self.store.data['year']}_{month + 1:02d}"
            if kind == "app1":
                path = export_appendix_1(self.store.snapshot(), folder / f"Приложение_1_{suffix}.docx", month)
            elif kind == "app2":
                month = self.resolve_appendix_2_month(month)
                if month is None:
                    return
                suffix = f"{self.store.data['year']}_{month + 1:02d}"
                path = export_appendix_2(self.store.snapshot(), folder / f"Приложение_2_{suffix}.docx", month)
            else:
                path = export_monthly_summary(self.store.snapshot(), folder / f"Сводные_данные_{self.store.data['year']}.xlsx")
        except Exception as error:
            messagebox.showerror("Ошибка выгрузки", f"Не удалось сформировать отчет:\n{error}")
            return
        self.set_status(f"Сформирован файл: {path}")
        messagebox.showinfo("Отчет готов", f"Файл сохранен:\n{path}")

    def preview_report(self, kind):
        _folder, month = self._report_context()
        data = self.store.snapshot()
        if kind == "app1":
            title = "Предпросмотр приложения 1"
            content = preview_appendix_1(data, month)
        else:
            month = self.resolve_appendix_2_month(month)
            if month is None:
                return
            title = "Предпросмотр приложения 2"
            content = preview_appendix_2(data, month)
        window = tk.Toplevel(self)
        window.title(title)
        window.geometry("1050x720")
        window.minsize(760, 500)
        window.transient(self)
        toolbar = ttk.Frame(window, padding=10)
        toolbar.pack(fill="x")
        ttk.Label(toolbar, text=title, style="Section.TLabel").pack(side="left")
        ttk.Button(toolbar, text="Выгрузить DOCX", style="Accent.TButton", command=lambda: self.export_one(kind)).pack(side="right")
        frame = ttk.Frame(window, padding=(10, 0, 10, 10))
        frame.pack(fill="both", expand=True)
        text = tk.Text(frame, wrap="word", font=("Segoe UI", 10), padx=14, pady=14, undo=False)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=text.yview)
        text.configure(yscrollcommand=scrollbar.set)
        text.insert("1.0", content)
        text.configure(state="disabled")
        text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.set_status(f"Открыт {title.lower()}")

    def open_report_folder(self):
        folder, _month = self._report_context()
        os.startfile(folder)

    def set_status(self, text):
        self.status_var.set(text)

    def _close(self):
        try:
            self.remember_api_key()
            self.store.save()
        finally:
            self.destroy()


def main():
    try:
        app = MinMolApp()
        app.mainloop()
    except Exception as error:
        messagebox.showerror("Ошибка запуска", f"Программа не может быть запущена:\n{error}")
        raise


if __name__ == "__main__":
    main()
