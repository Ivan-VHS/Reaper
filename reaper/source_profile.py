"""Per-source syntax and locale directives for mixed-style Reaper files.

Directive lines are replaced with same-length whitespace, so all token offsets
continue to refer to the original UTF-8-decoded source string.
"""
from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass, field

from .errors import ParseError


SUPPORTED_MODES = frozenset({"classic", "flow"})
SUPPORTED_LOCALES = frozenset({"en", "ru", "uk", "most"})


@dataclass(frozen=True, slots=True)
class SourceSpan:
    file: str
    line: int
    col: int
    start: int
    end: int


@dataclass(frozen=True, slots=True)
class SourceSegment:
    start: int
    end: int
    syntax_mode: str
    locale: str


@dataclass(frozen=True, slots=True)
class PreparedSource:
    text: str
    segments: tuple[SourceSegment, ...]
    final_mode: str = "classic"
    final_locale: str = "en"
    _starts: tuple[int, ...] = field(default=(), repr=False, compare=False)

    def __post_init__(self) -> None:
        if not self._starts and self.segments:
            object.__setattr__(self, "_starts", tuple(item.start for item in self.segments))

    def profile_at(self, offset: int) -> tuple[str, str]:
        if not self.segments:
            return self.final_mode, self.final_locale
        index = bisect_right(self._starts, max(0, offset)) - 1
        if index < 0:
            index = 0
        if index >= len(self.segments):
            return self.final_mode, self.final_locale
        segment = self.segments[index]
        if offset >= segment.end and index == len(self.segments) - 1:
            return self.final_mode, self.final_locale
        return segment.syntax_mode, segment.locale


class SourceProfileError(ParseError):
    """Invalid source directive with a precise, locale-aware source span."""

    def __init__(
        self,
        message: str,
        span: SourceSpan,
        syntax_mode: str,
        locale: str,
    ) -> None:
        super().__init__(
            f"{span.file}:{span.line}:{span.col}: {message}",
            span=span,
            syntax_mode=syntax_mode,
            locale=locale,
        )
        self.message = message


_DIRECTIVE_MESSAGES = {
    "en": {
        "unknown": "unknown source directive; use @use, @mode, or @locale",
        "empty": "@use requires mode= or locale=",
        "syntax": "invalid directive syntax",
        "duplicate": "directive key '{key}' is repeated",
        "key": "unsupported directive key '{key}'",
        "mode": "unsupported syntax mode '{value}'; expected classic or flow",
        "locale": "unsupported locale '{value}'; expected en, ru, uk, or most",
        "value": "directive value is missing",
    },
    "ru": {
        "unknown": "неизвестная директива; используйте @use, @mode или @locale",
        "empty": "для @use требуется mode= или locale=",
        "syntax": "неверный синтаксис директивы",
        "duplicate": "ключ директивы '{key}' указан повторно",
        "key": "неподдерживаемый ключ директивы '{key}'",
        "mode": "неподдерживаемый режим '{value}'; допустимы classic и flow",
        "locale": "неподдерживаемая локаль '{value}'; допустимы en, ru, uk и most",
        "value": "не указано значение директивы",
    },
    "uk": {
        "unknown": "невідома директива; використовуйте @use, @mode або @locale",
        "empty": "для @use потрібен mode= або locale=",
        "syntax": "неправильний синтаксис директиви",
        "duplicate": "ключ директиви '{key}' указано повторно",
        "key": "непідтримуваний ключ директиви '{key}'",
        "mode": "непідтримуваний режим '{value}'; дозволені classic і flow",
        "locale": "непідтримувана локаль '{value}'; дозволені en, ru, uk і most",
        "value": "не вказано значення директиви",
    },
}


def _language(locale: str) -> str:
    return "ru" if locale == "most" else locale if locale in {"ru", "uk"} else "en"


def _span(text: str, filename: str, start: int, end: int) -> SourceSpan:
    start = max(0, min(start, len(text)))
    end = max(start, min(end, len(text)))
    line = text.count("\n", 0, start) + 1
    line_start = text.rfind("\n", 0, start) + 1
    return SourceSpan(filename, line, start - line_start + 1, start, end)


def _fail(
    text: str,
    filename: str,
    line_start: int,
    body: str,
    marker_offset: int,
    mode: str,
    locale: str,
    key: str,
    **values: str,
) -> None:
    language = _language(locale)
    message = _DIRECTIVE_MESSAGES[language][key].format(**values)
    span = _span(text, filename, line_start + marker_offset, line_start + len(body))
    raise SourceProfileError(message, span, mode, locale)


