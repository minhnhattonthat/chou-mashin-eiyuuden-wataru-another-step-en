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
# FDS shop total line (FD_SHP.PX, G11): 個 -> "pcs" 18 px, 合計 -> "Total" moved 2 px right in the atlas
RECS += [
    ("FPRG/FDS.BIN", 0x171C6, REC, (0x0C, 0x784D, 144, 0, 32, 16, -32, 8), (0x0C, 0x784D, 146, 0, 30, 16, -32, 8),
     "shop Total"),
    ("FPRG/FDS.BIN", 0x171D4, REC, (0x0C, 0x784D, 128, 0, 16, 16, -56, 8), (0x0C, 0x784D, 128, 0, 18, 16, -56, 8),
     "shop pcs"),
]


# G23 field menu / status labels (FM16/FD_STS.BIN glyph sheet, tpage 0x0C, docs/re/graphics.md G23): each label is a
# run of FDS.BIN sprite records, one per JP glyph or word. The English goes into one strip of the freed glyph rows
# (FM_FREE, laid out by fm_layout), the label's leftmost record cuts the strip and the rest get w = h = 0.
FDS = "FPRG/FDS.BIN"
FM_FREE = [(0, 8, 120), (0, 24, 120), (0, 40, 120), (0, 56, 120), (0, 72, 120), (0, 88, 80), (0, 104, 72),
           (176, 152, 64), (0, 168, 256), (0, 184, 256), (0, 200, 208), (0, 216, 256), (0, 232, 224)]  # u, v, w; 16 tall
FM_K8 = {8: "あいうえおかきくけこさしすせそ", 24: "たちつてとなにぬねのはひふへほ", 40: "まみむめもやMゆPよらりるれろ",
         56: "わをんゃ_ゅ_ょぁぃぅぇぉっー", 72: "がぎぐげござじずぜぞだぢづでど", 88: "ばびぶべぼぱぴぷぺぽ", 104: "ランクタイプレベル"}
FM_K16 = {152: "...........第話最終：", 168: "炎部ワタル剣部アラゴト忍部サクヤ", 184: "ワルリーヌ回復攻撃・補助経験値の",
          200: "他アイテムそうびもんペット$$", 216: "ステータスコンフィグ気合装備属性", 232: "つかせいりペン超必殺技こたカ□",
          120: "....了"}
# (JP the records spell in (y, x) order, English, record offsets, x of the English: None = leftmost record's x,
#  "c" = centred on 0 (button titles), or an int; colon record moved to the English's right end, or None)
_NAMES = [("炎部ワタル", "Wataru", 0x12568, 0x142A6, 0x1506C), ("剣部アラゴト", "Aragoto", 0x126C8, 0x143CE, 0x151BC),
          ("忍部サクヤ", "Sakuya", 0x12828, 0x144F6, 0x1530C), ("ワルリーヌ", "Warurine", 0x12988, 0x1461E, 0x1545C)]
FM_LABELS = [(jp, en, [o], None, None) for jp, en, *offs in _NAMES for o in offs]
_MENU = [("アイテム", "Item", 0x12B04, 0x12D9C), ("そうび", "Equip", 0x12AF6, 0x12DF0),
         ("もんペット", "Monpet", 0x12AE8, 0x12E44), ("ステータス", "Status", 0x12ADA, 0x12E98),
         ("コンフィグ", "Config", 0x12ACC, 0x12EEC)]
