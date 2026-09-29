"""Shared pytest fixtures."""

from __future__ import annotations

import io
import sys
import zipfile
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def make_zip(entries: dict[str, str]) -> bytes:
    """Build an in-memory ZIP from {path: content}."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for path, content in entries.items():
            archive.writestr(path, content)
    return buffer.getvalue()


@pytest.fixture
def simple_zip() -> bytes:
    return make_zip(
        {
            "sample/app.py": (
                'import os\n'
                'def run(cmd):\n'
                '    os.system(cmd)\n'
            ),
            "sample/README.md": "# sample\n",
        }
    )