def _validate(
    text: str,
    filename: str,
    line_start: int,
    body: str,
    marker_offset: int,
    mode: str,
    locale: str,
    updates: dict[str, str],
) -> tuple[str, str]:
    next_mode, next_locale = mode, locale
    for key, value in updates.items():
        normalized = value.lower()
        if key == "mode":
            if normalized not in SUPPORTED_MODES:
                _fail(text, filename, line_start, body, marker_offset, mode, locale, "mode", value=value)
            next_mode = normalized
        elif key == "locale":
            if normalized not in SUPPORTED_LOCALES:
                _fail(text, filename, line_start, body, marker_offset, mode, locale, "locale", value=value)
            next_locale = normalized
    return next_mode, next_locale


def _parse_directive(
    text: str,
    filename: str,
    line_start: int,
    body: str,
    mode: str,
    locale: str,
) -> tuple[str, str]:
    leading = len(body) - len(body.lstrip(" \t"))
    command = body[leading:].split("#", 1)[0].strip()
    if not command:
        return mode, locale

    updates: dict[str, str] = {}
    if command == "@use" or command.startswith(("@use ", "@use\t")):
        fields = command[4:].split()
        if not fields:
            _fail(text, filename, line_start, body, leading, mode, locale, "empty")
        for field in fields:
            if "=" not in field:
                _fail(text, filename, line_start, body, leading, mode, locale, "syntax")
            key, value = field.split("=", 1)
            if key not in {"mode", "locale"}:
                _fail(text, filename, line_start, body, leading, mode, locale, "key", key=key)
            if key in updates:
                _fail(text, filename, line_start, body, leading, mode, locale, "duplicate", key=key)
            if not value:
                _fail(text, filename, line_start, body, leading, mode, locale, "value")
            updates[key] = value
    elif command.startswith("@mode"):
        remainder = command[len("@mode"):].strip()
        if remainder.startswith("="):
            remainder = remainder[1:].strip()
        if not remainder or len(remainder.split()) != 1:
            _fail(text, filename, line_start, body, leading, mode, locale, "syntax")
        updates["mode"] = remainder
    elif command.startswith("@locale"):
        remainder = command[len("@locale"):].strip()
        if remainder.startswith("="):
            remainder = remainder[1:].strip()
        if not remainder or len(remainder.split()) != 1:
            _fail(text, filename, line_start, body, leading, mode, locale, "syntax")
        updates["locale"] = remainder
    else:
        _fail(text, filename, line_start, body, leading, mode, locale, "unknown")

    return _validate(
        text, filename, line_start, body, leading, mode, locale, updates
    )


def prepare_source(source: str, filename: str = "<memory>") -> PreparedSource:
    """Mask source directives without changing offsets or line endings.

    Supported forms:
      @use mode=flow locale=ru
      @use locale=uk mode=classic
      @mode flow / @mode=flow
      @locale ru / @locale=ru

    The default remains classic/en for backward compatibility.
    """
    if not source:
        return PreparedSource("", (), "classic", "en")

    output: list[str] = []
    segments: list[SourceSegment] = []
    cursor = 0
    mode, locale = "classic", "en"

    for raw_line in source.splitlines(keepends=True):
        body = raw_line.rstrip("\r\n")
        ending = raw_line[len(body):]
        leading = len(body) - len(body.lstrip(" \t"))
        candidate = body[leading:]

        if candidate.startswith("@"):
            mode, locale = _parse_directive(
                source, filename, cursor, body, mode, locale
            )
            output.append((" " * len(body)) + ending)
        else:
            output.append(raw_line)

        end = cursor + len(raw_line)
        segments.append(SourceSegment(cursor, end, mode, locale))
        cursor = end

    # splitlines(keepends=True) returns no segment for an empty trailing line,
    # but EOF still inherits the most recently selected profile.
    return PreparedSource(
        "".join(output),
        tuple(segments),
        mode,
        locale,
        tuple(item.start for item in segments),
    )




def span_from_offsets(
    text: str, filename: str, start: int, end: int
) -> SourceSpan:
    """Convert original-source half-open offsets into a line/column span."""
    return _span(text, filename, start, end)


