"""Modular detection engine: rule base class and rule registry.

The engine is intentionally generic so additional detectors (Semgrep, CodeQL,
LLM analysis, taint analysis, ...) can be registered later without touching
the scanner or the API layer.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RuleMatch:
    """A single raw match produced by a rule before normalization."""

    line: int
    code: str
    description: str | None = None
    evidence: str | None = None
    flow: list[str] | None = None
    confidence: int | None = None
    title: str | None = None
    extras: dict = field(default_factory=dict)


class SecurityRule:
    """Base class for every detection rule."""

    id = ""
    name = ""
    description = ""
    cwe = ""
    severity = ""
    confidence = 85
    language = ""
    recommendation = ""
    fix_vulnerable = ""
    fix_secure = ""
    fix_explanation = ""
    flow: list[str] = []

    def detect(self, code: str, file_path: str) -> list[RuleMatch]:
        """Return every match of this rule inside ``code``."""
        return []

    def manifest(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "cwe": self.cwe,
            "severity": self.severity,
            "confidence": self.confidence,
            "language": self.language,
        }


# Imported here (after SecurityRule/RuleMatch exist) to avoid circular imports.
from .rules.java_rules import JAVA_RULES  # noqa: E402
from .rules.javascript_rules import JAVASCRIPT_RULES  # noqa: E402
from .rules.python_rules import PYTHON_RULES  # noqa: E402

_REGISTRY: dict[str, list[SecurityRule]] = {
    "python": [rule() for rule in PYTHON_RULES],
    "javascript": [rule() for rule in JAVASCRIPT_RULES],
    "java": [rule() for rule in JAVA_RULES],
}


def rules_for(language: str) -> list[SecurityRule]:
    """Return the rule instances that apply to a language family."""
    return list(_REGISTRY.get(language, []))


def all_rules() -> list[SecurityRule]:
    """Return every registered rule instance."""
    return [rule for rules in _REGISTRY.values() for rule in rules]


def rule_manifest() -> list[dict]:
    """Serializable description of every rule (used by GET /api/rules)."""
    return [rule.manifest() for rule in all_rules()]
