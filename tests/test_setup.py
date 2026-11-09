import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import tbl  # noqa: E402

BIN = ROOT / "rom" / "Chou Mashin Eiyuuden Wataru - Another Step (Japan).bin"


def test_rom_sha1_listing_parses():
    lines = [l for l in (ROOT / "rom.sha1").read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
    assert len(lines) == 1 and len(lines[0].split(None, 1)[0]) == 40


@pytest.mark.skipif(not BIN.exists(), reason="no ROM")
def test_rom_matches_sha1():
    import check_rom
    check_rom.check()


def test_tbl_importable():
    assert hasattr(tbl, "__doc__")
