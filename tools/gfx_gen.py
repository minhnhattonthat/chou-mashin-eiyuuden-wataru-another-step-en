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


def bdf_width(text, font="spleen-6x12.bdf"):
    """Width put_bdf draws `text` at with a 1-px outline."""
    cols = [c for ch in text for c in zip(*bdf(font)[ch])]
    while cols and not any(cols[-1]):
        cols.pop()
    while cols and not any(cols[0]):
        cols.pop(0)
    return len(cols) + 2


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


def _embolden(cols):
    out = [tuple(a | b for a, b in zip(c, p)) for c, p in zip(cols + [(0,) * len(cols[0])], [(0,) * len(cols[0])] + cols)]
    return out


def put_bdf(img, lut, rect, text, font, ink, edge, align="center", trim=True, shadow=None, bold=False):
    """Pixel-font text with a 1-px outline (8-neighbour; none when edge is None) in rect; trims the font cell's
    empty rows/columns."""
    g = bdf(font)
    cols = [c for ch in text for c in zip(*g[ch])]  # columns left to right
    if bold:  # faux bold: each glyph ORed with itself 1 px right (one extra column per glyph)
        cols = [c for ch in text for c in _embolden(list(zip(*g[ch])))]
    while cols and not any(cols[-1]):
        cols.pop()
    while cols and not any(cols[0]):
        cols.pop(0)
    rows_used = [j for j in range(len(cols[0])) if any(c[j] for c in cols)]
    j0, j1 = (rows_used[0], rows_used[-1]) if trim else (0, len(cols[0]) - 1)  # trim=False: one baseline
    e = edge is not None
    s = shadow is not None  # 1-px drop shadow down-right
    w, h = len(cols) + 2 * e + s, j1 - j0 + 1 + 2 * e + s
    x, y, rw, rh = rect
    assert w <= rw + 2 * e and h <= rh, (text, (w, h), rect)  # up to 2 px over: the outline's end columns are cut
    ox = x + ((rw - w) // 2 if align == "center" else 0)
    oy = y + (rh - h + 1) // 2
    on = {(i + e, j - j0 + e) for i, c in enumerate(cols) for j in range(j0, j1 + 1) if c[j]}
    px = img.load()
    for i in range(w):
        if not x <= ox + i < x + rw:
            continue
        for j in range(h):
            if (i, j) in on:
                px[ox + i, oy + j] = lut[ink]
            elif e and any((i + a, j + b) in on for a in (-1, 0, 1) for b in (-1, 0, 1)):
                px[ox + i, oy + j] = lut[edge]
            elif s and (i - 1, j - 1) in on:
                px[ox + i, oy + j] = lut[shadow]
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


def shop():
    """G11 shop labels (FD_SHP.PX row v 0-15): ｶﾞﾝﾎﾞ u96 w32, 個 u128 -> 18 px, 合計 u144 -> u146 w30 (gfx.RECS)."""
    png = "FM16/SHP_labels.png"
    img = Image.open(gfx.GFX / "orig" / png).convert("RGB")
    lut = lut_of(png)
    clear(img, (0, 0) + img.size)
    for rect, t in (((2, 0, 30, 16), "Ganbo"), ((32, 0, 18, 16), "pcs"), ((50, 0, 30, 16), "Total")):
        put_bdf(img, lut, rect, t, "spleen-6x12.bdf", 1, None, trim=False, shadow=13)
    img.save(gfx.GFX / "en" / png)


def _grow(on, r):
    return {(i + a, j + b) for i, j in on for a in range(-r, r + 1) for b in range(-r, r + 1)}


def put_stone(img, lut, rect, text, size, face, edge, shade, font=SANS_B, xs=1.0, ha="c"):
    """Big carved letters: face ramp face[0] (top) .. face[-1] (bottom), 2-px outline `edge`, 3-px drop shadow
    `shade`, in rect (IQ まけ!/かちっ! style), centred or `ha` "l"/"r". xs < 1 condenses to the tall JP proportions."""
    m = mask(text, font, size)
    m = m.resize((max(1, round(m.size[0] * xs)), m.size[1]), Image.LANCZOS)
    on = {(i, j) for j in range(m.size[1]) for i in range(m.size[0]) if m.getpixel((i, j)) > 110}
    ring = _grow(on, 2)
    drop = {(i + 3, j + 3) for i, j in ring}
    w, h = m.size[0] + 7, m.size[1] + 7
    x, y, rw, rh = rect
    assert w <= rw and h <= rh, (text, (w, h), rect)
    ox, oy = x + {"c": (rw - w) // 2, "l": 0, "r": rw - w}[ha] + 2, y + (rh - h) // 2 + 2
    px = img.load()
    for i, j in drop - ring:
        px[ox + i, oy + j] = lut[shade]
    for i, j in ring - on:
        px[ox + i, oy + j] = lut[edge]
    for i, j in on:
        px[ox + i, oy + j] = lut[face[j * len(face) // m.size[1]]]


def iq():
    """G12 IQ battle: hit-and-blow labels (HIT only) and the LOSE! / WIN! cards (HIT + KIO, own CLUTs)."""
    png = "IQ/HIT_labels.png"
    img = Image.open(gfx.GFX / "orig" / png).convert("RGB")
    lut = lut_of(png)
    clear(img, (0, 0) + img.size)
    # row 3 = "Tries [digit]": the digit sprite sits at x 32-47, where あと/回 left a gap
    for rect, t in (((0, 0, 64, 16), "Hit"), ((0, 16, 64, 16), "Blow"), ((0, 32, 32, 16), "Tries")):
        put_bdf(img, lut, rect, t, "spleen-6x12.bdf", 1, 14, align="left")
    img.save(gfx.GFX / "en" / png)
    face = [16, 16, 17, 17, 18, 18, 19, 19, 21]
    for game in ("HIT", "KIO"):
        # WIN and ! are two records that meet at x 16 (かち | っ!): push both to that seam (WIN! seen with a gap)
        for name, t, xs, ha in (("lose", "LOSE!", .58, "c"), ("win1", "WIN", .52, "r"), ("win2", "!", 1, "l")):
            png = f"IQ/{game}_{name}.png"
            img = Image.open(gfx.GFX / "orig" / png).convert("RGB")
            clear(img, (0, 0) + img.size)
            put_stone(img, lut_of(png), (0, 0) + img.size, t, 80, face, 26, 23, xs=xs, ha=ha)
            img.save(gfx.GFX / "en" / png)


def recolor(img, lut, rect, frm, to):
    """Inside rect, pixels of palette indices `frm` become index `to` (wipe text off a bubble, keep its fill)."""
    px = img.load()
    x, y, w, h = rect
    for j in range(y, y + h):
        for i in range(x, x + w):
            if px[i, j] in [lut[k] for k in frm]:
                px[i, j] = lut[to]


def bubbles():
    """G17 OTHER11 speech bubbles: ゴメンネ♥ -> Sorry♥ (the heart stays), バ〜ン -> Bam!"""
    for png, wipe, rect, t in (("YM/O11_sorry.png", (4, 1, 44, 25), (5, 4, 40, 18), "Sorry"),
                               ("YM/O11_bam.png", (2, 2, 34, 28), (3, 6, 30, 18), "Bam!")):
        img = Image.open(gfx.GFX / "orig" / png).convert("RGB")
        lut = lut_of(png)
        recolor(img, lut, wipe, (6, 7), 5)
        put_bdf(img, lut, rect, t, "spleen-6x12.bdf", 7, None, shadow=6)
        img.save(gfx.GFX / "en" / png)
    # G18 ENE09 圏外 (phone "out of range") with furigana -> "No / Signal" on the grey fill (index 13)
    png = "YM/E09_signal.png"
    img = Image.open(gfx.GFX / "orig" / png).convert("RGB")
    lut = lut_of(png)
    recolor(img, lut, (6, 4, 46, 36), (1, 2, 3, 4, 5), 13)
    put_bdf(img, lut, (7, 8, 44, 13), "No", "spleen-6x12.bdf", 3, None, shadow=1, bold=True)
    put_bdf(img, lut, (7, 21, 44, 13), "Signal", "spleen-6x12.bdf", 3, None, shadow=1, bold=True)
    img.save(gfx.GFX / "en" / png)


STS_NAMES = {  # STS_nn.CHG: (player, enemy), glossary / script names
    1: ("Ryujinmaru", "Microwave Ding"), 2: ("Ryujinmaru", "Welcome mashin"), 3: ("Super Funny Cool Squad", "SFX Saurus"),
    4: ("Ryujinmaru", "SFX Saurus"), 5: ("Ryujinmaru", "Animadesk Queen"), 6: ("Ryujinmaru", "Light Search"),
    7: ("Ryujinmaru", "Thunder Tiger"), 8: ("Ryujinmaru", "Electron"), 9: ("Ryujinmaru", "Mr. Illusion"),
    10: ("Ryujinmaru", "Amuler X55"), 11: ("Ryujinmaru", "Gold Medalar"), 12: ("Ryujinmaru", "Shape U2"),
    13: ("Ryujinmaru", "June Brideger"), 14: ("Ryujinmaru", "LL Lovers"), 15: ("Tensho Ryujinmaru", "LL Lovers"),
    16: ("Tensho Ryujinmaru", "QT Koalotter"), 17: ("Tensho Ryujinmaru", "St. Lovely Four"),
    18: ("Tensho Ryujinmaru", "Waruwaru Colossus"),
}


def fit_stone(img, lut, rect, text, size, face, edge, shade):
    """put_stone condensed (never widened) to fit rect's width."""
    w = mask(text, SANS_B, size).size[0]
    put_stone(img, lut, rect, text, size, face, edge, shade, xs=min(1.0, (rect[2] - 7) / w))


def mashin():
    """G19 mashin battle: menu labels (one png, all 18 STS files) and the VS-card names per file."""
    png = "YM/STS_labels.png"
    img = Image.open(gfx.GFX / "orig" / png).convert("RGB")
    lut = lut_of(png)
    clear(img, (0, 0, 32, 32), (0, 32, 48, 32))  # u56+ on rows 0/16 = gauge pips and MP/: kept
    for k, t in enumerate(("Fight", "Heal", "Spirit", "Special")):
        put_bdf(img, lut, (1, 16 * k, 31 if k < 2 else 47, 16), t, "spleen-6x12.bdf", 1, None, align="left",
                trim=False, shadow=14)
    img.save(gfx.GFX / "en" / png)
    face = [15, 14, 13, 12, 11, 10, 9]  # yellow top -> red bottom, outline 3, shadow 1 (the JP names' indices)
    for n, (pl, en) in STS_NAMES.items():
        png = f"YM/STS_{n:02d}_names.png"
        img = Image.open(gfx.GFX / "orig" / png).convert("RGB")
        lut = lut_of(png)
        clear(img, (0, 0, 200, 40), (0, 40, 168, 24), (200, 0, 48, 48))  # player, enemy strip, enemy lead cells
        if n == 3:  # this file's player records: 192x24 at the top (+ small pieces, cleared)
            fit_stone(img, lut, (0, 0, 192, 24), pl, 18, face, 3, 1)
        else:
            fit_stone(img, lut, (0, 0, 200, 40), pl, 30, face, 3, 1)
        fit_stone(img, lut, (0, 40, 168, 24), en, 18, face, 3, 1)
        img.save(gfx.GFX / "en" / png)


def fmenu():
    """G23 field menu / status: every freed glyph row cleared, one English strip per label (gfx.fm_layout), white
    (index 1) with the dark outline (15) like the JP glyphs; ｹﾞﾝﾎﾞ redrawn in place as Ganbo."""
    png = "FM16/STS_atlas.png"
    img = Image.open(gfx.GFX / "orig" / png).convert("RGB")
    lut = lut_of(png)
    clear(img, *[(u, v, w, 16) for u, v, w in gfx.FM_FREE], gfx.FM_GANBO[:2] + (gfx.FM_GANBO[2], 16))
    for en, (u, v, w) in gfx.fm_layout().items():
        assert put_bdf(img, lut, (u, v, w, 16), en, "spleen-6x12.bdf", 1, 15, trim=False)[0] == w, en
    put_bdf(img, lut, gfx.FM_GANBO[:2] + (gfx.FM_GANBO[2], 16), "Ganbo", "spleen-6x12.bdf", 1, 15, trim=False)
    img.save(gfx.GFX / "en" / png)


def put_mono(img, lut, u, v, text, ink, edge, font="spleen-8x16.bdf", rows=(2, 14)):
    """Monospace pixel text at (u, v) with a 1-px 8-neighbour outline: letter i's cell starts at u + 1 + 8 i (no
    column trim, so record x = cell x - 1), font rows rows[0]..rows[1] (one baseline for every strip)."""
    g = bdf(font)
    on = {(1 + 8 * i + c, 1 + j - rows[0]) for i, ch in enumerate(text) for j in range(rows[0], rows[1] + 1)
          for c, b in enumerate(g[ch][j]) if b}
    px = img.load()
    for i in range(8 * len(text) + 2):
        for j in range(rows[1] - rows[0] + 3):
            if (i, j) in on:
                px[u + i, v + j] = lut[ink]
            elif any((i + a, j + b) in on for a in (-1, 0, 1) for b in (-1, 0, 1)):
                px[u + i, v + j] = lut[edge]


def cards():
    """G5 area cards: freed glyph rows cleared, bar B drawn, one white (1) Spleen 8x16 strip per word with the
    darkest outline (15), like the JP glyphs (gfx.sbt_layout / sbt_recs)."""
    png = "OUT/SBT_atlas.png"
    img = Image.open(gfx.GFX / "orig" / png).convert("RGB")
    lut = lut_of(png)
    bu, bv, bw, bh = gfx.SBT_BAR
    clear(img, *[(u, v, w, 16) for u, v, w in gfx.SBT_FREE], gfx.SBT_BAR)
    px = img.load()
    for j in range(bv, bv + bh):  # bar B: the bar's middle column, then its right 4 columns
        for i in range(bw):
            px[bu + i, j] = px[80 - (bw - i) if i >= bw - 4 else 40, j]
    for t, (u, v) in gfx.sbt_layout(gfx.load(gfx.SBT)).items():
        put_mono(img, lut, u, v, t, 1, 15)
    img.save(gfx.GFX / "en" / png)


def line_width(text, size, font=SANS_B):
    return int(ImageFont.truetype(str(font), size).getlength(text)) + 4


def put_line(img, lut, u, v, h, text, size, ramp, font=SANS_B, cut=40):
    """TrueType text at (u, v) on one baseline for every line (top of 'H' 2 px below v), coverage -> ramp."""
    f = ImageFont.truetype(str(font), size)
    w = line_width(text, size, font)
    m = Image.new("L", (w, h))
    ImageDraw.Draw(m).text((2, 2 - f.getbbox("H")[1]), text, font=f, fill=255)
    assert m.crop((0, h - 1, w, h)).getbbox() is None and m.crop((w - 1, 0, w, h)).getbbox() is None, text
    px, mp = img.load(), m.load()
    for j in range(h):
        for i in range(w):
            c = mp[i, j]
            if c > cut:
                px[u + i, v + j] = lut[ramp[min(len(ramp) - 1, (255 - c) * len(ramp) // (256 - cut))]]


def captions():
    """G6 episode captions: the three SUBTTL blocks cleared, one strip per English line (gfx.cap_layout), white
    core (15) easing to the dark brown edge (1) of palette 0, like the JP glyphs."""
    lay = gfx.cap_layout()
    for tp in gfx.CAP_BLK:
        png = f"OUT/SUB_{tp:02X}.png"
        img = Image.open(gfx.GFX / "orig" / png).convert("RGB")
        lut = lut_of(png)
        clear(img, (0, 0) + img.size)
        for t, (tp2, u, v, w) in lay.items():
            if tp2 == tp:
                put_line(img, lut, u, v, gfx.CAP_H, t, gfx.CAP_SIZE, [15, 15, 14, 13, 12, 10, 8, 5, 3, 1])
        img.save(gfx.GFX / "en" / png)


def memcard():
    """G9 memory card: freed rows cleared, one stack of English lines per strip (gfx.mem_layout), white (1) Spleen
    6x12 with the dark drop shadow (14) like the JP glyphs; はい / いいえ / 第 話 redrawn in place."""
    png = "PRG/MEM_atlas.png"
    img = Image.open(gfx.GFX / "orig" / png).convert("RGB")
    lut = lut_of(png)
    clear(img, *[(256 * (tp - 0x0A) + u, v, w, 16) for tp, u, v, w in gfx.MEM_FREE])
    for t, (tp, u, v, w) in gfx.mem_layout(gfx.load(gfx.MEM)).items():
        for i, s in enumerate(t):
            if s:
                r = (256 * (tp - 0x0A) + u, v + 16 * i, w, 16)
                put_bdf(img, lut, r, s, "spleen-6x12.bdf", 1, None, align="left", trim=False, shadow=14)
    for tp, u, v, w, s, al in gfx.MEM_INPLACE:
        x = 256 * (tp - 0x0A) + u
        clear(img, (x, v, w, 16))
        sw = gfx.mem_w(s)
        r = (x, v, w, 16) if al == "c" else (x + al - sw, v, sw, 16)
        put_bdf(img, lut, r, s, "spleen-6x12.bdf", 1, None, align="center", trim=False, shadow=14)
    img.save(gfx.GFX / "en" / png)


BANNER = {  # G20 MBEXT_08 40x40 kanji cells (u, v): English beat (D22). The game flashes them one at a time
    (0, 0): "TO", (40, 0): "RYU", (80, 0): "KEN", (0, 40): "SKY", (40, 40): "SOAR",  # 登龍剣, 天翔 (+登龍剣)
    (128, 0): "PHAN", (168, 0): "TOM", (208, 0): "WYRM", (128, 40): "WAVE", (168, 40): "!!",  # 幻影招龍破
    (0, 128): "RISE", (40, 128): "WYRM", (80, 128): "BLAZE", (0, 168): "FIRE",  # 昇龍烈火
    (40, 168): "BURST", (80, 168): "REND", (0, 208): "HOLY", (40, 208): "SWORD",  # 爆裂聖剣
}


def banners():
    """G20 mashin special-move banners: each kanji cell cleared and redrawn as one carved English word, white-cream
    face over the cell's dark glow colours (palette 7)."""
    png = "YM/MBEXT08_cells.png"
    img = Image.open(gfx.GFX / "orig" / png).convert("RGB")
    lut = lut_of(png)
    for (u, v), t in BANNER.items():
        clear(img, (u, v, 40, 40))
        fit_stone(img, lut, (u, v + 2, 40, 36), t, 24, [14, 14, 14, 13, 13, 12], 4, 1)
    img.save(gfx.GFX / "en" / png)


GROUPS = {"title": title, "battle": battle, "shop": shop, "iq": iq, "bubbles": bubbles, "mashin": mashin,
          "fmenu": fmenu, "cards": cards, "captions": captions, "memcard": memcard,
          "banners": banners}

if __name__ == "__main__":
    for g in sys.argv[1:] or GROUPS:
        GROUPS[g]()
        print("drew", g)
