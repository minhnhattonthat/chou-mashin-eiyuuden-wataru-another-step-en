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


def test_recs_original():
    for path, off, fmt, old, new, why in gfx.RECS:
        assert struct.unpack_from(fmt, gfx.load(path), off) == old, why
