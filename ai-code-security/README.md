# AI Code Security Analyzer

**Detecting Security Vulnerabilities in AI-Generated Software**

A working demo MVP that takes an entire software project, scans its source files,
identifies potential security vulnerabilities, explains the findings and provides
remediation suggestions.

---

## Project Overview

The AI Code Security Analyzer is a **static source-code security analyzer** for
research and demonstration. It accepts a project ZIP (or a built-in demo project),
securely extracts it, recursively discovers supported source files, runs a modular
set of detection rules against every file, then normalizes and deduplicates the
results into a project security report with per-file and per-line evidence.

The system scans the **whole project**, not just a single pasted code snippet.

## Research Objective

> To systematically identify, quantify, and explain security vulnerabilities
> introduced by AI-generated software before it reaches production.

---

## Architecture

```text
Frontend (React + Vite, port 5173)
        │  proxy /api
        ▼
FastAPI backend (port 8000)
        │
        ├── ZIP validation & safe extraction   (uploads/<scan_id>/project)
        ├── Project traversal & structure analysis
        ├── Detection engine (SecurityRule registry, 20 rules)
        │       ├── python_rules.py
        │       ├── javascript_rules.py   (JS + TS)
        │       └── java_rules.py
        ├── Normalization · deduplication · severity summary
        └── Local storage (uploads/<scan_id>/result.json)
```

Key backend modules:

| Module | Responsibility |
| --- | --- |
| `backend/main.py` | FastAPI app, endpoints, streaming scan events |
| `backend/analyzer/engine.py` | `SecurityRule` base class + rule registry |
| `backend/analyzer/scanner.py` | Per-file scanning, normalization, dedup, IDs |
| `backend/analyzer/project_scanner.py` | Safe ZIP extraction, traversal, orchestration |
| `backend/analyzer/rules/*.py` | Language-specific detection rules |
| `backend/analyzer/models.py` | Finding / ScanResult pydantic models |
| `backend/analyzer/utils.py` | Limits, language detection, context snippets |

## Technology Stack

**Backend:** Python 3.12+, FastAPI, Uvicorn, pydantic
**Frontend:** React 19, TypeScript, Vite, Tailwind CSS 4, Recharts, React Router
**Storage:** temporary/local storage only — no PostgreSQL or Redis

## Supported Languages

| Language | Extensions |
| --- | --- |
| Python | `.py` |
| JavaScript | `.js`, `.jsx` |
| TypeScript | `.ts`, `.tsx` |
| Java | `.java` |

Ignored directories (configurable in `analyzer/utils.py::DEFAULT_IGNORED_DIRS`):
`.git`, `node_modules`, `venv`, `.venv`, `__pycache__`, `dist`, `build`, `target`,
`.idea`, `.vscode`, `coverage`, `.cache`.

Individual source files larger than **2 MB** are skipped and reported under
*Skipped Files*.

## Supported Vulnerabilities

| Vulnerability | CWE | Severity | Languages |
| --- | --- | --- | --- |
| SQL Injection | CWE-89 | HIGH | Python, Java |
| Command Injection | CWE-78 | CRITICAL | Python, JavaScript, Java |
| Code Injection (eval/exec) | CWE-95 | CRITICAL | Python, JavaScript |
| Cross-Site Scripting | CWE-79 | HIGH | JavaScript, TypeScript |
| Insecure Deserialization | CWE-502 | HIGH | Python, Java |
| Hardcoded Credentials | CWE-798 | HIGH | Python, JavaScript, Java |
| Path Traversal | CWE-22 | HIGH | Python |
| Weak Cryptography (MD5/SHA1) | CWE-327 | MEDIUM | Python |
| Debug Mode Enabled | CWE-489 | MEDIUM | Python |
| Disabled TLS Verification | CWE-295 | MEDIUM | Python |
| Weak Random Token | CWE-338 | MEDIUM | Python |
| Cleartext HTTP | CWE-319 | LOW | Python, JavaScript |

Every finding carries file, line number, code snippet with surrounding context,
confidence, description, detection evidence flow and a before/after recommended fix.

---

## Installation

### Prerequisites

* Python 3.12 or newer
* Node.js 18+ and npm

### Backend Setup

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
## Running the Application

1. Start the backend (terminal 1): `cd backend` → activate venv → `uvicorn main:app --reload`
2. Start the frontend (terminal 2): `cd frontend` → `npm run dev`
3. Open `http://localhost:5173`

## Scanning a Project

