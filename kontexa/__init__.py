"""Kontexa — context-preserving translation workspace."""

__version__ = "0.1.0"

from .engine import MAX_DOCUMENT_CHARS, analyze_document, translate_document

__all__ = ["MAX_DOCUMENT_CHARS", "analyze_document", "translate_document", "__version__"]
