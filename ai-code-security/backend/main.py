"""AI Code Security Analyzer — FastAPI application.

Static source-code analysis only: uploaded projects are extracted, read and
analyzed, never executed.
"""

from __future__ import annotations

import io
import json
import re
import shutil
import zipfile
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from analyzer.engine import rule_manifest
from analyzer.project_scanner import (
    ZipSecurityError,
    analyze_structure,
    iter_scan_events,
    new_scan_id,
    resolve_project_root,
    run_scan,
    safe_extract,
)
from analyzer.scanner import finalize_findings, scan_source, summarize
from analyzer.utils import MAX_ZIP_SIZE, rule_family  # noqa: F401  (kept for clarity)

BASE_DIR = Path(__file__).resolve().parent
UPLOADS_DIR = BASE_DIR / "uploads"
DEMO_DIR = BASE_DIR / "demo_project"
DEMO_NAME = "FairShare"

SUPPORTED_LANGUAGE_EXTS = {
    "python": "py",
    "javascript": "js",
    "typescript": "ts",
    "java": "java",
}

app = FastAPI(
    title="AI Code Security Analyzer",
    description="Detecting security vulnerabilities in AI-generated software.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory scan index; results also persist to uploads/<scan_id>/result.json
SCANS: dict[str, dict] = {}


def _persist(scan_id: str, result: dict, root: Path | None = None) -> None:
    scan_dir = UPLOADS_DIR / scan_id
    scan_dir.mkdir(parents=True, exist_ok=True)
    (scan_dir / "result.json").write_text(
        json.dumps(result, ensure_ascii=False), encoding="utf-8"
    )
    if root is not None:
        try:
            relative_root = root.relative_to(scan_dir / "project").as_posix()
        except ValueError:
            relative_root = "."
        (scan_dir / "root.txt").write_text(relative_root, encoding="utf-8")


def _load_existing_scans() -> None:
    if not UPLOADS_DIR.exists():
        return
    for scan_dir in UPLOADS_DIR.iterdir():
        result_file = scan_dir / "result.json"
        if result_file.is_file():
            try:
                SCANS[scan_dir.name] = json.loads(
                    result_file.read_text(encoding="utf-8")
                )
            except (json.JSONDecodeError, OSError):
                continue


_load_existing_scans()


def _demo_zip() -> bytes:
    """Bundle the built-in demo project as an in-memory ZIP."""
    if not DEMO_DIR.is_dir():
        raise HTTPException(status_code=404, detail="Demo project is not available.")
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(DEMO_DIR.rglob("*")):
            if path.is_file():
                archive.write(path, f"{DEMO_NAME}/{path.relative_to(DEMO_DIR).as_posix()}")
    return buffer.getvalue()


@app.get("/api/health")
def health() -> dict:
    return {
        "status": "ok",
        "service": "AI Code Security Analyzer",
        "version": "0.1.0",
        "mode": "static-analysis",
    }


@app.get("/api/rules")
def rules() -> dict:
    manifest = rule_manifest()
    return {"count": len(manifest), "rules": manifest}


@app.post("/api/projects/scan")
async def scan_project(
    file: UploadFile | None = File(None),
    demo: str | None = Form(None),
    stream: bool = Query(False),
):
    """Scan an uploaded project ZIP (or the built-in demo project).

    With ``stream=true`` the response is NDJSON: structure, per-file progress
    and the final result are emitted as they happen.
    """
    scan_id = new_scan_id()
    workdir = UPLOADS_DIR / scan_id
    zip_bytes: bytes
    original_name: str

    try:
        if demo and demo.lower() in {"1", "true", "yes"}:
            zip_bytes = _demo_zip()
            original_name = f"{DEMO_NAME}.zip"
        else:
            if file is None:
                raise HTTPException(
                    status_code=400,
                    detail="No project file uploaded. Upload project.zip or run the demo project.",
                )
            zip_bytes = await file.read()
            original_name = file.filename or "project.zip"
            if not zip_bytes:
                raise HTTPException(status_code=400, detail="The uploaded file is empty.")
            if len(zip_bytes) > MAX_ZIP_SIZE:
                limit_mb = MAX_ZIP_SIZE // (1024 * 1024)
                raise HTTPException(
                    status_code=400,
                    detail=f"ZIP exceeds the maximum size of {limit_mb} MB.",
                )

        workdir.mkdir(parents=True, exist_ok=True)
        project_dir = workdir / "project"
        extract_stats = safe_extract(zip_bytes, project_dir)
        ignored_entries = int(extract_stats.get("ignored_entries", 0))
        root, name = resolve_project_root(project_dir)
        if name == "project":
            stem = Path(original_name).stem.strip()
            name = stem or "project"
        structure = analyze_structure(root, name, ignored_entries=ignored_entries)
        if structure["files_found"] == 0:
            raise HTTPException(status_code=400, detail="The archive is empty.")
        if structure["source_files"] == 0:
            raise HTTPException(
                status_code=400,
                detail=(
                    "No supported source files found. Supported types: "
                    ".py, .js, .jsx, .ts, .tsx, .java"
                ),
            )
    except ZipSecurityError as exc:
        shutil.rmtree(workdir, ignore_errors=True)
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not stream:
        try:
            result = run_scan(
                root,
                name,
                scan_id,
                extracted=True,
                ignored_entries=ignored_entries,
            )
        except Exception as exc:  # pragma: no cover - defensive
            shutil.rmtree(workdir, ignore_errors=True)
            raise HTTPException(
                status_code=500, detail=f"Scan failed: {exc}"
            ) from exc
        _persist(scan_id, result, root=root)
        SCANS[scan_id] = result
        return result

    def generate():
        try:
            for event in iter_scan_events(
                root,
                name,
                scan_id,
                extracted=True,
                ignored_entries=ignored_entries,
            ):
                if event["type"] == "result":
                    _persist(scan_id, event["result"], root=root)
                    SCANS[scan_id] = event["result"]
                yield json.dumps(event, ensure_ascii=False) + "\n"
        except Exception as exc:  # pragma: no cover - defensive
            error = {"type": "error", "message": f"Scan failed: {exc}"}
            yield json.dumps(error, ensure_ascii=False) + "\n"

    return StreamingResponse(
        generate(),
        media_type="application/x-ndjson",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/api/demo/project")
def demo_project() -> dict:
    """Return the structure of the built-in demo project (not yet scanned)."""
    if not DEMO_DIR.is_dir():
        raise HTTPException(status_code=404, detail="Demo project is not available.")
    structure = analyze_structure(DEMO_DIR, DEMO_NAME)
    return {
        "name": DEMO_NAME,
        "note": "Demo project contains intentionally vulnerable code for security testing.",
        **structure,
    }


class CodePayload(BaseModel):
    code: str
    language: str | None = None


@app.post("/api/code/analyze")
def analyze_code(payload: CodePayload) -> dict:
    """Analyze a pasted code snippet (secondary feature)."""
    if not payload.code.strip():
        raise HTTPException(status_code=400, detail="No code provided.")
    if len(payload.code) > 512 * 1024:
        raise HTTPException(status_code=400, detail="Code snippet too large (max 512 KB).")

    language = (payload.language or "python").lower()
    if language not in SUPPORTED_LANGUAGE_EXTS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported language. Use python, javascript, typescript or java.",
        )
    path = f"snippet.{SUPPORTED_LANGUAGE_EXTS[language]}"
    findings = finalize_findings(scan_source(path, payload.code))
    return {
        "language": language,
        "findings": [finding.model_dump() for finding in findings],
        "summary": summarize(findings).model_dump(),
    }


@app.get("/api/projects/{scan_id}/file")
def get_project_file(scan_id: str, path: str) -> dict:
    """Return one source file of a previous scan (for the file explorer)."""
    if not re.fullmatch(r"[0-9a-f]{12}", scan_id):
        raise HTTPException(status_code=404, detail="Scan not found.")
    scan_dir = UPLOADS_DIR / scan_id
    if not scan_dir.is_dir() or scan_id not in SCANS:
        raise HTTPException(status_code=404, detail="Scan not found.")

    project_dir = (scan_dir / "project").resolve()
    root_file = scan_dir / "root.txt"
    relative_root = root_file.read_text(encoding="utf-8") if root_file.is_file() else "."
    root = (project_dir / relative_root).resolve()

    target = (root / path).resolve()
    if not str(target).startswith(str(project_dir)) or not str(target).startswith(
        str(root)
    ):
        raise HTTPException(status_code=400, detail="Invalid file path.")
    if not target.is_file():
        raise HTTPException(status_code=404, detail="File not found in this scan.")
    if target.stat().st_size > 2 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File is too large to display.")

    content = target.read_text(encoding="utf-8", errors="replace")
    return {
        "path": path,
        "content": content,
        "lines": len(content.splitlines()),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)


