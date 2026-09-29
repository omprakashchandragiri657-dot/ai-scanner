"""Project-level scanning: safe ZIP extraction, traversal and orchestration."""

from __future__ import annotations

import io
import os
import re
import shutil
import stat
import time
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Iterator

from .models import Finding, ProjectInfo, ScanResult, ScanStats
from .scanner import finalize_findings, scan_source, summarize
from .utils import (
    DEFAULT_IGNORED_DIRS,
    MAX_EXTRACTED_SIZE,
    MAX_FILE_SIZE,
    MAX_ZIP_FILES,
    MAX_ZIP_SIZE,
    MAX_COMPRESSION_RATIO,
    language_of,
)


class ZipSecurityError(Exception):
    """Raised when an archive fails a security validation check."""


def _is_ignored_entry(name: str) -> bool:
    """True when any path segment of the entry is an ignored folder/file."""
    return any(
        part.lower() in DEFAULT_IGNORED_DIRS for part in PurePosixPath(name).parts
    )


def safe_extract(zip_bytes: bytes, dest: Path) -> dict:
    """Validate and extract a ZIP archive inside ``dest`` only.

    Every entry is validated for path safety, but entries inside ignored
    directories (node_modules, .git, venv, dist, ...) are never extracted and
    never counted toward the entry/size limits -- they are never scanned.
    Typical project archives therefore no longer trip the entry cap.

    Returns ``{"ignored_entries": <number of skipped entries>}``.
    """
    if not zip_bytes:
        raise ZipSecurityError("The uploaded file is empty.")
    if len(zip_bytes) > MAX_ZIP_SIZE:
        limit_mb = MAX_ZIP_SIZE // (1024 * 1024)
        raise ZipSecurityError(f"ZIP exceeds the maximum size of {limit_mb} MB.")
    if not zip_bytes.startswith(b"PK"):
        raise ZipSecurityError("Invalid file: expected a ZIP archive (project.zip).")

    try:
        archive = zipfile.ZipFile(io.BytesIO(zip_bytes))
    except zipfile.BadZipFile as exc:
        raise ZipSecurityError(
            "The archive is corrupted or not a valid ZIP file."
        ) from exc

    dest = dest.resolve()
    dest.mkdir(parents=True, exist_ok=True)

    kept_entries = 0
    ignored_entries = 0
    total_uncompressed = 0

    with archive:
        infos = archive.infolist()

        # Pass 1: validate every entry; apply limits only to kept entries.
        for info in infos:
            mode = info.external_attr >> 16
            if stat.S_ISLNK(mode):
                continue  # ignore symbolic links

            name = info.filename
            if not name:
                continue
            # Zip Slip / absolute path / drive-letter protection (all entries).
            if (
                name.startswith(("/", "\\"))
                or re.match(r"^[A-Za-z]:", name)
                or ".." in Path(name).parts
            ):
                raise ZipSecurityError(f"Unsafe path rejected by archive scan: {name}")

            if _is_ignored_entry(name):
                if not (info.is_dir() or name.endswith("/")):
                    ignored_entries += 1
                continue

            kept_entries += 1
            if kept_entries > MAX_ZIP_FILES:
                raise ZipSecurityError(
                    f"Archive contains too many entries (limit: {MAX_ZIP_FILES} files). "
                    "Exclude folders like node_modules, .git, venv or dist before zipping."
                )

            if info.is_dir() or name.endswith("/"):
                continue

            if info.file_size and info.compress_size:
                ratio = info.file_size / info.compress_size
                if ratio > MAX_COMPRESSION_RATIO and info.file_size > 1024 * 1024:
                    raise ZipSecurityError(
                        "Suspicious compression ratio detected (possible ZIP bomb)."
                    )
            total_uncompressed += info.file_size
            if total_uncompressed > MAX_EXTRACTED_SIZE:
                limit_mb = MAX_EXTRACTED_SIZE // (1024 * 1024)
                raise ZipSecurityError(
                    f"Extracted size exceeds the maximum of {limit_mb} MB."
                )

        # Pass 2: extract kept entries only.
        for info in infos:
            mode = info.external_attr >> 16
            if stat.S_ISLNK(mode):
                continue
            name = info.filename
            if not name:
                continue
            if _is_ignored_entry(name):
                continue
            target = (dest / name).resolve()
            if not str(target).startswith(str(dest) + os.sep) and target != dest:
                raise ZipSecurityError(
                    f"Unsafe path rejected during extraction: {name}"
                )
            if info.is_dir() or name.endswith("/"):
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(info) as source, open(target, "wb") as out:
                shutil.copyfileobj(source, out)

    return {"ignored_entries": ignored_entries}