FM_LABELS += [(jp, en, [lst], None, None) for jp, en, lst, _ in _MENU]  # field menu list
FM_LABELS += [(jp, en, [btn], "c", None) for jp, en, _, btn in _MENU]  # window title buttons
FM_LABELS += [
    ("第話", "Ep.", [0x12BA0, 0x12B92], -27, None),  # 第 [episode digits] 話: the frame is a fixed 64 px
    ("最終話", "Final", [0x12BE6, 0x12BD8], "c", None),
    ("つかう", "Use", [0x12F4E, 0x12F40], "c", None),
    ("せいり", "Sort", [0x12F88], "c", None),
    ("イペント", "Key Items", [0x12FDC, 0x12FCE, 0x12FC0], "c", None),
    ("回復", "Heal", [0x1303E, 0x13030], "c", None),  # item tabs
    ("攻撃", "Attack", [0x1306A, 0x1305C], "c", None),
    ("攻撃補助", "Support", [0x13096, 0x13088], "c", None),
    ("その他", "Other", [0x130D0, 0x130C2, 0x130B4], "c", None),
    ("回復", "Heal", [0x140B8, 0x140AA], None, None),  # item list headings
    ("攻撃", "Attack", [0x14138, 0x1412A], None, None),
    ("攻撃・補助", "Support", [0x141E2, 0x141D4, 0x141C6, 0x141B8, 0x141AA], None, None),
    ("その他", "Other", [0x1426E, 0x14260, 0x14252], None, None),
    ("ちから", "Strength", [0x14C18, 0x14C0A, 0x14BFC], None, None),  # status / equip stat column
    ("かしこさ", "Wisdom", [0x14BEE, 0x14BE0, 0x14BD2, 0x14BC4], None, None),
    ("がんじょうさ", "Toughness", [0x14BB6, 0x14BA8, 0x14B9A, 0x14B8C, 0x14B7E, 0x14B70], None, None),
    ("がまんづよさ", "Endurance", [0x14B62, 0x14B54, 0x14B46, 0x14B38, 0x14B2A, 0x14B1C], None, None),
    ("すばやさ", "Speed", [0x14B0E, 0x14B00, 0x14AF2, 0x14AE4], None, None),
    ("こうげき", "Attack", [0x14AD6, 0x14AC8, 0x14ABA, 0x14AAC], None, None),
    ("ぼうぎょ", "Defense", [0x14A9E, 0x14A90, 0x14A82, 0x14A74], None, None),
    ("とくしゅこうげき", "Sp. Attack", [0x14A66, 0x14A58, 0x14A4A, 0x14A3C, 0x14A2E, 0x14A20, 0x14A12, 0x14A04],
     None, None),  # 72 px to the value column (D20)
    ("とくしゅぼうぎょ", "Sp. Defense", [0x149F6, 0x149E8, 0x149DA, 0x149CC, 0x149BE, 0x149B0, 0x149A2, 0x14994],
     None, None),
    ("かいひ", "Evasion", [0x14986, 0x14978, 0x1496A], None, None),
    ("ゆうき", "Valor", [0x1495C, 0x1494E, 0x14940], None, None),
    ("気合い", "Spirit", [0x14932, 0x148FA], None, None),
    ("必殺技", "Special", [0x14D30], None, None),
    ("超必殺技", "Super Special", [0x14D4C], None, None),
    ("げんざいのレベル", "Level", [0x14F54, 0x14F46, 0x14F38, 0x14F2A, 0x14F1C, 0x14F0E], None, None),
    ("経験値", "Experience", [0x14EAC, 0x14E9E, 0x14E90], None, None),
    ("つぎのレベルまで", "Next Level", [0x14F00, 0x14EF2, 0x14EE4, 0x14ED6, 0x14EC8, 0x14EBA], None, None),
] + [("装備：", "Equipment", [o], None, o - 14) for o in (0x15088, 0x151D8, 0x15328, 0x15478)] + [
    ("属性：", "Element", [0x1619A], -107, 0x1618C),  # monpet detail; the element value starts 2 px after the colon
    ("げんざいのランク：", "Current Rank", [0x1612A, 0x16138, 0x16146, 0x16154, 0x16162, 0x16170], -1, 0x1617E),
    ("攻撃カ", "Power", [0x1635A, 0x1634C], None, None),
    ("しょうひMP", "MP Cost", [0x1633E, 0x16330, 0x16322, 0x16314, 0x16306, 0x162F8], None, None),
    ("必殺技", "Special", [0x162EA], None, None),
    ("必殺技タイプ", "Special Type", [0x162DC, 0x162CE], None, None),
    ("こうたい", "Swap", [0x1649E, 0x16490, 0x16482, 0x16474], "c", None),
    ("終了", "Exit", [0x179CA, 0x179BC], None, None),
]
FM_GANBO = (208, 200, 32)  # ｹﾞﾝﾎﾞ money unit (record 0x12C2E): redrawn in place
FM_BLANK = [0x13188, 0x13196, 0x131A4, 0x131B2]  # spacers cutting the empty cell (32, 56): w = h = 0
FM_SHOP = (0x16E00, 0x17700)  # shop records: they cut FD_SHP.PX, swapped into the same VRAM (G11)


