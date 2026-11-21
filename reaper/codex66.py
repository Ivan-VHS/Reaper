"""CODEX-66 capability catalogue for Reaper Studio.

The catalogue separates shipped behavior from partial protocol support and
planned work. It is metadata only: listing a capability never enables code.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable
import json


CATEGORIES = (
    ("ai-suggest", "Подсказки и анализ"),
    ("editor-nav", "Редактор и навигация"),
    ("debug-test", "Отладка и тестирование"),
    ("term-git", "Команды, Git и сборка"),
    ("perf-ergo", "Производительность и эргономика"),
    ("sec-collab", "Безопасность и совместная работа"),
)

STATUS_LABELS = {
    "implemented": "Реализовано",
    "partial": "Частично",
    "planned": "В плане",
    "not_supported": "Не поддерживается",
}


@dataclass(frozen=True, slots=True)
class CodexFeature:
    id: str
    category: str
    title: str
    status: str
    summary: str
    evidence: str
    action: str | None = None


_ROWS = (
    # 01–11 · подсказки и анализ
    ("01", "ai-suggest", "Локальное автодополнение REAPER", "implemented",
     "Предлагает ключевые слова, встроенные функции и символы открытого файла.",
     "Использует LanguageService и текущий документ. Это локальная подсказка, не облачная AI-генерация.",
     "completion"),
    ("02", "ai-suggest", "Контекстное окно IntelliSense", "implemented",
     "Открывает список кандидатов с выбором стрелками и вставкой по Enter или Tab.",
     "Работает по локальному индексу документа; межфайловое разрешение типов не заявляется.",
     "completion"),
    ("03", "ai-suggest", "AI-рефакторинг выделения", "planned",
     "Предложение переписывания выделенного кода с предпросмотром diff.",
     "AI-провайдера и безопасного слоя применения предложений в Studio пока нет."),
    ("04", "ai-suggest", "Генерация документации функций", "planned",
     "Создание комментариев и примеров для выбранного объявления.",
     "Автогенератор TSDoc/JSDoc не является частью Reaper runtime."),
    ("05", "ai-suggest", "Предсказание следующего курсора", "planned",
     "Навигация между предполагаемыми точками редактирования.",
     "Предиктивная модель и журнал редактирования не реализованы."),
    ("06", "ai-suggest", "Диагностика и объяснение ошибок", "partial",
     "Показывает ошибки парсера и диагностические сообщения языка.",
     "Проверка использует существующий parser; автоматическое исправление и типовой анализ не реализованы.",
     "check_source"),
    ("07", "ai-suggest", "Генерация unit-тестов", "planned",
     "Подготовка тестовых случаев по выбранной функции и граничным значениям.",
     "Встроенного генератора тестов и test explorer пока нет."),
    ("08", "ai-suggest", "Объяснение выражения", "planned",
     "Пошаговое объяснение выбранного выражения и потока данных.",
     "Отдельного explain-engine в текущем IDE/runtime нет."),
    ("09", "ai-suggest", "Анализ сложности алгоритма", "planned",
     "Поиск потенциально лишних проходов и оценка сложности.",
     "Статический complexity analyzer не подключён."),
    ("10", "ai-suggest", "Библиотека сниппетов", "planned",
     "Пользовательские шаблоны для повторяющихся конструкций REAPER/MOST.",
     "Управляемого snippet registry в Studio пока нет."),
    ("11", "ai-suggest", "Профили стиля кода", "planned",
     "Проверка форматирования и проектных соглашений.",
     "Отдельный formatter/linter с профилями ещё не интегрирован."),

    # 12–22 · редактор и навигация
    ("12", "editor-nav", "Множественные курсоры", "planned",
     "Синхронное редактирование нескольких выделений.",
     "Tk Text editor пока использует один основной курсор."),
    ("13", "editor-nav", "Палитра команд Ctrl+K", "implemented",
     "Поиск и запуск основных действий Studio с клавиатуры.",
     "Команды вызывают существующие обработчики Studio.",
     "command_palette"),
    ("14", "editor-nav", "Переход к определению", "implemented",
     "Переходит к объявлению символа в текущем открытом документе.",
     "Разрешение основано на локальном LanguageService; cross-file semantic navigation не заявлена.",
     "go_to_definition"),
    ("15", "editor-nav", "Breadcrumbs структуры", "planned",
     "Путь проекта, файла, функции и текущего блока.",
     "В Studio есть заголовок файла и дерево проекта, но нет структурной breadcrumbs-панели."),
    ("16", "editor-nav", "Сворачивание AST-блоков", "planned",
     "Сворачивание функций, условий и блоков на основе AST.",
     "AST folding UI и стабильная карта диапазонов ещё не подключены."),
    ("17", "editor-nav", "Подсветка парных скобок", "partial",
     "Подсветка лексических токенов и анализ несбалансированных разделителей.",
     "Парная подсветка курсорных скобок пока отсутствует; диагностика доступна через language service."),
    ("18", "editor-nav", "Перемещение строк", "planned",
     "Перенос строки или блока вверх/вниз с сохранением отступов.",
     "Команды Alt+Up/Down ещё не реализованы."),
    ("19", "editor-nav", "Дублирование строки", "planned",
     "Клонирование текущей строки без изменения буфера обмена.",
     "Отдельной команды duplicate-line пока нет."),
    ("20", "editor-nav", "Расширение выделения по AST", "planned",
     "Переход от слова к выражению, блоку и функции.",
     "AST-aware selection не реализован."),
    ("21", "editor-nav", "Поиск ссылок на символ", "implemented",
     "Находит вхождения символа в текущем документе и выводит номера строк.",
     "Использует лексический индекс LanguageService; строки и комментарии не считаются ссылками.",
     "find_references"),
    ("22", "editor-nav", "Разделённый редактор", "planned",
     "Одновременный просмотр двух документов и спецификации.",
     "Studio остаётся однодокументным редактором; multi-tab/split view не реализован."),

    # 23–33 · отладка и тестирование
    ("23", "debug-test", "Условные точки останова", "not_supported",
     "Остановка по выражению или условию счётчика.",
     "DAP явно сообщает supportsConditionalBreakpoints=false; доступны обычные line breakpoints."),
    ("24", "debug-test", "Logpoints без остановки", "planned",
     "Вывод значений переменных при прохождении строки.",
     "Logpoint runtime hook пока не реализован."),
    ("25", "debug-test", "Инспектор локальных переменных", "implemented",
     "Показывает локальные значения остановленного debug-сеанса.",
     "Значения приходят из RuntimeDebugger snapshot.",
     "show_variables"),
    ("26", "debug-test", "Проверка и запуск программы", "implemented",
     "Запускает проверку синтаксиса или программу из Studio.",
     "Check использует parser; Run использует существующий interpreter в worker thread.",
     "check_source"),
    ("27", "debug-test", "Покрытие строк", "planned",
     "Отчёт о выполненных и непокрытых строках/ветках.",
     "Инструментации coverage и панели отчётов пока нет."),
    ("28", "debug-test", "Стек вызовов", "implemented",
     "Показывает стек текущей отладки.",
     "Использует call_stack из RuntimeDebugger.",
     "show_call_stack"),
    ("29", "debug-test", "Watch-выражения", "planned",
     "Повторная оценка отслеживаемых выражений при каждом шаге.",
     "Отдельного watch evaluator нет; DAP evaluate отключён."),
    ("30", "debug-test", "Перезапуск текущего кадра", "not_supported",
     "Повторный запуск функции из выбранного stack frame.",
     "Restart Frame отсутствует в RuntimeDebugger и DAP."),
    ("31", "debug-test", "Снимок состояния памяти", "planned",
     "Сравнение доступных данных и состояния между шагами.",
     "Heap snapshot/debug memory inspector не реализован."),
    ("32", "debug-test", "Проверка синтаксиса и диагностика", "implemented",
     "Проверяет текущий REAPER-код и выводит ошибки парсера.",
     "Использует canonical parser; отдельный статический security scanner не подразумевается.",
     "check_source"),
    ("33", "debug-test", "Таймлайн исполнения", "planned",
     "Последовательность вызовов и временных отметок.",
     "Runtime event timeline и профилировщик пока не реализованы."),

    # 34–44 · команды, Git и сборка
    ("34", "term-git", "Встроенный терминал", "planned",
     "Интерактивная shell-сессия внутри Studio.",
     "Studio не открывает произвольную shell-сессию; команды запускаются отдельными явными workflow."),
    ("35", "term-git", "Git Gutter", "planned",
     "Маркеры добавленных и изменённых строк рядом с кодом.",
     "Git status/diff декорации в редакторе не реализованы."),
    ("36", "term-git", "Генератор commit message", "planned",
     "Подготовка сообщения коммита по проверенному diff.",
     "Git commit workflow не встроен в Studio."),
    ("37", "term-git", "Просмотр и принятие diff", "planned",
     "Просмотр diff и выборочное принятие блоков.",
     "Нет встроенного diff/staging UI."),
    ("38", "term-git", "Git blame", "planned",
     "Автор и коммит для выбранной строки.",
     "Blame viewer в Studio отсутствует."),
    ("39", "term-git", "Разрешение merge-конфликтов", "planned",
     "Сравнение ours/theirs и ручное разрешение конфликта.",
     "Conflict editor и автоматические merge-действия не подключены."),
    ("40", "term-git", "Команды Node.js и npm через NOO TAH", "implemented",
     "Запускает Node.js, проверку JavaScript, Inspector и npm-команды.",
     "Используется управляемый NOO TAH runtime; это не универсальный терминал.",
     "run_noo_tah_npm"),
    ("41", "term-git", "Менеджер Git stash", "planned",
     "Просмотр, сохранение и восстановление отложенных изменений.",
     "Git stash UI отсутствует."),
    ("42", "term-git", "Граф веток и тегов", "planned",
     "Граф истории репозитория и релизных точек.",
     "Встроенный Git history graph не реализован."),
    ("43", "term-git", "CI и pre-merge проверки", "partial",
     "Репозиторий проверяется CI при push/PR.",
     "Проверки существуют в GitHub Actions, но не управляются из локальной панели Studio."),
    ("44", "term-git", "Переключение Git worktree", "planned",
     "Работа с параллельными деревьями исходников.",
     "Worktree manager в IDE отсутствует."),

    # 45–55 · производительность и эргономика
    ("45", "perf-ergo", "Фоновый индекс символов документа", "partial",
     "Языковой сервис строит индекс открытого документа в фоне.",
     "Индекс ограничен одним документом; это не incremental AST или cross-file workspace index."),
    ("46", "perf-ergo", "Темы интерфейса", "implemented",
     "Системная, светлая, тёмная, рассвет, закат и ночная палитры.",
     "Выбор и сохранение темы доступны через меню Вид.",
     "toggle_ui_theme"),
    ("47", "perf-ergo", "Компактная плотность интерфейса", "planned",
     "Отдельный компактный режим для панелей и списков.",
     "Сохранённый density-профиль пока не реализован."),
    ("48", "perf-ergo", "Режим фокуса", "planned",
     "Скрытие второстепенных панелей и акцентов.",
     "Focus/Zen layout mode пока отсутствует."),
    ("49", "perf-ergo", "Моноширинный редактор", "implemented",
     "Код отображается шрифтом Cascadia Code с фиксированным размером.",
     "Шрифт задан настройкой виджета; отдельного font chooser нет."),
    ("50", "perf-ergo", "Локальные подсказки символов", "partial",
     "Подбор локальных идентификаторов, ключевых слов и builtin-функций.",
     "Подсказки не используют cloud AI, типовой inference или межфайловый индекс.",
     "completion"),
    ("51", "perf-ergo", "Автосохранение и восстановление сессии", "planned",
     "Автосохранение несохранённого буфера и восстановление после сбоя.",
     "В Studio действует явное сохранение и предупреждение о несохранённых изменениях."),
    ("52", "perf-ergo", "Клавиатурные команды", "partial",
     "Основные действия доступны через меню и сочетания клавиш.",
     "Не все действия IDE имеют настраиваемые keybindings.",
     "command_palette"),
    ("53", "perf-ergo", "Reduce Motion и Eco Visuals", "implemented",
     "Сохраняемые параметры доступности и ограничение анимаций.",
     "Настройки Reduce Motion, Eco и Expressive Motion доступны в меню Вид.",
     "show_motion_settings"),
    ("54", "perf-ergo", "Поиск по 66 возможностям", "implemented",
     "Поиск, фильтр категорий и просмотр зрелости функций.",
     "Нативный CODEX-66 каталог; статусы основаны на коде, не на рекламных обещаниях.",
     "show_codex66"),
    ("55", "perf-ergo", "Изменяемая компоновка Studio", "implemented",
     "Разделители панелей и размер главного окна можно менять.",
     "Используются Tk PanedWindow и resizable desktop layout."),

    # 56–66 · безопасность и совместная работа
    ("56", "sec-collab", "Сканер секретов", "planned",
     "Поиск токенов, приватных ключей и случайно сохранённых паролей.",
     "Секрет-сканер редактора пока не подключён."),
    ("57", "sec-collab", "Диагностика рискованных конструкций", "partial",
     "Parser и структурные диагностики выявляют ошибки исходного кода.",
     "Полного SAST, taint analysis и allow/deny policy для кода нет.",
     "check_source"),
    ("58", "sec-collab", "Аудит зависимостей и лицензий", "planned",
     "Инвентаризация зависимостей, лицензий и уязвимостей.",
     "Отдельный dependency/license audit panel не реализован."),
    ("59", "sec-collab", "Проверка перед запуском", "implemented",
     "Проверка синтаксиса доступна отдельно от запуска.",
     "Запуск остаётся явным действием пользователя; автозапуска при открытии проекта нет.",
     "check_source"),
    ("60", "sec-collab", "OS-изолированная песочница", "not_supported",
     "Изоляция процесса, файловой системы и сети для недоверенного кода.",
     "Interpreter quotas не являются OS sandbox. Запускайте только доверенные программы."),
    ("61", "sec-collab", "Живые курсоры соавторов", "planned",
     "Синхронизация позиций нескольких участников.",
     "Сетевой collaboration backend в Reaper Studio отсутствует."),
    ("62", "sec-collab", "Комментарии к строкам кода", "planned",
     "Контекстные review-комментарии с привязкой к диапазону.",
     "Review thread UI и сервер хранения комментариев отсутствуют."),
    ("63", "sec-collab", "Совместная отладка", "planned",
     "Общий debug-сеанс и состояние переменных.",
     "Live-share transport и control protocol не реализованы."),
    ("64", "sec-collab", "CI readiness для Pull Request", "partial",
     "GitHub Actions проверяет тесты, архитектуру, нативный C и сборки.",
     "PR checklist и управление pull request из Studio отсутствуют."),
    ("65", "sec-collab", "Журнал действий IDE", "planned",
     "Локальный audit trail действий редактора и расширений.",
     "Постоянный audit log UI/service пока не реализован."),
    ("66", "sec-collab", "Экспорт CODEX-66 в JSON", "implemented",
     "Экспортирует весь каталог, статусы и границы возможностей.",
     "Экспорт является документационным снимком; он не активирует функции.",
     "export_catalog"),
)

FEATURES = tuple(CodexFeature(*row) for row in _ROWS)
CATEGORY_LABELS = dict(CATEGORIES)


def validate_catalog(features: Iterable[CodexFeature] = FEATURES) -> int:
    items = tuple(features)
    ids = [item.id for item in items]
    if len(items) != 66 or ids != [f"{number:02d}" for number in range(1, 67)]:
        raise ValueError("CODEX-66 must contain ordered, unique IDs 01 through 66")
    if any(item.category not in CATEGORY_LABELS for item in items):
        raise ValueError("CODEX-66 contains an unknown category")
    if any(item.status not in STATUS_LABELS for item in items):
        raise ValueError("CODEX-66 contains an unknown maturity status")
    per_category = {key: sum(item.category == key for item in items) for key, _ in CATEGORIES}
    if set(per_category.values()) != {11}:
        raise ValueError("Each CODEX-66 category must contain exactly 11 capabilities")
    return len(items)


def search_features(
    query: str = "",
    category: str = "all",
    status: str = "all",
    features: Iterable[CodexFeature] = FEATURES,
) -> tuple[CodexFeature, ...]:
    needle = str(query or "").strip().casefold()
    result = []
    for feature in features:
        if category != "all" and feature.category != category:
            continue
        if status != "all" and feature.status != status:
            continue
        haystack = " ".join((
            feature.id, feature.title, feature.summary, feature.evidence,
            feature.category, CATEGORY_LABELS.get(feature.category, ""),
        )).casefold()
        if needle and needle not in haystack:
            continue
        result.append(feature)
    return tuple(result)


def status_counts(features: Iterable[CodexFeature] = FEATURES) -> dict[str, int]:
    counts = {key: 0 for key in STATUS_LABELS}
    for feature in features:
        counts[feature.status] += 1
    return counts


def export_payload() -> dict[str, object]:
    counts = status_counts()
    return {
        "schema": "reaper.codex66.v1",
        "product": "Reaper Studio",
        "catalogue_count": len(FEATURES),
        "status_counts": counts,
        "categories": [{"id": key, "label": label, "count": 11} for key, label in CATEGORIES],
        "features": [asdict(feature) for feature in FEATURES],
        "notice": (
            "Catalogue metadata only. Status describes evidence in the current repository; "
            "planned and partial items are not activated by export."
        ),
    }


def export_json(indent: int = 2) -> str:
    return json.dumps(export_payload(), ensure_ascii=False, indent=indent) + "\n"


validate_catalog()