def localize_lex_message(locale: str, message: str) -> str:
    """Localize stable lexer failures without translating source lexemes."""
    language = _language(locale)
    if language == "en":
        return message
    import re
    templates = {
        "ru": {
            "string literal cannot span lines": "строковый литерал не может занимать несколько строк",
            "unterminated string literal": "незакрытый строковый литерал",
        },
        "uk": {
            "string literal cannot span lines": "рядковий літерал не може займати кілька рядків",
            "unterminated string literal": "незакритий рядковий літерал",
        },
    }
    if message in templates[language]:
        return templates[language][message]
    patterns = {
        "ru": (
            (r"unknown escape sequence (.+)", "неизвестная escape-последовательность {0}"),
            (r"unexpected character (.+)", "неожиданный символ {0}"),
            (r"'(.+)' requires @mode flow", "оператор '{0}' доступен только в режиме @mode flow"),
            (r"source exceeds the (.+)-character limit", "исходный текст превышает ограничение в {0} символов"),
            (r"token limit \\((.+)\\) exceeded", "превышен предел количества токенов: {0}"),
        ),
        "uk": (
            (r"unknown escape sequence (.+)", "невідома escape-послідовність {0}"),
            (r"unexpected character (.+)", "неочікуваний символ {0}"),
            (r"'(.+)' requires @mode flow", "оператор '{0}' доступний лише в режимі @mode flow"),
            (r"source exceeds the (.+)-character limit", "вихідний текст перевищує обмеження у {0} символів"),
            (r"token limit \\((.+)\\) exceeded", "перевищено межу кількості токенів: {0}"),
        ),
    }
    for pattern, replacement in patterns[language]:
        match = re.fullmatch(pattern, message)
        if match:
            return replacement.format(*match.groups())
    return message

def span_for_token(token: object, filename: str = "<memory>") -> SourceSpan:
    """Return a half-open source span for a lexer/parser token."""
    start = getattr(token, "start", None)
    end = getattr(token, "end", None)
    if start is None:
        start = 0
    if end is None:
        end = start
    return SourceSpan(
        filename,
        int(getattr(token, "line", 1)),
        int(getattr(token, "column", 1)),
        int(start),
        int(end),
    )


_PARSE_MESSAGES = {
    "ru": {
        "expected an expression": "ожидалось выражение",
        "expected a new line after this statement": "ожидался перевод строки после инструкции",
        "expected ')' after arguments": "ожидалась ')' после аргументов",
        "expected ']' after list": "ожидалась ']' после списка",
        "expected ']' after index": "ожидалась ']' после индекса",
        "expected '}' after block": "ожидалась '}' после блока",
        "expected '{' to start a block": "ожидалась '{' в начале блока",
        "catalogue operator is reserved; executable semantics are not registered": "оператор зарезервирован; исполняемая семантика ещё не зарегистрирована",
    },
    "uk": {
        "expected an expression": "очікувався вираз",
        "expected a new line after this statement": "очікувався перехід рядка після інструкції",
        "expected ')' after arguments": "очікувалася ')' після аргументів",
        "expected ']' after list": "очікувалася ']' після списку",
        "expected ']' after index": "очікувалася ']' після індексу",
        "expected '}' after block": "очікувалася '}' після блоку",
        "expected '{' to start a block": "очікувалася '{' на початку блоку",
        "catalogue operator is reserved; executable semantics are not registered": "оператор зарезервовано; виконувану семантику ще не зареєстровано",
    },
}



