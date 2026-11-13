"""gfx_gen.py: draw the English graphics text into gfx/en/ from gfx/orig/ (rows in gfx/gfx.tsv, tools/gfx.py).

One section per group: clear rects (to the transparent colour) then draw text with a label class (font, size,
ramp of palette colours from full to faint coverage). Rerun after any wording change:
  python -X utf8 tools/gfx_gen.py [GROUP..]
Fonts only from fonts/ (docs/fonts.md).
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import gfx  # noqa: E402

FONTS = ROOT / "fonts"
SANS_B = FONTS / "liberation" / "LiberationSans-Bold.ttf"
SANS = FONTS / "liberation" / "LiberationSans-Regular.ttf"


def lut_of(png):
    r = next(r for r in gfx.rows() if r["png"] == png)
    return gfx.palette(gfx.load(r["cpath"]), r["coff"], r["pal"], r["bpp"])


def mask(text, font, size, spacing=0):
    """8-bit coverage of `text` (antialiased FreeType), tight box. spacing: extra px between letters."""
    f = ImageFont.truetype(str(font), size)
    if not spacing:
        l, t, r, b = f.getbbox(text)
        im = Image.new("L", (r - l + 2, b - t + 2))
        ImageDraw.Draw(im).text((1 - l, 1 - t), text, font=f, fill=255)
        return im.crop(im.getbbox())
    parts = [mask(c, font, size) if c != " " else Image.new("L", (size // 3, 1)) for c in text]
    asc = f.getbbox("H")[1]
    w = sum(p.size[0] for p in parts) + spacing * (len(parts) - 1)
    im = Image.new("L", (w, size * 2))
    x = 0
    for c, p in zip(text, parts):
        if c != " ":
            top = f.getbbox(c)[1] - asc + size // 2
            im.paste(p, (x, top))
        x += p.size[0] + spacing
    return im.crop(im.getbbox())


def put_text(img, lut, rect, text, font, size, ramp, align="center", spacing=0, cut=40, dy=0):
    """Draw text centred (or left) in rect = (x, y, w, h) of img; coverage -> ramp[0] (full) .. ramp[-1]."""
    m = mask(text, font, size, spacing)
    x, y, w, h = rect
    assert m.size[0] <= w and m.size[1] <= h, (text, m.size, rect)
    ox = x + ((w - m.size[0]) // 2 if align == "center" else 0)
    oy = y + (h - m.size[1]) // 2 + dy
    px, mp = img.load(), m.load()
    for j in range(m.size[1]):
        for i in range(m.size[0]):
            c = mp[i, j]
            if c > cut:
                k = min(len(ramp) - 1, (255 - c) * len(ramp) // (256 - cut))
                px[ox + i, oy + j] = lut[ramp[k]]
    return m.size


def bdf(name, cache={}):
    """{char: list of rows (lists of 0/1)}, every glyph in the font's full cell (FONTBOUNDINGBOX)."""
    if name in cache:
        return cache[name]
    out, cur, rows, fw, fh, fy = {}, None, None, 0, 0, 0
    for line in (FONTS / name).read_text(encoding="ascii").splitlines():
        k = line.split()
        if k and k[0] == "FONTBOUNDINGBOX":
            fw, fh, _, fy = map(int, k[1:])
        elif k and k[0] == "ENCODING":
            cur = int(k[1])
        elif k and k[0] == "BBX":
            bw, bh, bx, by = map(int, k[1:])
        elif line == "BITMAP":
            rows = []
        elif line == "ENDCHAR":
            if 0x20 <= cur < 0x7F:
                cell = [[0] * fw for _ in range(fh)]
                top = fh - (by - fy) - bh
                for j, r in enumerate(rows):
                    for i in range(bw):
                        if (r >> (8 * ((bw + 7) // 8) - 1 - i)) & 1:
                            cell[top + j][bx + i] = 1
                out[chr(cur)] = cell
            rows = None
        elif rows is not None:
            rows.append(int(line, 16))
    cache[name] = out
    return out


def put_bdf(img, lut, rect, text, font, ink, edge, align="center"):
    """Pixel-font text with a 1-px outline (8-neighbour) in rect; trims the font cell's empty rows/columns."""
    g = bdf(font)
    cols = [c for ch in text for c in zip(*g[ch])]  # columns left to right
    while cols and not any(cols[-1]):
        cols.pop()
    while cols and not any(cols[0]):
        cols.pop(0)
    rows_used = [j for j in range(len(cols[0])) if any(c[j] for c in cols)]
    j0, j1 = rows_used[0], rows_used[-1]
    w, h = len(cols) + 2, j1 - j0 + 3
    x, y, rw, rh = rect
    assert w <= rw + 2 and h <= rh, (text, (w, h), rect)  # up to 2 px over: the outline's end columns are cut
    ox = x + ((rw - w) // 2 if align == "center" else 0)
    oy = y + (rh - h + 1) // 2
    on = {(i + 1, j - j0 + 1) for i, c in enumerate(cols) for j in range(j0, j1 + 1) if c[j]}
    px = img.load()
    for i in range(w):
        if not x <= ox + i < x + rw:
            continue
        for j in range(h):
            if (i, j) in on:
                px[ox + i, oy + j] = lut[ink]
            elif any((i + a, j + b) in on for a in (-1, 0, 1) for b in (-1, 0, 1)):
                px[ox + i, oy + j] = lut[edge]
    return w, h


def clear(img, *rects):
    px = img.load()
    for x, y, w, h in rects:
        for j in range(y, y + h):
            for i in range(x, x + w):
                px[i, j] = gfx.MAGENTA


def title():
    """G4 title menu (palette 4, white -> purple) + G3 copyright line (palette 1, white -> blue)."""
    # menu words: Config keeps its rect; New Game / Continue (kana shared ニュー) get 80 px each (gfx.RECS)
    purple = [1, 1, 2, 3, 4, 6, 8, 10, 12, 14]
    for png, items in (("OUT/TTL_config.png", [((0, 0, 80, 16), "Config")]),
                       ("OUT/TTL_menu.png", [((0, 0, 80, 16), "New Game"), ((80, 0, 80, 16), "Continue")])):
        img = Image.open(gfx.GFX / "orig" / png).convert("RGB")
        clear(img, (0, 0) + img.size)
        for rect, t in items:
            put_text(img, lut_of(png), rect, t, SANS_B, 14, purple)
        img.save(gfx.GFX / "en" / png)
    # copyright (G3) line 1, in a plain sans like the original Latin; line 2 (BANPRESTO 1998) is Latin already
    png = "OUT/TTL_copy.png"
    img = Image.open(gfx.GFX / "orig" / png).convert("RGB")
    clear(img, (0, 0) + img.size)
    put_text(img, lut_of(png), (0, 0, 255, 16), "SUNRISE·RED·TV TOKYO·ASATSU", SANS, 15,
             [13, 13, 12, 10, 9, 8, 7, 5, 3, 1], spacing=1)
    img.save(gfx.GFX / "en" / png)


def battle():
    """G16 battle command column (5 rows, 13 px pitch from v=144) + party name columns (16-px rows)."""
    png = "YM/BR17_cmd.png"
    img = Image.open(gfx.GFX / "orig" / png).convert("RGB")
    lut = lut_of(png)
    clear(img, (0, 0) + img.size)
    for k, t in enumerate(("Fight", "Special", "Item", "Run", "Tactics")):
        put_bdf(img, lut, (0, 13 * k, 49, 13), t, "spleen-6x12.bdf", 1, 15)
    img.save(gfx.GFX / "en" / png)
    # names: col A (u 112, every record widened to 48 by gfx.RECS) and col B (u 160, w 40/48/40/64), rows
    # v 144/160/176/192; only the record rects are cleared (status icons sit beside col B)
    png = "YM/BR17_names.png"
    img = Image.open(gfx.GFX / "orig" / png).convert("RGB")
    for k, (t, wb) in enumerate((("Wataru", 40), ("Aragoto", 48), ("Sakuya", 40), ("Warurine", 64))):
        clear(img, (0, 16 * k, 48, 16), (48, 16 * k, wb, 16))
        put_bdf(img, lut, (0, 16 * k, 48, 16), t, "spleen-6x12.bdf", 1, 15)
        put_bdf(img, lut, (48, 16 * k, wb, 16), t, "spleen-6x12.bdf", 1, 15)
    img.save(gfx.GFX / "en" / png)


GROUPS = {"title": title, "battle": battle}

if __name__ == "__main__":
    for g in sys.argv[1:] or GROUPS:
        GROUPS[g]()
        print("drew", g)
