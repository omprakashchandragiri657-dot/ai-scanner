"""ZIP extraction security tests."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pytest

from analyzer.project_scanner import ZipSecurityError, safe_extract
from analyzer.utils import MAX_ZIP_FILES, MAX_ZIP_SIZE

from conftest import make_zip


def test_valid_zip_extracts(tmp_path: Path) -> None:
    payload = make_zip({"proj/main.py": "print('hi')\n"})
    safe_extract(payload, tmp_path / "out")
    assert (tmp_path / "out" / "proj" / "main.py").is_file()


def test_zip_slip_rejected(tmp_path: Path) -> None:
    payload = make_zip({"../../evil.py": "import os\n"})
    with pytest.raises(ZipSecurityError, match="Unsafe path"):
        safe_extract(payload, tmp_path / "out")
    assert not list(tmp_path.glob("**/evil.py"))


def test_absolute_path_rejected(tmp_path: Path) -> None:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("/etc/evil.py", "x = 1\n")
    with pytest.raises(ZipSecurityError, match="Unsafe path"):
        safe_extract(buffer.getvalue(), tmp_path / "out")


def test_windows_drive_path_rejected(tmp_path: Path) -> None:
    payload = make_zip({"C:\\windows\\evil.py": "x = 1\n"})
    with pytest.raises(ZipSecurityError, match="Unsafe path"):
        safe_extract(payload, tmp_path / "out")


def test_too_many_files_rejected(tmp_path: Path) -> None:
    entries = {f"dir/file_{index}.py": "x = 1\n" for index in range(MAX_ZIP_FILES + 1)}
    with pytest.raises(ZipSecurityError, match="too many entries"):
        safe_extract(make_zip(entries), tmp_path / "out")


def test_oversized_zip_rejected(tmp_path: Path) -> None:
    limit_mb = MAX_ZIP_SIZE // (1024 * 1024)
    with pytest.raises(ZipSecurityError, match=f"{limit_mb} MB"):
        safe_extract(b"PK" + b"\0" * (MAX_ZIP_SIZE + 1), tmp_path / "out")


def test_not_a_zip_rejected(tmp_path: Path) -> None:
    with pytest.raises(ZipSecurityError, match="ZIP"):
        safe_extract(b"this is not a zip file", tmp_path / "out")


def test_corrupted_zip_rejected(tmp_path: Path) -> None:
    with pytest.raises(ZipSecurityError):
        safe_extract(b"PK\x03\x04corrupted-data", tmp_path / "out")


def test_empty_zip_allowed(tmp_path: Path) -> None:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w"):
        pass
    safe_extract(buffer.getvalue(), tmp_path / "out")  # no exception
    assert (tmp_path / "out").exists()


def test_ignored_dirs_not_extracted_and_counted(tmp_path: Path) -> None:
    entries = {f"proj/node_modules/pkg/file_{i}.js": "x = 1\n" for i in range(50)}
    entries["proj/app.py"] = "print(1)\n"
    entries[".git/config"] = "[core]\n"
    stats = safe_extract(make_zip(entries), tmp_path / "out")
    assert stats["ignored_entries"] == 51
    assert not (tmp_path / "out" / "proj" / "node_modules").exists()
    assert not (tmp_path / "out" / ".git").exists()
    assert (tmp_path / "out" / "proj" / "app.py").is_file()


def test_ignored_entries_do_not_count_toward_entry_limit(tmp_path: Path) -> None:
    """A node_modules-heavy archive must NOT trip the entry cap."""
    entries = {
        f"proj/node_modules/pkg/file_{i}.js": "x = 1\n"
        for i in range(MAX_ZIP_FILES + 1)
    }
    entries["proj/app.py"] = "print(1)\n"
    stats = safe_extract(make_zip(entries), tmp_path / "out")
    assert stats["ignored_entries"] == MAX_ZIP_FILES + 1
    assert (tmp_path / "out" / "proj" / "app.py").is_file()


def test_too_many_non_ignored_entries_still_rejected(tmp_path: Path) -> None:
    entries = {f"src/file_{index}.py": "x = 1\n" for index in range(MAX_ZIP_FILES + 1)}
    with pytest.raises(ZipSecurityError, match="too many entries"):
        safe_extract(make_zip(entries), tmp_path / "out")