_PARSE_MESSAGES["ru"].update({
    "flow step requires a preceding expression": "шаг потока требует предшествующего выражения",
    "expected a quoted .rpr path after 'import'": "ожидался путь к файлу .rpr в кавычках после 'import'",
    "expected an import alias after 'as'": "ожидался псевдоним импорта после 'as'",
    "inline export must declare a name or craft": "встроенный export должен объявлять имя или функцию craft",
    "expected a name after 'export'": "ожидалось имя после 'export'",
    "expected a name after declaration": "ожидалось имя после объявления",
    "expected ':=' after the name": "ожидался оператор ':=' после имени",
    "expected a mutable name after 'change'": "после 'change' ожидалось имя изменяемой переменной",
    "expected a function name after 'craft'": "после 'craft' ожидалось имя функции",
    "expected '(' after function name": "после имени функции ожидалась '('",
    "expected a parameter name": "ожидалось имя параметра",
    "expected ')' after parameters": "после параметров ожидалась ')'",
    "expected 'while' after 'loop'": "после 'loop' ожидалось 'while'",
    "expected an iteration variable after 'each'": "после 'each' ожидалось имя переменной цикла",
    "expected 'in' after iteration variable": "после переменной цикла ожидалось 'in'",
    "expected ')' after expression": "после выражения ожидалась ')'",
})
_PARSE_MESSAGES["uk"].update({
    "flow step requires a preceding expression": "крок потоку потребує попереднього виразу",
    "expected a quoted .rpr path after 'import'": "після 'import' очікувався шлях до файлу .rpr у лапках",
    "expected an import alias after 'as'": "після 'as' очікувався псевдонім імпорту",
    "inline export must declare a name or craft": "вбудований export має оголошувати ім'я або функцію craft",
    "expected a name after 'export'": "після 'export' очікувалося ім'я",
    "expected a name after declaration": "після оголошення очікувалося ім'я",
    "expected ':=' after the name": "після імені очікувався оператор ':='",
    "expected a mutable name after 'change'": "після 'change' очікувалося ім'я змінної",
    "expected a function name after 'craft'": "після 'craft' очікувалося ім'я функції",
    "expected '(' after function name": "після імені функції очікувалася '('",
    "expected a parameter name": "очікувалося ім'я параметра",
    "expected ')' after parameters": "після параметрів очікувалася ')'",
    "expected 'while' after 'loop'": "після 'loop' очікувалося 'while'",
    "expected an iteration variable after 'each'": "після 'each' очікувалося ім'я змінної циклу",
    "expected 'in' after iteration variable": "після змінної циклу очікувалося 'in'",
    "expected ')' after expression": "після виразу очікувалася ')'",
})


def localize_parse_message(locale: str, message: str) -> str:
    """Translate stable parser diagnostics while retaining unknown detail verbatim."""
    language = _language(locale)
    if language == "en":
        return message
    known = _PARSE_MESSAGES[language].get(message)
    if known:
        return known
    if message.startswith("expected "):
        prefix = "ожидалось: " if language == "ru" else "очікувалося: "
        return prefix + message[len("expected "):]
    if message.startswith("unexpected "):
        prefix = "неожиданный элемент: " if language == "ru" else "неочікуваний елемент: "
        return prefix + message[len("unexpected "):]
    return message


def span_for_node(node: object, filename: str = "<memory>") -> SourceSpan:
    """Return the complete half-open source range of an AST node.

    Parser nodes expose token, optional end_token and children. Duck typing
    avoids a source_profile -> parser import cycle and also supports compatible
    tooling ASTs.
    """
    candidates: list[object] = []

    def visit(current: object) -> None:
        start_token = getattr(current, "start_token", None)
        if start_token is not None:
            candidates.append(start_token)
        token = getattr(current, "token", None)
        if token is not None:
            candidates.append(token)
        end_token = getattr(current, "end_token", None)
        if end_token is not None:
            candidates.append(end_token)
        for child in getattr(current, "children", None) or ():
            if child is not None:
                visit(child)

    visit(node)
    if not candidates:
        return SourceSpan(filename, 1, 1, 0, 0)

    positioned = [
        token for token in candidates
        if getattr(token, "start", None) is not None
    ]
    if not positioned:
        return span_for_token(candidates[0], filename)

    first = min(positioned, key=lambda item: int(getattr(item, "start")))
    start = min(int(getattr(item, "start")) for item in positioned)
    ends = [
        int(getattr(item, "end")) for item in positioned
        if getattr(item, "end", None) is not None
    ]
    end = max(ends, default=start)
    return SourceSpan(
        filename,
        int(getattr(first, "line", 1)),
        int(getattr(first, "column", 1)),
        start,
        max(start, end),
    )


