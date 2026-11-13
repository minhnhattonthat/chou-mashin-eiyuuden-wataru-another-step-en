"""Shared fixture: one insert.edits() run for every test module that inspects the English build."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))


@pytest.fixture(scope="session")
def built():
    import insert
    if not (insert.TREE / "SLPS_013.68").exists():
        pytest.skip("disc not unpacked")
    return insert.edits()
