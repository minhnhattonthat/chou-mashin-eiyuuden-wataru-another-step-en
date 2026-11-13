"""Phase 4: room text pages roundtrip through the codec and cover every text-like run (docs/re/text.md)."""
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import rooms  # noqa: E402
from jtext import Codec, load_rows, table  # noqa: E402

pytestmark = pytest.mark.skipif(not (rooms.FPRG / "R00.BIN").exists(), reason="disc not unpacked (tools/build.py)")


def waivers():
    out = {}
    for line in (ROOT / "tbl" / "room_data.txt").read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.startswith("#"):
            name, *offs = line.split()
            out[name] = {int(o, 16) for o in offs}
    return out


@pytest.mark.parametrize("name", rooms.OVERLAYS)
def test_room_pages(name):
    data = (rooms.FPRG / f"{name}.BIN").read_bytes()
    pages = rooms.pages(data)
    codecs = {}
    for o, n, term, _ in pages:
        f = rooms.font(name, o)
        c = codecs.setdefault(f, Codec(table(f)))
        text = c.decode(data[o:o + 2 * n])
        assert c.encode(text) == data[o:o + 2 * n], hex(o)
        assert not re.search(r"\[0[12][0-9A-F]{2}\]", text), f"{name} {o:#x}: code past the font: {text!r}"
    un = {o for o, _ in rooms.uncovered(data, [(o, n) for o, n, _, _ in pages])}
    assert un == waivers().get(name, set()), f"{name}: uncovered {sorted(map(hex, un))}"


def test_kanji_rows_match_fonts():
    rows = load_rows()
    for font, r in rows.items():
        if font != "CG":
            n = len((ROOT / "work/disc/tree/FM16" / f"{font}.BIN").read_bytes()) // 128
            assert sorted(r) == list(range(0x1A4, 0x1A4 + n)), font