def localize_type_message(locale: str, code: str, message: str) -> str:
    """Localize the current conservative type-checker diagnostic catalogue.

    Type names, identifiers, operators and arity values remain canonical so
    messages can be compared across locales and consumed by editor tooling.
    """
    language = _language(locale)
    if language == "en":
        return message

    import re

    patterns = {
        "ru": {
            "RPR-T0001": (
                r"cannot assign (.+) to '(.+)' declared as (.+)",
                "нельзя присвоить значение типа {0} переменной '{1}', объявленной как {2}",
            ),
            "RPR-T0002": (
                r"'(.+)' is immutable and cannot be reassigned",
                "'{0}' неизменяема и не может быть переназначена",
            ),
            "RPR-T0003": (
                r"sequence index must be Int, not (.+)",
                "индекс последовательности должен иметь тип Int, а не {0}",
            ),
            "RPR-T0004-unary": (
                r"unary '-' requires a number, not (.+)",
                "унарный '-' требует число, получен тип {0}",
            ),
            "RPR-T0004-binary": (
                r"operator '(.+)' requires numeric operands, got (.+) and (.+)",
                "оператор '{0}' требует числовые операнды, получены {1} и {2}",
            ),
            "RPR-T0005": (
                r"operator '(.+)' requires Text operands, got (.+) and (.+)",
                "оператор '{0}' требует операнды Text, получены {1} и {2}",
            ),
            "RPR-T0006": (
                r"operator '(.+)' cannot compare (.+) with (.+)",
                "оператор '{0}' не может сравнивать типы {1} и {2}",
            ),
            "RPR-T0007": (
                r"(.+?)\(\) expects (.+) arguments, got (.+)",
                "вызов {0}() ожидает аргументы: {1}; получено: {2}",
            ),
            "RPR-T0008-collection": (
                r"(.+?)\(\) expects a collection or Text, got (.+)",
                "вызов {0}() ожидает коллекцию или Text, получен тип {1}",
            ),
            "RPR-T0008-index": (
                r"cannot index a value of type (.+)",
                "нельзя индексировать значение типа {0}",
            ),
            "RPR-T0008-iterate": (
                r"cannot iterate or index a value of type (.+)",
                "нельзя перебирать или индексировать значение типа {0}",
            ),
            "RPR-T0009": (
                r"(.+?)\(\) expects Int arguments, got (.+)",
                "вызов {0}() ожидает аргументы Int, получен тип {1}",
            ),
        },
        "uk": {
            "RPR-T0001": (
                r"cannot assign (.+) to '(.+)' declared as (.+)",
                "не можна присвоїти значення типу {0} змінній '{1}', оголошеній як {2}",
            ),
            "RPR-T0002": (
                r"'(.+)' is immutable and cannot be reassigned",
                "'{0}' незмінна й не може бути перепризначена",
            ),
            "RPR-T0003": (
                r"sequence index must be Int, not (.+)",
                "індекс послідовності повинен мати тип Int, а не {0}",
            ),
            "RPR-T0004-unary": (
                r"unary '-' requires a number, not (.+)",
                "унарний '-' потребує число, отримано тип {0}",
            ),
            "RPR-T0004-binary": (
                r"operator '(.+)' requires numeric operands, got (.+) and (.+)",
                "оператор '{0}' потребує числові операнди, отримано {1} і {2}",
            ),
            "RPR-T0005": (
                r"operator '(.+)' requires Text operands, got (.+) and (.+)",
                "оператор '{0}' потребує операнди Text, отримано {1} і {2}",
            ),
            "RPR-T0006": (
                r"operator '(.+)' cannot compare (.+) with (.+)",
                "оператор '{0}' не може порівнювати типи {1} і {2}",
            ),
            "RPR-T0007": (
                r"(.+?)\(\) expects (.+) arguments, got (.+)",
                "виклик {0}() очікує аргументи: {1}; отримано: {2}",
            ),
            "RPR-T0008-collection": (
                r"(.+?)\(\) expects a collection or Text, got (.+)",
                "виклик {0}() очікує колекцію або Text, отримано тип {1}",
            ),
            "RPR-T0008-index": (
                r"cannot index a value of type (.+)",
                "не можна індексувати значення типу {0}",
            ),
            "RPR-T0008-iterate": (
                r"cannot iterate or index a value of type (.+)",
                "не можна перебирати або індексувати значення типу {0}",
            ),
            "RPR-T0009": (
                r"(.+?)\(\) expects Int arguments, got (.+)",
                "виклик {0}() очікує аргументи Int, отримано тип {1}",
            ),
        },
    }
    candidates = [code]
    if code == "RPR-T0004":
        candidates = ["RPR-T0004-unary", "RPR-T0004-binary"]
    elif code == "RPR-T0008":
        candidates = ["RPR-T0008-collection", "RPR-T0008-index", "RPR-T0008-iterate"]
    for candidate in candidates:
        definition = patterns[language].get(candidate)
        if definition is None:
            continue
        match = re.fullmatch(definition[0], message)
        if match:
            return definition[1].format(*match.groups())
    return message
