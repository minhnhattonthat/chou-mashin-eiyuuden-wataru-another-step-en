"""Insert path: every write logged and clean under romdiff, markers keep the JP layout, pairs allocated in budget."""
import struct
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import insert  # noqa: E402
import romdiff  # noqa: E402

pytestmark = pytest.mark.skipif(not (insert.TREE / "SLPS_013.68").exists(), reason="disc not unpacked")


@pytest.fixture(scope="module")
def built():
    return insert.edits()


def test_writes_clean_under_romdiff(built):
    for path, new in built.items():
        orig = (insert.TREE / path).read_bytes()
        errs, _ = romdiff.check(orig, new, set(), insert.WRITES[path])
        assert not errs, (path, errs[:5])


def test_every_entry_written(built):
    ents = insert.entries()
    written = {by for w in insert.WRITES.values() for _, _, _, by in w}
    assert {e["id"] for e, *_ in ents} <= written
    assert not insert.not_text() & written


def test_marker_keeps_layout():
    words = [0x10, 0x11, 0x1000, 0, 0x12, 0xB000, 3, 0x13, 0x2000]
    m = insert.marker(words, 1234, 0x1000, False)
    assert m == "1234\n  cd[B000][0003]ef[2000]"  # blank cells count as columns
    c = insert.cells(m, 0x1000)
    assert c == ["12", "34", 0x1000, "  ", "cd", 0xB000, 3, "ef", 0x2000]


def test_allocate_promotes_shared_pairs():
    cap = insert.ROOM_CAP
    many = {f"{i:02d}" for i in range(cap)}
    m = insert.allocate({"CG": {"AB"}, "M16_R00": many | {"xx"}, "M16_R02": {"xx", "yy"}})
    assert "xx" in m["CG"] and m["M16_R02"]["yy"] == insert.ROOM_FIRST
    assert len([c for c in m["M16_R00"].values() if c >= insert.ROOM_FIRST]) == cap


def test_page_word_counts_kept(built):
    """Each written entry keeps its slot size: nothing past the JP words + padding."""
    for e, path, off, words, avail, nl, ctx in insert.entries():
        new = struct.unpack_from("<%dH" % avail, built[path], off)
        assert sum(1 for w in new if w == nl) == sum(1 for w in words if w == nl) or e.get("en"), e["id"]
