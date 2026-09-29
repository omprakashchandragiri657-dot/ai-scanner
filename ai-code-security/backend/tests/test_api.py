"""API endpoint tests using FastAPI's TestClient."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import main
from analyzer.project_scanner import new_scan_id

from conftest import make_zip

client = TestClient(main.app)


@pytest.fixture(autouse=True)
def _fresh_scan_index() -> None:
    main.SCANS.clear()


def test_health() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["mode"] == "static-analysis"


def test_rules_endpoint() -> None:
    payload = client.get("/api/rules").json()
    assert payload["count"] >= 14
    ids = {rule["id"] for rule in payload["rules"]}
    assert {"PY-SQLI", "PY-CMDI", "JS-XSS", "JAVA-SQLI"} <= ids
    for rule in payload["rules"]:
        assert rule["cwe"].startswith("CWE-")
        assert rule["severity"] in {"CRITICAL", "HIGH", "MEDIUM", "LOW"}


def test_demo_project_structure() -> None:
    payload = client.get("/api/demo/project").json()
    assert payload["name"] == "FairShare"
    assert payload["source_files"] == 31
    assert payload["by_language"]["python"] == 18
    assert "intentionally vulnerable" in payload["note"]


def test_demo_project_scan() -> None:
    response = client.post("/api/projects/scan", data={"demo": "true"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["project"]["name"] == "FairShare"
    assert payload["project"]["files_scanned"] == 31
    summary = payload["summary"]
    assert summary["total"] == 12
    assert summary["critical"] == 2
    assert summary["high"] == 5
    assert summary["medium"] == 4
    assert summary["low"] == 1
    assert payload["stats"]["rules_executed"] >= 14
    assert payload["stats"]["duration_seconds"] >= 0
    for finding in payload["findings"]:
        for key in (
            "id",
            "title",
            "severity",
            "cwe",
            "confidence",
            "file",
            "line",
            "code",
            "description",
            "evidence",
            "recommendation",
            "detector",
        ):
            assert key in finding
        assert finding["context"]


def test_zip_upload_scan(simple_zip: bytes) -> None:
    response = client.post(
        "/api/projects/scan",
        files={"file": ("sample.zip", simple_zip, "application/zip")},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["project"]["files_scanned"] == 1
    assert payload["summary"]["critical"] == 1
    finding = payload["findings"][0]
    assert finding["cwe"] == "CWE-78"
    # the extracted file must be readable through the explorer endpoint
    scan_id = payload["project"]["scan_id"]
    file_response = client.get(
        "/api/projects/" + scan_id + "/file", params={"path": "app.py"}
    )
    assert file_response.status_code == 200
    assert "os.system" in file_response.json()["content"]


def test_zip_slip_upload_rejected() -> None:
    payload = make_zip({"../../evil.py": "import os\n"})
    response = client.post(
        "/api/projects/scan",
        files={"file": ("evil.zip", payload, "application/zip")},
    )
    assert response.status_code == 400
    assert "Unsafe path" in response.json()["detail"]


def test_invalid_file_rejected() -> None:
    response = client.post(
        "/api/projects/scan",
        files={"file": ("notes.txt", b"hello", "text/plain")},
    )
    assert response.status_code == 400


def test_missing_file_rejected() -> None:
    response = client.post("/api/projects/scan")
    assert response.status_code == 400


def test_unsupported_project_rejected() -> None:
    payload = make_zip({"docs/readme.md": "# hi\n"})
    response = client.post(
        "/api/projects/scan",
        files={"file": ("docs.zip", payload, "application/zip")},
    )
    assert response.status_code == 400
    assert "No supported source files" in response.json()["detail"]


def test_stream_scan_emits_events(simple_zip: bytes) -> None:
    response = client.post(
        "/api/projects/scan?stream=true",
        files={"file": ("sample.zip", simple_zip, "application/zip")},
    )
    assert response.status_code == 200
    events = [
        __import__("json").loads(line)
        for line in response.text.splitlines()
        if line.strip()
    ]
    kinds = [event["type"] for event in events]
    assert "structure" in kinds
    assert "progress" in kinds
    assert kinds[-1] == "result"
    assert events[-1]["result"]["summary"]["total"] == 1


def test_code_analyze_endpoint() -> None:
    response = client.post(
        "/api/code/analyze",
        json={"code": "os.system(user_input)\n", "language": "python"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["total"] == 1
    assert payload["findings"][0]["cwe"] == "CWE-78"


def test_code_analyze_rejects_empty() -> None:
    response = client.post("/api/code/analyze", json={"code": "   "})
    assert response.status_code == 400


def test_file_endpoint_rejects_bad_scan_id() -> None:
    response = client.get(
        "/api/projects/not-a-scan/file", params={"path": "app.py"}
    )
    assert response.status_code == 404


def test_file_endpoint_rejects_path_traversal() -> None:
    result = {
        "project": {"name": "x"},
        "summary": {"total": 0},
        "stats": {},
        "findings": [],
    }
    scan_id = new_scan_id()
    main.SCANS[scan_id] = result
    response = client.get(
        f"/api/projects/{scan_id}/file",
        params={"path": "../../../Windows/win.ini"},
    )
    assert response.status_code in {400, 404}
