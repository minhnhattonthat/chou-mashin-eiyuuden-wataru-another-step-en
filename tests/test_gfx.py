"""Graphics-text rows (gfx/gfx.tsv): the exported original re-imports to no change, every English PNG maps onto
its palette, and the sprite records gfx.RECS patches still hold their original values."""
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import gfx  # noqa: E402


def test_rows_import():
    for r in gfx.rows():
        d = gfx.load(r["path"])
        lut = gfx.palette(gfx.load(r["cpath"]), r["coff"], r["pal"], r["bpp"])
        assert gfx.image(d, r["off"], r["bpp"], lut, r["rect"]).tobytes() == \
            gfx.Image.open(gfx.GFX / "orig" / r["png"]).convert("RGB").tobytes(), r["png"] + ": orig stale"
        gfx.indices(r, d, lut)  # raises on a colour outside the palette


def test_set_px_roundtrip():
    buf = bytearray(8 + 8 * 2)
    struct.pack_into("<4H", buf, 0, 0, 0, 2, 2)  # 2x2 halfwords = 8x2 px at 4bpp
    for v, (x, y) in enumerate([(0, 0), (1, 0), (7, 1), (6, 1)], 3):
        gfx.set_px(buf, 0, 4, x, y, v)
    assert [gfx.get_px(buf, 0, 4, x, y) for x, y in [(0, 0), (1, 0), (7, 1), (6, 1)]] == [3, 4, 5, 6]


def test_fmenu_labels():
    """G23: every label's records spell its JP, the strips fit the freed rows without overlap, and no other
    FD_STS record cuts a freed row."""
    d = gfx.load(gfx.FDS)
    recs = gfx.fm_recs(d)  # asserts the JP spelling
    assert len({off for _, off, *_ in recs}) == len(recs), "a record patched twice"
    lay = sorted(gfx.fm_layout().values(), key=lambda s: (s[1], s[0]))
    for (u, v, w), (u2, v2, _) in zip(lay, lay[1:]):
        assert v != v2 or u + w <= u2, "strips overlap"
    assert all(any(fv == v and fu <= u and u + w <= fu + fw for fu, fv, fw in gfx.FM_FREE) for u, v, w in lay)
    assert gfx.fm_check(d) == []


def test_card_labels():
    """G5: every card label spells a JP key with English, strips stay inside the freed rows without overlap, and no
    record outside the card lists cuts a freed row or bar B."""
    d = gfx.load(gfx.SBT)
    recs = gfx.sbt_recs(d)  # asserts JP keys, box twins
    assert len({off for _, off, *_ in recs}) == len(recs), "a record patched twice"
    strips = sorted((v, u, 8 * len(t) + 2) for t, (u, v) in gfx.sbt_layout(d).items())
    for (v, u, w), (v2, u2, _) in zip(strips, strips[1:]):
        assert v != v2 or u + w <= u2, "strips overlap"
    assert all(any(fv == v and fu <= u and u + w <= fu + fw for fu, fv, fw in gfx.SBT_FREE) for v, u, w in strips)
    bu, bv, bw, bh = gfx.SBT_BAR
    areas = [(u, v, w, 16) for u, v, w in gfx.SBT_FREE] + [gfx.SBT_BAR]
    for o in range(0, len(d) - 14, 2):
        tp, cl, u, v, w, h, x, y = struct.unpack_from(gfx.REC, d, o)
        if tp == 0x0C and 0x7DC0 <= cl <= 0x7DCF and not gfx.SBT_LISTS[0] <= o < gfx.SBT_LISTS[1]:
            assert not any(u < au + aw and au < u + w and v < av + ah and av < v + h for au, av, aw, ah in areas), hex(o)


def test_captions():
    """G6: 32 lists (16 captions x 2 CLUTs), each JP line gets one English strip, strips don't overlap, and every
    caption-CLUT record in SBTTL.BIN is inside the lists."""
    d = gfx.load(gfx.SBT)
    recs = gfx.cap_recs(d)  # asserts list and line counts
    assert len({off for _, off, *_ in recs}) == len(recs), "a record patched twice"
    assert sum(1 for *_, new, _ in recs if new[4]) == 2 * sum(len(en) for _, en in gfx.CAP_EN)
    strips = sorted(gfx.cap_layout().values())
    for (tp, u, v, w), (tp2, u2, v2, _) in zip(strips, strips[1:]):
        assert (tp, v) != (tp2, v2) or u + w <= u2, "strips overlap"
    assert all(u + w <= 256 and v + gfx.CAP_H <= 256 for _, u, v, w in strips)
    inside = {off for _, off, *_ in recs}
    for o in range(0, len(d) - 14, 2):
        tp, cl = struct.unpack_from("<HH", d, o)
        if tp in gfx.CAP_BLK and cl in (0x7E80, 0x7E81):
            assert o in inside, hex(o)


def test_staff_roll():
    """G25: every English page cell decodes back to its laid-out pair and colour from the rebuilt map; the CLUT and
    headers stay; entry 0 is the blank cell."""
    import staff
    d = gfx.load(staff.PATH)
    b = staff.build(d)
    assert len(b) == len(d) and b[:staff.CELLS + 8] == d[:staff.CELLS + 8]
    assert b[staff.MAP:staff.MAP + 8] == d[staff.MAP:staff.MAP + 8]
    cells, W, H, m = staff.parse(b)
    slot = {}
    for (pc, pr), rows in staff.pages().items():
        for j, row in enumerate(rows):
            for i in range(staff.PAGE_W):
                pair, pal = staff.cell_of(row[2 * i], row[2 * i + 1])
                c = cells[m[(pr * staff.PAGE_H + j) * W + pc * staff.PAGE_W + i]]
                xy = staff.cell_xy(c)
                assert pair == "  " or (c[2] == 0x79C0 + pal and slot.setdefault(pair, xy) == xy), (pc, pr, j, i)
                assert pair != "  " or xy == (0, 0)
    assert len(set(slot.values())) == len(slot), "two pairs share a cell"
    assert not any(staff.px(b, a, k) for a in range(16) for k in range(16)), "cell 0 not blank"


def test_recs_original():
    for path, off, fmt, old, new, why in gfx.RECS:
        assert struct.unpack_from(fmt, gfx.load(path), off) == old, why
