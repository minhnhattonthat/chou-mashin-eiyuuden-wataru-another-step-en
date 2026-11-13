"""staff.py: FVHH/STAFF.BIN, the staff roll (credits). Recon + render.

Layout (verified by rendering): CLUT upload (0,487) 256x1 (16 palettes) at 0; sprite list at 0x208
(u32 0x322, u16 count 0x800, u8 32, 64; 8-byte cells `u8 u, v, u16 clut, u16 0, u16 tp`, tp & 0xF = tpage: 6-9 =
the four 256-px quarters of the image); tile map at 0x4210 (u32 0x23, u8 W 120, H 98, 16, 16; W*H u16 cell
indices); image upload (384,0) 256x256 hw = 1024x256 4bpp at 0x9DF8.

English (G25): gfx/staff_en.txt is laid out per page as rows of 40 letters (8 px), cut into 16x16 cells of two
letters; each distinct letter pair is drawn once into the image (Spleen 8x16 bold, ink index 15), each distinct
(pair, palette) gets one cell entry, the map points every page cell at its entry (0 = blank). Map size, cell count
and page grid stay as they are, so the roll code is untouched.

usage: python -X utf8 tools/staff.py render OUT.png [STAFF.BIN]   whole tile map as one image
       python -X utf8 tools/staff.py cells                          cell usage summary
       python -X utf8 tools/staff.py en OUT.png                     render the English build of the map
"""
import struct
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PATH = "FVHH/STAFF.BIN"
SRC = ROOT / "work" / "disc" / "tree" / PATH
EN = ROOT / "gfx" / "staff_en.txt"
CLUT, CELLS, MAP, IMG = 0, 0x208, 0x4210, 0x9DF8
PAGE_W, PAGE_H = 20, 14  # cells per page (320x224)
PAL = {"W": 0, "O": 1, "Y": 2}  # CLUT (0,487) palettes: grey ramp, orange ramp, yellow ramp (0x79C0 + n)
INK = 15
SPLIT = 152  # default x where the left column ends; the right one starts 16 px later


def pages(text=None):
    """{(col, row): [40-letter rows as [(char, palette)..]]}, block centred vertically on the page."""
    out, cur, split = {}, None, SPLIT
    for line in (text if text is not None else EN.read_text(encoding="utf-8")).splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        if line.startswith("= "):
            k = line[2:].split()
            cur = out.setdefault(tuple(int(v) for v in k[0].split(",")), [])
            split = int(k[1].split("=")[1]) if len(k) > 1 else SPLIT
            continue
        row = [(" ", 0)] * 40
        if line.strip() != "-":
            parts = [p.strip() for p in line.split("|")]
            assert len(parts) <= 2, line
            for n, p in enumerate(parts):
                col = "Y" if len(parts) == 2 and n == 0 else "W"
                if len(p) > 1 and p[1] == ":" and p[0] in PAL:
                    col, p = p[0], p[2:]
                if not p:
                    continue
                if len(parts) == 1:
                    x = (40 - len(p)) // 2
                else:
                    x = split // 8 - len(p) if n == 0 else split // 8 + 2
                assert 1 <= x and x + len(p) <= 39, ("too wide (8-px margins)", line)
                for i, ch in enumerate(p):
                    row[x + i] = (ch, PAL[col])
        cur.append(row)
    for k, rows in out.items():
        assert len(rows) <= PAGE_H, (k, len(rows))
        top = (PAGE_H - len(rows)) // 2
        out[k] = [[(" ", 0)] * 40] * top + rows + [[(" ", 0)] * 40] * (PAGE_H - top - len(rows))
    return out


def cell_of(a, b):
    """(pair text, palette) of two letters; a cell mixing two colours is a layout bug."""
    pal = {p for ch, p in (a, b) if ch != " "}
    assert len(pal) <= 1, ("two colours in one cell", a, b)
    return a[0] + b[0], (pal.pop() if pal else 0)


def draw_pair(buf, cx, cy, pair):
    import gfx_gen
    g = gfx_gen.bdf("spleen-8x16.bdf")
    for k, ch in enumerate(pair):
        for i, c in enumerate(zip(*g[ch])):
            for j, on in enumerate(c):
                if on:
                    x, y = cx + 8 * k + i, cy + j
                    o = IMG + 8 + y * 512 + x // 2
                    buf[o] = (buf[o] & 0x0F | INK << 4) if x & 1 else (buf[o] & 0xF0 | INK)


