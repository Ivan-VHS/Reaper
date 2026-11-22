"""Versioned stdio Language Server Protocol adapter for Reaper Studio."""
from __future__ import annotations

import json
import re
import sys
from .language_service import BUILTINS, KEYWORDS, LanguageService, Span, _offset
from .lexer import KEYWORD_ALIASES

SEMANTIC_TOKEN_TYPES = [
    "namespace", "type", "class", "enum", "interface", "struct",
    "typeParameter", "parameter", "variable", "property", "enumMember",
    "event", "function", "method", "macro", "keyword", "modifier",
    "comment", "string", "number", "regexp", "operator", "decorator",
]
SEMANTIC_TOKEN_MODIFIERS = [
    "declaration", "readonly", "static", "deprecated", "abstract",
    "async", "modification", "documentation", "defaultLibrary",
]
_SEMANTIC_TOKEN_RE = re.compile(
    r'"(?:\\.|[^"\\])*"|#.*$|(?:\d+(?:\.\d+)?)|'
    r'(?:[A-Za-z_][A-Za-z0-9_]*|[^\W\d]\w*)|'
    r'(?:~>|::|:=|==|!=|<=|>=|\*\*|//|[+\-*/%<>=!{}()[\],.:])',
    re.UNICODE,
)
_DECLARATION_KEYWORDS = {"make", "vary", "craft", "fn", "let", "const", "функция", "процедура", "пусть", "переменная", "связать"}

HOVER = {
    "make": "Immutable binding: `make name := expression`.",
    "vary": "Mutable binding: `vary name := expression`.",
    "change": "Reassign a mutable binding: `change name := expression`.",
    "craft": "Function declaration: `craft name(parameters) { ... }`.",
    "yield": "Return a value from a function.",
    "emit": "Write a value to the program output.",
    "when": "Conditional statement; may be followed by `otherwise`.",
    "each": "Iterate over a collection.",
    "loop": "Repeat while a condition is true.",
    "~>": "Flow operator: pass the left value to the next operation.",
}

