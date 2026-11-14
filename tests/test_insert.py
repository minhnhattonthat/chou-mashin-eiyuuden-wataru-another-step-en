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


def allowed_spans(path, orig):
    """[(lo, hi)] byte spans the build may write in `path`, from the script layout and the named code/data sites
    (not from the writes): text slots + terminators, pointer and lui/lo sites of movable strings, free space, the
    compose font/table/hook, strips, CODE words, battle-font cells."""
    import compose
    import roompack
    import rooms
    import strpack
    s = []
    ents = [t for t in insert.entries() if t[1] == path]
    enames = sorted(off for e, _, off, *_ in ents if e.get("kind") == "ename")
    if path in strpack.BASE:
        u32, code, _ = strpack.refs(orig, strpack.BASE[path])
    for e, _, off, words, avail, nl, ctx in ents:
        if "len_at" in e:
            s.append((int(e["len_at"], 16), int(e["len_at"], 16) + 1))
        if e.get("kind") == "bname":  # may start in the ename slot before it; its ptr8 is re-aimed
            s.append((max([o for o in enames if o < off], default=off), off + avail + 1))
            for k in range(0, len(orig) - 3, 4):
                if struct.unpack_from("<I", orig, k)[0] == insert.ENE_BASE + off:
                    s.append((k, k + 4))
            continue
        end = off + 2 * avail
        if insert.movable(e, path):
            end += strpack.term_len(orig, e, off, avail) or 0
            end += 2 if end % 4 else 0  # the zero word padding the next string to 4 bytes
            s += [(k, k + 4) for k in u32.get(off, [])] + [(k, k + 4) for lu_lo in code.get(off, []) for k in lu_lo]
        s.append((off, end))
    if path in strpack.TAIL_END:
        s.append(((len(orig) + 3) & ~3, strpack.TAIL_END[path] - strpack.BASE[path]))
    if path in strpack.POOL:
        s.append((min(a for a, _ in s), max(b for _, b in s)))
    if path.startswith("FPRG/R"):
        name = Path(path).stem
        s += [(p[0]["start"], p[-1]["end"]) for p in roompack.pools(name)]
        s += [(u["start"], u["end"]) for u in roompack.units(name)]
        s.append(((len(orig) + 3) & ~3, roompack.LIMIT))
        s += [(k, k + 4) for ks in rooms.pointers(orig).values() for k in ks]
    if path == insert.EXE:
        s.append((strpack.EXE_FREE[0] - strpack.BASE[path], strpack.EXE_FREE[1] - strpack.BASE[path]))
        s.append((compose.HOOK - compose.EXE_BASE, strpack.EXE_FREE[1] - compose.EXE_BASE))
        s.append((compose.LOADIMAGE - compose.EXE_BASE, compose.LOADIMAGE - compose.EXE_BASE + 8))
    if path in ("FM16/MSG_CG.BIN", "OUT/CNF_MSG.BIN"):
        s.append((compose.FONT - compose.FONT_RAM, compose.FONT - compose.FONT_RAM + 95 * 64))
        s.append((compose.TABLE - compose.FONT_RAM, compose.TABLE - compose.FONT_RAM + 2 * compose.TABLE_MAX))
    if path == "FM16/MSG_CG.BIN":
        s.append((insert.BF_FIRST * 64, (insert.BF_FIRST + 0x5F) * 64))
        s += [(0x5300 + k * 128, 0x5300 + k * 128 + 128) for k in insert.digraph.ICONS]  # element icons
    if path == "PRG/MACHINE.BIN":
        s.append((insert.STRIP_LIST, insert.STRIP_END))
        for addiu, slti, names in insert.STRIP_ROWS:
            s += [(addiu, addiu + 4), (slti, slti + 4)]
            s += [r for _, recs in names for uo, wo in recs for r in ((uo, uo + 1), (wo, wo + 2))]
        s += [(k, k + 4) for k in insert.STRIP_SHORT[1:]]
    s += [(off, off + 4) for p, off, *_ in insert.CODE if p == path]
    s += [(off, off + e["max"]) for e, p, off in insert.sjis_entries() if p == path]
    s += insert.gfx.spans(path)
    return strpack.coalesce(s)


def test_writes_clean_under_romdiff(built):
    """romdiff on every edited file, then every logged write must sit inside the file's allowed spans."""
    import bisect
    for path, new in built.items():
        orig = (insert.TREE / path).read_bytes()
        errs, _ = romdiff.check(orig, new, set(), insert.WRITES[path])
        assert not errs, (path, errs[:5])
        spans = allowed_spans(path, orig)
        los = [a for a, _ in spans]
        out = [(hex(off), by) for off, _, data, by in insert.WRITES[path]
               if (i := bisect.bisect_right(los, off) - 1) < 0 or off + len(data) > spans[i][1]]
        assert not out, (path, len(out), out[:5])


def test_spu_zero_buffer_stays_zero(built):
    """SpuClearReverbWorkArea uploads strpack.SPU_ZERO to SPU RAM: nothing may be written there."""
    import strpack
    a, b = (x - strpack.BASE[insert.EXE] for x in strpack.SPU_ZERO)
    assert built[insert.EXE][a:b] == bytes(b - a)


def test_no_overflow(built):
    """A real build never falls back to a marker (edits() raises; this guards the qa-only fallback)."""
    assert not insert.OVERFLOW


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