def fm_char(u, v, w, h):
    """JP the FD_STS cell rect (u, v, w, h) shows, None outside the glyph rows."""
    for k, s, cw in [(k, s, 8) for k, s in FM_K8.items()] + [(k, s, 16) for k, s in FM_K16.items()]:
        if v == k and h == 16 and (cw == 16 or u < 120):
            return "".join(s[c] if c < len(s) else "?" for c in range(u // cw, (u + w + cw - 1) // cw))
    return None


def fm_layout():
    """{English: (u, v, w)}: first fit, longest first, into FM_FREE (widths from gfx_gen's outlined Spleen 6x12)."""
    import gfx_gen
    free = [list(f) for f in FM_FREE]
    out = {}
    for en in sorted({lab[1] for lab in FM_LABELS}, key=lambda t: (-gfx_gen.bdf_width(t), t)):
        w = gfx_gen.bdf_width(en)
        f = next(f for f in free if f[2] >= w)  # StopIteration = atlas full
        out[en] = (f[0], f[1], w)
        f[0] += w
        f[2] -= w
    return out


def fm_recs(d):
    """gfx.RECS-style entries for the G23 labels, checked against the original FDS.BIN bytes `d`."""
    lay = fm_layout()
    out = []
    for jp, en, offs, xpos, colon in FM_LABELS:
        recs = {o: struct.unpack_from(REC, d, o) for o in offs}
        assert all(r[0] == 0x0C and r[1] in (0x784D, 0x784C) for r in recs.values()), (en, "not an FD_STS record")
        spelt = "".join(fm_char(*r[2:6]) or "?" for r in sorted(recs.values(), key=lambda r: (r[7], r[6])))
        assert spelt + ("：" if colon else "") == jp, (en, spelt, jp)
        u, v, w = lay[en]
        lead = min(recs, key=lambda o: (recs[o][6], recs[o][7]))
        tp, cl, _, _, _, _, x, y = recs[lead]
        x = -(w // 2) if xpos == "c" else x if xpos is None else xpos
        for o, r in recs.items():
            new = (tp, cl, u, v, w, 16, x, y) if o == lead else r[:4] + (0, 0) + r[6:]
            out.append((FDS, o, REC, r, new, "fmenu " + en))
        if colon:
            r = struct.unpack_from(REC, d, colon)
            assert fm_char(*r[2:6]) == "：", (en, "colon")
            out.append((FDS, colon, REC, r, r[:6] + (x + w - 1, r[7]), "fmenu colon " + en))
    for o in FM_BLANK:
        r = struct.unpack_from(REC, d, o)
        assert fm_char(*r[2:6]) == "_", hex(o)
        out.append((FDS, o, REC, r, r[:4] + (0, 0) + r[6:], "fmenu blank"))
    return out


def fm_check(d):
    """Every FD_STS record in FDS.BIN that cuts a freed glyph row is one fm_recs rewrites (else it would show
    English pieces): returns the offsets of the strays."""
    done = {o for lab in FM_LABELS for o in lab[2]} | set(FM_BLANK)
    stray = []
    for o in range(0, len(d) - 14, 2):
        tp, cl, u, v, w, h, x, y = struct.unpack_from(REC, d, o)
        if tp != 0x0C or cl not in (0x784D, 0x784C) or not (0 < w <= 256 and 0 < h <= 64) or o in done or \
                FM_SHOP[0] <= o < FM_SHOP[1]:
            continue
        if any(u < fu + fw and fu < u + w and v < fv + 16 and fv < v + h for fu, fv, fw in FM_FREE):
            stray.append(o)
    return stray


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
    for path, off, fmt, old, new, why in RECS + fm_recs(orig[load_path(FDS)]):
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
    out += [(off, off + struct.calcsize(fmt)) for p, off, fmt, *_ in RECS + fm_recs(load(FDS)) if p == path]
    return out


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "export":
        export(set(a[1:]))
    elif a and a[0] == "show":
        f, off, bpp, cf, coff, pal, out = a[1:8]
        coff = -int(coff[1:], 16) - 1 if coff.startswith("r") else int(coff, 16)
        image(load(f), int(off, 16), int(bpp), palette(load(cf), coff, int(pal), int(bpp))).save(out)
    else:
        print(__doc__)
