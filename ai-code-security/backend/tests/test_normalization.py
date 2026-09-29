"""Tests for finding normalization, deduplication and severity summaries."""

from __future__ import annotations

from analyzer.models import Finding, Summary
from analyzer.scanner import finalize_findings, scan_source, summarize
from analyzer.utils import build_context, language_of, rule_family


def make_finding(rule_id: str, file: str, line: int, severity: str) -> Finding:
    return Finding(
        id="",
        title="T",
        severity=severity,
        cwe="CWE-0",
        confidence=50,
        file=file,
        line=line,
        code="x = 1",
        language="python",
        description="d",
        evidence="e",
        recommendation="r",
        detector="detector",
        rule_id=rule_id,
    )


def test_deduplicate_same_rule_file_line() -> None:
    findings = [
        make_finding("R1", "a.py", 3, "HIGH"),
        make_finding("R1", "a.py", 3, "HIGH"),
        make_finding("R2", "a.py", 3, "HIGH"),
    ]
    result = finalize_findings(findings)
    assert len(result) == 2


def test_ids_assigned_in_severity_order() -> None:
    findings = [
        make_finding("R1", "b.py", 10, "LOW"),
        make_finding("R2", "a.py", 5, "CRITICAL"),
        make_finding("R3", "a.py", 2, "HIGH"),
    ]
    result = finalize_findings(findings)
    assert [f.id for f in result] == ["VULN-001", "VULN-002", "VULN-003"]
    assert [f.severity for f in result] == ["CRITICAL", "HIGH", "LOW"]


def test_summary_counts() -> None:
    findings = [
        make_finding("R1", "a.py", 1, "CRITICAL"),
        make_finding("R2", "a.py", 2, "HIGH"),
        make_finding("R3", "a.py", 3, "HIGH"),
        make_finding("R4", "a.py", 4, "MEDIUM"),
        make_finding("R5", "a.py", 5, "LOW"),
    ]
    summary = summarize(findings)
    assert summary == Summary(
        total=5, critical=1, high=2, medium=1, low=1
    )


def test_empty_summary() -> None:
    assert summarize([]).total == 0


def test_language_detection() -> None:
    assert language_of("src/main.py") == "python"
    assert language_of("src/App.tsx") == "typescript"
    assert language_of("src/App.jsx") == "javascript"
    assert language_of("Main.java") == "java"
    assert language_of("README.md") is None
    assert rule_family("typescript") == "javascript"


def test_context_includes_highlight() -> None:
    lines = ["l1", "l2", "l3", "l4", "l5", "l6", "l7"]
    context = build_context(lines, 4)
    highlighted = [entry for entry in context if entry["highlight"]]
    assert [entry["line"] for entry in highlighted] == [4]
    assert len(context) == 5  # radius 2 on each side


def test_scan_source_normalizes_fields() -> None:
    code = 'query = f"SELECT * FROM t WHERE id={uid}"\ncursor.execute(query)\n'
    findings = scan_source("db.py", code)
    assert findings
    finding = findings[0]
    assert finding.detector.endswith("Rule")
    assert finding.remediation.secure, "remediation example required"
    assert finding.flow, "detection evidence flow required"
    assert finding.recommendation
