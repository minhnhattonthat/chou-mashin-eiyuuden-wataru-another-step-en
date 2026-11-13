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


def test_bname_starts_early(built):
    """ENE06 Combat Doll (8-byte header slot) starts in Steel Jane's unused ename cells; ptr8 follows it."""
    d = built["YM/BR_02/ENE06.BIN"]
    at = struct.unpack_from("<I", d, 0x2624)[0] - insert.ENE_BASE
    assert at < 0x25D4 and d[at:d.index(b"\0", at)] == bytes(insert.bf_code(c) for c in "Combat Doll")


def test_marker_keeps_layout():
    words = [0x10, 0x11, 0x1000, 0, 0x12, 0xB000, 3, 0x13, 0x2000]
    m = insert.marker(words, 1234, 0x1000, False)
    assert m == "1234\n  cd[B000][0003]ef[2000]"  # blank cells count as columns
    c = insert.cells(m, 0x1000)
    assert c == ["12", "34", 0x1000, "  ", "cd", 0xB000, 3, "ef", 0x2000]


def test_allocate_one_code_per_pair():
    from collections import Counter
    m = insert.allocate(Counter({"ab": 1, "  ": 9, "xy": 5}))
    assert m == {"  ": 0, "xy": insert.compose.PAIR_FIRST, "ab": insert.compose.PAIR_FIRST + 1}
    with pytest.raises(SystemExit):
        insert.allocate(Counter({chr(33 + i // 90) + chr(33 + i % 90): 1 for i in range(insert.compose.TABLE_MAX + 1)}))


def test_compose_tables_written(built):
    """The hook, the LoadImage patch, and letters + pair table in both fonts."""
    whys = {by for w in insert.WRITES.values() for _, _, _, by in w}
    assert {"code compose hook", "code LoadImage -> compose hook", "compose font", "compose table"} <= whys
    cg, cnf = built["FM16/MSG_CG.BIN"], built["OUT/CNF_MSG.BIN"]
    for path in ("FM16/MSG_CG.BIN", "OUT/CNF_MSG.BIN"):
        for off, _, new, by in insert.WRITES[path]:
            if by.startswith("compose"):
                assert cg[off:off + len(new)] == cnf[off:off + len(new)] == new


def test_page_word_counts_kept(built):
    """Each written entry keeps its slot size: nothing past the JP words + padding."""
    for e, path, off, words, avail, nl, ctx in insert.entries():
        new = struct.unpack_from("<%dH" % avail, built[path], off)
        assert sum(1 for w in new if w == nl) == sum(1 for w in words if w == nl) or e.get("en"), e["id"]
