"""Single-file scanning: run rules, normalize, deduplicate findings."""

from __future__ import annotations

from .engine import rules_for
from .models import (
    ContextLine,
    Finding,
    Remediation,
    SEVERITY_ORDER,
    Summary,
)
from .utils import build_context, language_of, rule_family

# Human-friendly titles shown in the UI (spec section 16).
TITLE_OVERRIDES = {
    "PY-SQLI": "SQL Injection",
    "JAVA-SQLI": "SQL Injection",
    "PY-CMDI": "Command Injection",
    "JS-CMDI": "Command Injection",
    "JAVA-CMDI": "Command Injection",
    "PY-EVAL": "Code Injection",
    "JS-EVAL": "Code Injection",
    "PY-DESER": "Insecure Deserialization",
    "JAVA-DESER": "Insecure Deserialization",
    "PY-SECRETS": "Hardcoded Credentials",
    "JS-SECRETS": "Hardcoded Credentials",
    "JAVA-SECRETS": "Hardcoded Credentials",
    "PY-PATH": "Path Traversal",
    "JS-XSS": "Cross-Site Scripting",
    "PY-WEAKHASH": "Weak Cryptography",
    "PY-DEBUG": "Debug Mode Enabled",
    "PY-TLS": "Disabled TLS Verification",
    "PY-WEAKRNG": "Weak Random Token",
    "PY-HTTP": "Cleartext HTTP",
    "JS-HTTP": "Cleartext HTTP",
}


def _title_for(rule_id: str, rule_name: str) -> str:
    if rule_id in TITLE_OVERRIDES:
        return TITLE_OVERRIDES[rule_id]
    if rule_name.endswith(" Rule"):
        return rule_name[: -len(" Rule")]
    return rule_name


def scan_source(path: str, code: str) -> list[Finding]:
    """Run every applicable rule against one source file."""
    language = language_of(path)
    if language is None:
        return []

    rules = rules_for(rule_family(language))
    lines = code.splitlines()
    findings: list[Finding] = []
    seen: set[tuple[str, int]] = set()

    for rule in rules:
        try:
            matches = rule.detect(code, path)
        except Exception:
            # A single broken rule must never abort a project scan.
            continue
        for match in matches:
            key = (rule.id, match.line)
            if key in seen:
                continue
            seen.add(key)
            findings.append(
                Finding(
                    id="",  # assigned globally after deduplication
                    title=_title_for(rule.id, rule.name),
                    severity=rule.severity,
                    cwe=rule.cwe,
                    confidence=match.confidence or rule.confidence,
                    file=path,
                    line=match.line,
                    code=match.code,
                    language=language,
                    description=match.description or rule.description,
                    evidence=match.evidence or rule.description,
                    recommendation=rule.recommendation,
                    detector=rule.name,
                    rule_id=rule.id,
                    flow=list(match.flow or rule.flow),
                    context=[
                        ContextLine(**entry)
                        for entry in build_context(lines, match.line)
                    ],
                    remediation=Remediation(
                        vulnerable=rule.fix_vulnerable,
                        secure=rule.fix_secure,
                        explanation=rule.fix_explanation,
                    ),
                )
            )
    return findings


def finalize_findings(findings: list[Finding]) -> list[Finding]:
    """Deduplicate (rule + file + line), sort and assign VULN-nnn ids."""
    deduped: dict[tuple[str, str, int], Finding] = {}
    for finding in findings:
        key = (finding.rule_id or finding.detector, finding.file, finding.line)
        current = deduped.get(key)
        if current is None or finding.confidence > current.confidence:
            deduped[key] = finding

    ordered = sorted(
        deduped.values(),
        key=lambda f: (
            SEVERITY_ORDER.get(f.severity, 99),
            f.file.lower(),
            f.line,
        ),
    )
    for index, finding in enumerate(ordered, start=1):
        finding.id = f"VULN-{index:03d}"
    return ordered


def summarize(findings: list[Finding]) -> Summary:
    """Count findings per severity."""
    summary = Summary(total=len(findings))
    for finding in findings:
        if finding.severity == "CRITICAL":
            summary.critical += 1
        elif finding.severity == "HIGH":
            summary.high += 1
        elif finding.severity == "MEDIUM":
            summary.medium += 1
        elif finding.severity == "LOW":
            summary.low += 1
    return summary
