"""gfx.py: graphics-text redraws. Export a rect of an upload block (docs/re/graphics.md) as RGB PNG under its CLUT,
and write edited PNGs back into the disc files through insert.put() (build) by palette index.

gfx/gfx.tsv rows (tab-separated, # comments):
  png  target file  block offset  bpp  clut file  clut offset  palette  rect x,y,w,h (block pixels)
`png` is relative to gfx/en/ (the English); the original rect goes to gfx/orig/ (export). A png may be listed for
several targets (the same image in several files). Colour 0x0000 (transparent) shows as magenta (255,0,255).
Import keeps a pixel's original index when its colour didn't change, else takes the first palette index with that
colour (index 0 only for magenta); any colour outside the palette fails the build.

usage: python -X utf8 tools/gfx.py export [ROW-PNG..]      write gfx/orig/<png> (+ gfx/en/<png> if missing)
       python -X utf8 tools/gfx.py show FILE OFF BPP CLUTFILE CLUTOFF PAL OUT.png   whole block, one palette
"""
import struct
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
TREE = ROOT / "work" / "disc" / "tree"
GFX = ROOT / "gfx"
MAGENTA = (255, 0, 255)


# Sprite records that cut the redrawn text out of its atlas: (path, offset, struct fmt, original, new, why).
# TTL.BIN title menu: [u16 tpage, u16 clut, u8 u, u8 v, u16 w, u16 h, s16 x, s16 y] (docs/re/graphics.md G4).
REC = "<HHBBHHhh"
RECS = [
    ("PRG/TTL.BIN", 0x4FA2, REC, (0x1A, 0x7E44, 0, 112, 112, 16, -56, -40), (0x1A, 0x7E44, 80, 112, 80, 16, -40, -40),
     "title Continue"),
    ("PRG/TTL.BIN", 0x4FB0, REC, (0x1A, 0x7E44, 64, 112, 96, 16, -48, -56), (0x1A, 0x7E44, 0, 112, 80, 16, -40, -56),
     "title New Game"),
]
# BALLBAT party-panel names (col u=112, rows v 144-192): w 32/40 -> 48, left edge kept (HP digits sit far right)
RECS += [("PRG/BALLBAT.BIN", off + 6, "<H", (w,), (48,), "battle name w") for off, w in
         ((0x250FC, 32), (0x2510A, 40), (0x25118, 32), (0x25144, 32), (0x25160, 32), (0x2518C, 32), (0x2519A, 40))]


def rows():
    out = []
    for line in (GFX / "gfx.tsv").read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        png, path, off, bpp, cpath, coff, pal, rect = line.split("\t")[:8]
        coff = -int(coff[1:], 16) - 1 if coff.startswith("r") else int(coff, 16)  # rHEX: raw colours
        out.append(dict(png=png, path=path, off=int(off, 16), bpp=int(bpp), cpath=cpath, coff=coff,
                        pal=int(pal), rect=tuple(int(v) for v in rect.split(","))))
    return out


def palette(d, coff, pal, bpp):
    """CLUT upload block at coff (16 palettes per 256-wide row), or raw colours when coff < 0 (at -coff - 1:
    YM/BR_17/OTHER*.CHG keep theirs in the 0xC00-byte header)."""
    n = 16 if bpp == 4 else 256
    if coff < 0:
        return _cols(struct.unpack_from(f"<{n}H", d, -coff - 1 + pal * 2 * n))
    w = struct.unpack_from("<H", d, coff + 4)[0]
    cols = struct.unpack_from(f"<{n}H", d, coff + 8 + pal * 32 * (bpp == 4))
    assert pal * n + n <= w or bpp == 8, "palette past the CLUT row"
    return _cols(cols)