def resolve_project_root(dest: Path) -> tuple[Path, str]:
    """Use the single top-level directory as project root when present."""
    entries = [entry for entry in dest.iterdir() if not entry.name.startswith(".")]
    if len(entries) == 1 and entries[0].is_dir():
        return entries[0], entries[0].name
    return dest, dest.name


def _iter_files(root: Path) -> Iterator[Path]:
    """Yield every file, pruning configurable ignored directories."""
    for current, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d.lower() not in DEFAULT_IGNORED_DIRS)
        for filename in sorted(files):
            yield Path(current) / filename


def _count_ignored(root: Path) -> int:
    """Count files that live inside ignored directories."""
    count = 0
    for current, dirs, files in os.walk(root):
        for directory in list(dirs):
            if directory.lower() in DEFAULT_IGNORED_DIRS:
                ignored_path = Path(current) / directory
                count += sum(1 for entry in ignored_path.rglob("*") if entry.is_file())
                dirs.remove(directory)
    return count


def build_tree(root: Path) -> list[dict]:
    """Build a nested file tree (ignored directories excluded)."""
    nodes: dict[str, dict] = {"": {"children": []}}
    root = root.resolve()

    def ensure_dir(rel: str) -> dict:
        if rel not in nodes:
            parent_rel = Path(rel).parent.as_posix() if rel else ""
            if parent_rel == ".":
                parent_rel = ""
            parent = ensure_dir(parent_rel)
            node = {
                "name": Path(rel).name,
                "path": rel,
                "type": "dir",
                "children": [],
            }
            nodes[rel] = node
            parent["children"].append(node)
        return nodes[rel]

    for file_path in _iter_files(root):
        relative = file_path.relative_to(root).as_posix()
        parent_rel = Path(relative).parent.as_posix()
        if parent_rel == ".":
            parent_rel = ""
        parent = ensure_dir(parent_rel)
        language = language_of(relative)
        parent["children"].append(
            {
                "name": file_path.name,
                "path": relative,
                "type": "file",
                "source": language is not None,
                "language": language,
                "findings": 0,
                "max_severity": None,
            }
        )

    def sort_children(node: dict) -> None:
        node["children"].sort(
            key=lambda child: (0 if child["type"] == "dir" else 1, child["name"].lower())
        )
        for child in node["children"]:
            if child["type"] == "dir":
                sort_children(child)

    tree = nodes[""]["children"]
    sort_children({"children": tree})
    return tree


def analyze_structure(
    root: Path, name: str, ignored_entries: int | None = None
) -> dict:
    """Count files/languages and build the explorer tree.

    ``ignored_entries`` supplies the count of archive entries that were
    skipped during extraction (they never exist on disk).
    """
    total = 0
    source = 0
    by_language: dict[str, int] = {}

    for file_path in _iter_files(root):
        total += 1
        language = language_of(file_path.name)
        if language:
            source += 1
            by_language[language] = by_language.get(language, 0) + 1

    ignored = (
        ignored_entries if ignored_entries is not None else _count_ignored(root)
    )
    return {
        "name": name,
        "files_found": total + ignored,
        "source_files": source,
        "by_language": by_language,
        "ignored": ignored,
        "tree": build_tree(root),
    }