1. Open **Project Scanner** in the sidebar.
2. Drop `project.zip` (max 100 MB) onto the upload area — or click to browse.
   On the Dashboard, **Upload Project** opens the native file picker for any file,
   and **Upload Folder** compresses a whole project folder to a ZIP in the browser
   (no manual zipping needed).
3. The project structure is analyzed, files are discovered recursively, and a
   progress screen shows every file being scanned (based on the real files
   processed — nothing is simulated).
4. The **Security Report** appears with statistics, severity/file/CWE charts,
   a file explorer (per-file finding counts) and a source viewer.
5. Click a file to read its source; click a finding marker to open the full
   analysis: vulnerable code, why it is vulnerable, detection evidence and the
   recommended fix.
6. Use **Export Report** to download `security-report.json`.

**Paste Code** is available as an optional secondary feature for single snippets.

### Demo Project

Click **Try Demo Project** on the Project Scanner page to load the built-in
FairShare project (31 source files across Python, JavaScript, TypeScript and
Java), then **Scan Demo Project** to run the full pipeline.

> Demo project contains intentionally vulnerable code for security testing.

The demo scan reports **12 vulnerabilities** (2 critical, 5 high, 4 medium,
1 low) produced by the real detection engine — the frontend contains no
hardcoded results.

## API Documentation

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/health` | Service health and version |
| POST | `/api/projects/scan` | Scan an uploaded ZIP (`file` form field) or the demo project (`demo=true`) |
| POST | `/api/code/analyze` | Analyze a pasted snippet (`{"code": "...", "language": "python"}`) |
| GET | `/api/rules` | List every registered detection rule |
| GET | `/api/demo/project` | Structure of the built-in demo project (not yet scanned) |
| GET | `/api/projects/{scan_id}/file?path=` | Source file content for the explorer |

### Scanning a project

```bash
curl -F "file=@project.zip" http://127.0.0.1:8000/api/projects/scan
```

Response shape:

```json
{
  "project": {
    "name": "FairShare",
    "files_scanned": 31,
    "lines_analyzed": 1062
  },
  "summary": { "total": 12, "critical": 2, "high": 5, "medium": 4, "low": 1 },
  "stats": { "rules_executed": 20, "duration_seconds": 0.14 },
  "findings": [
    {
      "id": "VULN-003",
      "title": "SQL Injection",
      "severity": "HIGH",
      "cwe": "CWE-89",
      "confidence": 91,
      "file": "backend/users.py",
      "line": 10,
      "code": "cursor.execute(query)",
      "description": "User-controlled input appears to reach SQL execution without safe parameterization.",
      "evidence": "The SQL query is constructed using unsafe query variable around `query` instead of bound parameters.",
      "recommendation": "Use parameterized SQL queries.",
      "detector": "SQL Injection Rule"
    }
  ]
}
```

With `?stream=true` the endpoint returns NDJSON progress events
(`step` → `structure` → `progress` per file → `result`) so the UI can show
real per-file scanning progress.

## Security Considerations

* **Uploaded code is never executed.** The analyzer only extracts, reads,
  parses (lexically) and reports.
* ZIP uploads are validated: max 100 MB archive, max 500 MB extracted,
  max 10,000 entries, compression-ratio (ZIP bomb) guard, and **Zip Slip /
  absolute path rejection** — every extracted file must stay inside the
  project directory. Entries inside ignored folders (`node_modules`, `.git`,
  `venv`, `dist`, ...) are skipped during extraction, never counted toward the
  limits and never scanned — so zipping a project folder as-is works.
  project directory.
* Symbolic links in archives are ignored.
* The file-explorer endpoint resolves paths inside the scanned project only.
* Limits are enforced on snippet size (512 KB) and displayed file size (2 MB).

## Future Research

Planned research extensions (not yet implemented):

* Multi-engine detection (Semgrep, CodeQL)
* AST analysis
* Taint analysis
* LLM-assisted analysis
* Dynamic testing
* Vulnerability correlation
* Dataset generation
* AI model comparison

The detection engine is intentionally modular — new engines plug in through the
`SecurityRule` registry without touching the scanner or the API layer.

# source venv/bin/activate

pip install -r requirements.txt
uvicorn main:app --reload
```

The API is available at `http://127.0.0.1:8000` (interactive docs at `/docs`).

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The UI is available at `http://localhost:5173` and proxies `/api` to the backend.

### Running Tests

```bash
cd backend
venv\Scripts\python.exe -m pytest tests -q
```

Covers ZIP extraction security, path traversal protection, file filtering,
SQL/command injection detection, hardcoded secret detection, XSS detection,
eval detection, finding normalization, severity calculation and API responses.

---