class LspServer:
    def __init__(self):
        self.service = LanguageService()
        self.notifications = []
        self.exit_requested = False

    def _notify(self, method, params):
        self.notifications.append({"jsonrpc": "2.0", "method": method, "params": params})

    def drain_notifications(self):
        pending, self.notifications = self.notifications, []
        return pending

    def _range(self, text, span: Span):
        lines = text.splitlines()
        line = lines[span.line] if span.line < len(lines) else ""
        start = len(line[:span.start].encode("utf-16-le")) // 2
        end = len(line[:span.end].encode("utf-16-le")) // 2
        return {"start": {"line": span.line, "character": start},
                "end": {"line": span.line, "character": end}}

    def _publish(self, uri):
        analysis = self.service.analyze(uri)
        diagnostics = [{
            "range": self._range(analysis.snapshot.text, item.span),
            "severity": {"error": 1, "warning": 2, "information": 3, "hint": 4}.get(item.severity, 1),
            "source": "reaper",
            "code": item.code,
            "message": item.message,
            **({"data": {"help": item.help}} if item.help else {}),
        } for item in analysis.diagnostics]
        self._notify("textDocument/publishDiagnostics", {
            "uri": uri, "version": analysis.snapshot.version, "diagnostics": diagnostics
        })

    def _word_at(self, uri, position):
        snapshot = self.service._docs[uri]
        lines = snapshot.text.splitlines()
        row = position.get("line", 0)
        if row < 0 or row >= len(lines):
            return ""
        absolute = _offset(snapshot.text, position)
        line_start = _offset(snapshot.text, {"line": row, "character": 0})
        column = max(0, absolute - line_start)
        line = lines[row]
        for match in re.finditer(r"[\wА-Яа-яЁё]+|~>|::", line):
            if match.start() <= column <= match.end():
                return match.group(0)
        previous = [m for m in re.finditer(r"[\wА-Яа-яЁё]+|~>|::", line) if m.end() <= column]
        return previous[-1].group(0) if previous else ""

    def dispatch(self, message):
        method = message.get("method")
        params = message.get("params") or {}
        request_id = message.get("id")
        result = None
        try:
            if method == "initialize":
                result = {
                    "capabilities": {
                        "textDocumentSync": {"openClose": True, "change": 2},
                        "completionProvider": {"triggerCharacters": [".", ":", "~"]},
                        "hoverProvider": True,
                        "definitionProvider": True,
                        "referencesProvider": True,
                        "renameProvider": {"prepareProvider": False},
                        "documentSymbolProvider": True,
                        "workspaceSymbolProvider": True,
                    },
                    "serverInfo": {"name": "reaper-language-server", "version": "0.2.0"},
                }
            elif method == "textDocument/didOpen":
                doc = params["textDocument"]
                uri = doc["uri"]
                self.service.open(uri, doc.get("text", ""), doc.get("version", 1))
                self._publish(uri)
            elif method == "textDocument/didChange":
                doc = params["textDocument"]
                uri = doc["uri"]
                snapshot = self.service.change(uri, doc["version"], params.get("contentChanges", []))
                if snapshot.version == doc["version"]:
                    self._publish(uri)
            elif method == "textDocument/didClose":
                uri = params["textDocument"]["uri"]
                self.service.close(uri)
                self._notify("textDocument/publishDiagnostics", {"uri": uri, "diagnostics": []})
            elif method == "textDocument/completion":
                uri = params["textDocument"]["uri"]
                prefix = self._word_at(uri, params["position"])
                result = {"isIncomplete": False, "items": self.service.completion(uri, prefix)}
            elif method == "textDocument/hover":
                uri = params["textDocument"]["uri"]
                word = self._word_at(uri, params["position"])
                description = HOVER.get(word)
                if description:
                    result = {"contents": {"kind": "markdown", "value": description}}
                elif word:
                    result = {"contents": {"kind": "markdown", "value": f"REAPER symbol `{word}`."}}
            elif method == "workspace/symbol":
                query = params.get("query", "")
                result = [{
                    "name": symbol.name,
                    "kind": 12 if symbol.kind == "function" else 13,
                    "containerName": "Reaper workspace",
                    "location": {
                        "uri": symbol.uri,
                        "range": self._range(
                            self.service._docs[symbol.uri].text, symbol.span
                        ),
                    },
                } for symbol in self.service.workspace_symbols(query)]
            elif method in {"textDocument/definition", "textDocument/references", "textDocument/rename"}:
                uri = params["textDocument"]["uri"]
                snapshot = self.service._docs[uri]
                word = self._word_at(uri, params["position"])
                if method == "textDocument/definition":
                    symbols = self.service.workspace_definitions(word)
                    result = [{
                        "uri": symbol.uri,
                        "range": self._range(
                            self.service._docs[symbol.uri].text, symbol.span
                        ),
                    } for symbol in symbols] or None
                elif method == "textDocument/references":
                    result = [{
                        "uri": target_uri,
                        "range": self._range(
                            self.service._docs[target_uri].text, span
                        ),
                    } for target_uri, span in self.service.workspace_references(word)]
                else:
                    edits = self.service.rename(uri, word, params["newName"])
                    result = {"changes": {uri: [
                        {"range": self._range(snapshot.text, span), "newText": replacement}
                        for span, replacement in edits
                    ]}}
            elif method == "textDocument/documentSymbol":
                uri = params["textDocument"]["uri"]
                analysis = self.service.result(uri) or self.service.analyze(uri)
                result = [{
                    "name": symbol.name,
                    "kind": 12 if symbol.kind == "function" else 13,
                    "range": self._range(analysis.snapshot.text, symbol.span),
                    "selectionRange": self._range(analysis.snapshot.text, symbol.span),
                } for symbol in analysis.symbols]
            elif method == "shutdown":
                self.service.shutdown()
            elif method == "exit":
                self.exit_requested = True
            elif method in {"initialized", "$/cancelRequest"}:
                return None
            elif request_id is not None:
                return {"jsonrpc": "2.0", "id": request_id,
                        "error": {"code": -32601, "message": f"Method not found: {method}"}}
        except (KeyError, IndexError, TypeError, ValueError) as error:
            if request_id is not None:
                return {"jsonrpc": "2.0", "id": request_id,
                        "error": {"code": -32602, "message": str(error)}}
            return None
        return {"jsonrpc": "2.0", "id": request_id, "result": result} if request_id is not None else None


def read_message(stream):
    headers = {}
    while True:
        line = stream.readline()
        if not line:
            return None
        if line in (b"\r\n", b"\n"):
            break
        key, _, value = line.decode("ascii").partition(":")
        headers[key.lower()] = value.strip()
    length = int(headers.get("content-length", "0"))
    if length < 0 or length > 16 * 1024 * 1024:
        raise ValueError("invalid LSP Content-Length")
    body = stream.read(length)
    return json.loads(body.decode("utf-8")) if len(body) == length else None


def write_message(stream, payload):
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    stream.write(f"Content-Length: {len(body)}\r\n\r\n".encode("ascii") + body)
    stream.flush()


def serve(stdin=None, stdout=None):
    stdin, stdout = stdin or sys.stdin.buffer, stdout or sys.stdout.buffer
    server = LspServer()
    try:
        while True:
            message = read_message(stdin)
            if message is None:
                return 0
            response = server.dispatch(message)
            for notification in server.drain_notifications():
                write_message(stdout, notification)
            if response is not None:
                write_message(stdout, response)
            if server.exit_requested:
                return 0
    finally:
        server.service.shutdown()


if __name__ == "__main__":
    raise SystemExit(serve())