def _annotate_tree(tree: list[dict], findings: list[Finding]) -> None:
    """Attach finding counts and worst severity to tree file nodes."""
    from .models import SEVERITY_ORDER

    counts: dict[str, tuple[int, str]] = {}
    for finding in findings:
        current = counts.get(finding.file)
        if current is None or SEVERITY_ORDER.get(finding.severity, 99) < SEVERITY_ORDER.get(
            current[1], 99
        ):
            counts[finding.file] = (1, finding.severity)
        else:
            counts[finding.file] = (current[0] + 1, current[1])

    def walk(nodes: list[dict]) -> None:
        for node in nodes:
            if node["type"] == "file":
                entry = counts.get(node["path"])
                if entry:
                    node["findings"] = entry[0]
                    node["max_severity"] = entry[1]
            else:
                walk(node["children"])

    walk(tree)


def iter_scan_events(
    root: Path,
    name: str,
    scan_id: str,
    extracted: bool = True,
    ignored_entries: int | None = None,
) -> Iterator[dict]:
    """Yield NDJSON-ready events while scanning a real project directory.

    Events are produced from the actual files being processed — nothing is faked.
    """
    started = time.perf_counter()

    if extracted:
        yield {"type": "step", "label": "Project extracted"}

    structure = analyze_structure(root, name, ignored_entries=ignored_entries)
    yield {"type": "step", "label": "Project structure analyzed"}
    yield {"type": "structure", "structure": structure}

    by_language = structure["by_language"]
    labels = {
        "python": "Python files discovered",
        "javascript": "JavaScript files discovered",
        "typescript": "TypeScript files discovered",
        "java": "Java files discovered",
    }
    for language in ("python", "javascript", "typescript", "java"):
        if by_language.get(language):
            yield {"type": "step", "label": f"{labels[language]} ({by_language[language]})"}

    from .engine import all_rules

    rules_loaded = len(all_rules())
    yield {"type": "step", "label": f"Security rules loaded ({rules_loaded})"}

    # Collect the source files that will actually be scanned.
    targets: list[Path] = []
    skipped: list[str] = []
    for file_path in _iter_files(root):
        if language_of(file_path.name) is None:
            continue
        try:
            if file_path.stat().st_size > MAX_FILE_SIZE:
                skipped.append(file_path.relative_to(root).as_posix())
                continue
        except OSError:
            continue
        targets.append(file_path)

    total = len(targets)
    findings: list[Finding] = []
    lines_analyzed = 0
    languages: dict[str, int] = {}

    for index, file_path in enumerate(targets, start=1):
        relative = file_path.relative_to(root).as_posix()
        try:
            code = file_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        lines_analyzed += len(code.splitlines())
        language = language_of(relative)
        if language:
            languages[language] = languages.get(language, 0) + 1
        findings.extend(scan_source(relative, code))
        yield {
            "type": "progress",
            "file": relative,
            "index": index,
            "total": total,
            "percent": round(index / total * 100) if total else 100,
        }

    yield {"type": "step", "label": "Checking security patterns..."}

    findings = finalize_findings(findings)
    _annotate_tree(structure["tree"], findings)

    duration = round(time.perf_counter() - started, 2)
    project = ProjectInfo(
        scan_id=scan_id,
        name=structure["name"],
        files_found=structure["files_found"],
        source_files=structure["source_files"],
        files_scanned=total,
        lines_analyzed=lines_analyzed,
        by_language=structure["by_language"],
        ignored=structure["ignored"],
        tree=structure["tree"],
    )
    stats = ScanStats(
        files_scanned=total,
        lines_analyzed=lines_analyzed,
        rules_executed=rules_loaded,
        duration_seconds=duration,
        languages=languages,
        total_files=structure["files_found"],
        ignored_files=structure["ignored"],
        skipped_files=skipped,
    )
    result = ScanResult(
        project=project,
        summary=summarize(findings),
        stats=stats,
        findings=findings,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )
    yield {"type": "result", "result": result.model_dump()}


def run_scan(
    root: Path,
    name: str,
    scan_id: str,
    extracted: bool = True,
    ignored_entries: int | None = None,
) -> dict:
    """Consume the event stream and return only the final result."""
    final: dict = {}
    for event in iter_scan_events(
        root,
        name,
        scan_id,
        extracted=extracted,
        ignored_entries=ignored_entries,
    ):
        if event["type"] == "result":
            final = event["result"]
    return final


def new_scan_id() -> str:
    return uuid.uuid4().hex[:12]


