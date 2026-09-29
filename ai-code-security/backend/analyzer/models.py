"""Data models shared across the analyzer."""

from __future__ import annotations

from pydantic import BaseModel, Field

SEVERITIES = ("CRITICAL", "HIGH", "MEDIUM", "LOW")
SEVERITY_ORDER = {severity: index for index, severity in enumerate(SEVERITIES)}


class ContextLine(BaseModel):
    """A single source line shown around a finding."""

    line: int
    text: str
    highlight: bool = False


class Remediation(BaseModel):
    """Before/after example shown in the finding detail panel."""

    vulnerable: str = ""
    secure: str = ""
    explanation: str = ""


class Finding(BaseModel):
    """Normalized finding produced by the detection engine."""

    id: str
    title: str
    severity: str
    cwe: str
    confidence: int
    file: str
    line: int
    code: str
    language: str
    description: str
    evidence: str
    recommendation: str
    detector: str
    rule_id: str = ""
    flow: list[str] = Field(default_factory=list)
    context: list[ContextLine] = Field(default_factory=list)
    remediation: Remediation = Field(default_factory=Remediation)


class Summary(BaseModel):
    total: int = 0
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0


class ScanStats(BaseModel):
    files_scanned: int = 0
    lines_analyzed: int = 0
    rules_executed: int = 0
    duration_seconds: float = 0.0
    languages: dict[str, int] = Field(default_factory=dict)
    total_files: int = 0
    ignored_files: int = 0
    skipped_files: list[str] = Field(default_factory=list)


class ProjectInfo(BaseModel):
    scan_id: str = ""
    name: str = "project"
    files_found: int = 0
    source_files: int = 0
    files_scanned: int = 0
    lines_analyzed: int = 0
    by_language: dict[str, int] = Field(default_factory=dict)
    ignored: int = 0
    tree: list[dict] = Field(default_factory=list)


class ScanResult(BaseModel):
    project: ProjectInfo
    summary: Summary
    stats: ScanStats
    findings: list[Finding] = Field(default_factory=list)
    generated_at: str = ""