def build(d, text=None):
    """English STAFF.BIN bytes from the original `d`."""
    cells, W, H, m = parse(d)
    P = pages(text)
    assert all(0 <= c < W // PAGE_W and 0 <= r < H // PAGE_H for c, r in P), "page outside the map"
    buf = bytearray(d)
    buf[IMG + 8:] = bytes(len(d) - IMG - 8)  # every JP glyph goes
    slots, ents, newmap = {"  ": 0}, {("  ", 0): 0}, [0] * (W * H)
    for (pc, pr), rows in sorted(P.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        for j, row in enumerate(rows):
            for i in range(PAGE_W):
                pair, pal = cell_of(row[2 * i], row[2 * i + 1])
                if pair == "  ":
                    continue
                if pair not in slots:
                    slots[pair] = len(slots)
                    assert slots[pair] < 1024, "image full (64x16 cells)"
                    s = slots[pair]
                    draw_pair(buf, (s % 64) * 16, (s // 64) * 16, pair)
                if (pair, pal) not in ents:
                    ents[(pair, pal)] = len(ents)
                    assert ents[(pair, pal)] < len(cells), "cell list full"
                newmap[(pr * PAGE_H + j) * W + pc * PAGE_W + i] = ents[(pair, pal)]
    for (pair, pal), e in ents.items():
        s = slots[pair]
        x, y = (s % 64) * 16, (s // 64) * 16
        tp = 6 + x // 256
        struct.pack_into("<BBHHH", buf, CELLS + 8 + 8 * e, x % 256, y, 0x79C0 + pal, 0, tp | (tp - 6) << 14)
    for e in range(len(ents), len(cells)):  # unused entries -> the blank cell, as the original's tail
        struct.pack_into("<BBHHH", buf, CELLS + 8 + 8 * e, 0, 0, 0x79C0, 0, 6)
    struct.pack_into(f"<{W * H}H", buf, MAP + 8, *newmap)
    return bytes(buf)


def writes(d):
    """[(offset, bytes)] runs where build(d) differs from d."""
    new, out, k = build(d), [], 0
    while k < len(d):
        if new[k] == d[k]:
            k += 1
            continue
        e = k
        while e < len(d) and new[e] != d[e]:
            e += 1
        out.append((k, new[k:e]))
        k = e
    return out


def spans():
    return [(CELLS + 8, len(SRC.read_bytes()))]  # cell list, tile map, image (the CLUT and headers stay)


def parse(d):
    assert struct.unpack_from("<4H", d, IMG) == (384, 0, 256, 256)
    tag, n, cw, ch = struct.unpack_from("<IHBB", d, CELLS)
    assert (tag, n) == (0x322, 0x800), (hex(tag), n)
    cells = [struct.unpack_from("<BBHHH", d, CELLS + 8 + 8 * i) for i in range(n)]
    tag, W, H, tw, th = struct.unpack_from("<IBBBB", d, MAP)
    assert (tag, tw, th) == (0x23, 16, 16)
    m = struct.unpack_from(f"<{W * H}H", d, MAP + 8)
    return cells, W, H, m


def pals(d):
    c = struct.unpack_from("<256H", d, CLUT + 8)
    return [[(0, 0, 0) if v == 0 else ((v & 31) * 8, (v >> 5 & 31) * 8, (v >> 10 & 31) * 8) for v in c[p * 16:p * 16 + 16]]
            for p in range(16)]


def px(d, x, y):
    b = d[IMG + 8 + y * 512 + x // 2]
    return b >> 4 if x & 1 else b & 15


def cell_xy(c):
    u, v, clut, _, tp = c
    return ((tp & 0xF) - 6) * 256 + u, v


def render(d, out):
    cells, W, H, m = parse(d)
    P = pals(d)
    im = Image.new("RGB", (W * 16, H * 16))
    put = im.load()
    for k, idx in enumerate(m):
        cx, cy = (k % W) * 16, (k // W) * 16
        c = cells[idx]
        x0, y0 = cell_xy(c)
        pal = P[c[2] & 0xF]
        for j in range(16):
            for i in range(16):
                put[cx + i, cy + j] = pal[px(d, x0 + i, y0 + j)]
    im.save(out)


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "render":
        render((Path(a[2]) if len(a) > 2 else SRC).read_bytes(), a[1])
    elif a and a[0] == "en":
        b = build(SRC.read_bytes())
        render(b, a[1])
        print("pairs", len(set(cell_xy(c) for c in parse(b)[0])), "entries", len(set(parse(b)[3])))
    elif a and a[0] == "cells":
        d = SRC.read_bytes()
        cells, W, H, m = parse(d)
        from collections import Counter
        print("map", W, H, "distinct cells used", len(set(m)))
        print("tp", Counter(c[4] for c in cells), "clut", Counter(c[2] for c in cells), "z", Counter(c[3] for c in cells))
    else:
        print(__doc__)