def _cols(cols):
    return [MAGENTA if c == 0 else ((c & 31) * 255 // 31, (c >> 5 & 31) * 255 // 31, (c >> 10 & 31) * 255 // 31)
            for c in cols]


def _geom(d, off, bpp):
    x, y, w, h = struct.unpack_from("<4H", d, off)
    return w * 2 * (2 if bpp == 4 else 1), h  # pixel width, height


def get_px(d, off, bpp, px, py):
    pw, _ = _geom(d, off, bpp)
    if bpp == 8:
        return d[off + 8 + py * pw + px]
    b = d[off + 8 + py * pw // 2 + px // 2]
    return b >> 4 if px & 1 else b & 15


def set_px(buf, off, bpp, px, py, v):
    pw, _ = _geom(buf, off, bpp)
    if bpp == 8:
        buf[off + 8 + py * pw + px] = v
        return
    k = off + 8 + py * pw // 2 + px // 2
    buf[k] = (buf[k] & 0x0F | v << 4) if px & 1 else (buf[k] & 0xF0 | v)


def image(d, off, bpp, lut, rect=None):
    pw, ph = _geom(d, off, bpp)
    x0, y0, w, h = rect or (0, 0, pw, ph)
    im = Image.new("RGB", (w, h))
    im.putdata([lut[get_px(d, off, bpp, x0 + i, y0 + j)] for j in range(h) for i in range(w)])
    return im


def load(path, cache={}):
    if path not in cache:
        cache[path] = (TREE / path).read_bytes()
    return cache[path]


def export(only=()):
    for r in rows():
        if only and r["png"] not in only:
            continue
        d = load(r["path"])
        im = image(d, r["off"], r["bpp"], palette(load(r["cpath"]), r["coff"], r["pal"], r["bpp"]), r["rect"])
        for sub in ("orig", "en"):
            p = GFX / sub / r["png"]
            if sub == "orig" or not p.exists():
                p.parent.mkdir(parents=True, exist_ok=True)
                im.save(p)
        print(r["png"], r["path"], hex(r["off"]), r["rect"])


def indices(r, d, lut):
    """Palette indices of gfx/en/<png> for row r (ValueError on a colour outside the palette)."""
    im = Image.open(GFX / "en" / r["png"]).convert("RGB")
    x0, y0, w, h = r["rect"]
    assert im.size == (w, h), (r["png"], im.size, (w, h))
    first = {}
    for i, c in enumerate(lut):
        if c != MAGENTA or i == 0:
            first.setdefault(c, i)
    out = {}
    px = im.load()
    for j in range(h):
        for i in range(w):
            c = px[i, j]
            o = get_px(d, r["off"], r["bpp"], x0 + i, y0 + j)
            if lut[o] == c:
                continue
            if c not in first:
                raise ValueError(f"{r['png']} ({i},{j}): colour {c} not in palette {r['pal']}")
            out[(x0 + i, y0 + j)] = first[c]
    return out


def apply(put, bufs, orig, load_path):
    """Write every gfx.tsv row through insert.put(); one put per changed byte run."""
    for r in rows():
        p = load_path(r["path"])
        d = orig[p]
        buf = bytearray(bufs.get(p, d))
        lut = palette(orig[load_path(r["cpath"])], r["coff"], r["pal"], r["bpp"])
        for (x, y), v in indices(r, d, lut).items():
            set_px(buf, r["off"], r["bpp"], x, y, v)
        cur = bufs.get(p, d)
        k, n = 0, len(buf)
        while k < n:
            if buf[k] == cur[k]:
                k += 1
                continue
            e = k
            while e < n and buf[e] != cur[e]:
                e += 1
            put(bufs, orig, p, k, bytes(buf[k:e]), "gfx " + r["png"])
            k = e
    for path, off, fmt, old, new, why in RECS:
        p = load_path(path)
        assert struct.unpack_from(fmt, orig[p], off) == old, (path, hex(off), why)
        put(bufs, orig, p, off, struct.pack(fmt, *new), "gfx rec " + why)


def spans(path):
    """Byte spans gfx.tsv rows may write in `path` (test_insert allowed_spans)."""
    out = []
    for r in rows():
        if r["path"] != path:
            continue
        d = load(path)
        pw, _ = _geom(d, r["off"], r["bpp"])
        x0, y0, w, h = r["rect"]
        bpr = pw if r["bpp"] == 8 else pw // 2
        for y in range(y0, y0 + h):
            a = r["off"] + 8 + y * bpr + (x0 if r["bpp"] == 8 else x0 // 2)
            out.append((a, a + (w if r["bpp"] == 8 else (w + 2) // 2)))
    out += [(off, off + struct.calcsize(fmt)) for p, off, fmt, *_ in RECS if p == path]
    return out


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "export":
        export(set(a[1:]))
    elif a and a[0] == "show":
        f, off, bpp, cf, coff, pal, out = a[1:8]
        image(load(f), int(off, 16), int(bpp), palette(load(cf), int(coff, 16), int(pal), int(bpp))).save(out)
    else:
        print(__doc__)
