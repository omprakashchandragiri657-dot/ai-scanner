"""Shared helpers: language detection, limits, snippets, severity utils."""

from __future__ import annotations

import re

from .models import SEVERITY_ORDER

# Extensions mapped to a language family understood by the rule registry.
SUPPORTED_EXTENSIONS: dict[str, str] = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".java": "java",
}

# Rule families group TypeScript with JavaScript rules.
RULE_FAMILY = {
    "python": "python",
    "javascript": "javascript",
    "typescript": "javascript",
    "java": "java",
}

LANGUAGE_LABELS = {
    "python": "Python",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "java": "Java",
}

DEFAULT_IGNORED_DIRS = {
    ".git",
    "node_modules",
    "venv",
    ".venv",
    "__pycache__",
    "dist",
    "build",
    "target",
    ".idea",
    ".vscode",
    "coverage",
    ".cache",
}

MAX_FILE_SIZE = 2 * 1024 * 1024  # 2 MB per source file
MAX_ZIP_SIZE = 100 * 1024 * 1024  # 100 MB uploaded archive
MAX_EXTRACTED_SIZE = 500 * 1024 * 1024  # 500 MB extracted
MAX_ZIP_FILES = 10000  # maximum number of entries
MAX_COMPRESSION_RATIO = 200  # zip-bomb guard

CONTEXT_RADIUS = 2  # surrounding lines sent with a finding


def language_of(path: str) -> str | None:
    """Return the language family for a file path, or None if unsupported."""
    lowered = path.lower()
    dot = lowered.rfind(".")
    if dot == -1:
        return None
    return SUPPORTED_EXTENSIONS.get(lowered[dot:])


def rule_family(language: str) -> str:
    return RULE_FAMILY.get(language, language)


def severity_rank(severity: str) -> int:
    return SEVERITY_ORDER.get(severity.upper(), 99)


def build_context(lines: list[str], line_number: int) -> list[dict]:
    """Return 2-3 surrounding lines with the highlight flag on the finding."""
    start = max(1, line_number - CONTEXT_RADIUS)
    end = min(len(lines), line_number + CONTEXT_RADIUS)
    context = []
    for number in range(start, end + 1):
        text = lines[number - 1] if number - 1 < len(lines) else ""
        context.append(
            {"line": number, "text": text, "highlight": number == line_number}
        )
    return context


def slug_language(language: str) -> str:
    return {"python": "py", "javascript": "js", "typescript": "ts", "java": "java"}.get(
        language, "txt"
    )


_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def first_identifier(expression: str, exclude: set[str] | None = None) -> str | None:
    """Return the first plausible variable name inside an expression."""
    exclude = exclude or set()
    for match in _IDENTIFIER.finditer(expression):
        name = match.group(0)
        if name not in exclude and name.lower() not in {
            "self",
            "true",
            "false",
            "none",
            "null",
            "string",
            "str",
            "var",
        }:
            return name
    return None
