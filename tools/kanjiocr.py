"""kanjiocr.py: first-guess OCR of 16x16 4bpp font glyphs by template matching against Windows Japanese fonts.

Each glyph's ink (colour indices other than 0 and the 0xE drop shadow) is cropped to its bounding box and scaled to
NxN; every JIS X 0208 character is rendered the same way in MS Gothic and Yu Gothic; cosine similarity ranks them.
A guess, not a reading: confirm with the decoded script (context) and a zoomed sheet.

usage: python -X utf8 tools/kanjiocr.py FONT.BIN --first GLYPH --count N [--label-base CODE] [--top 5] [--test]
  --test   score the method on MSG_CG kana (known codes) and the verified kanji, then exit
Output: one line per glyph: code<TAB>best<TAB>score<TAB>top-k
"""
import argparse
import functools
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
FONTS = [r"C:\Windows\Fonts\msgothic.ttc", r"C:\Windows\Fonts\YuGothM.ttc"]
N = 24
BLUR = 1.0
SHADOW = 14


def glyph(data, i):
    o = i * 128
    a = np.zeros((16, 16), np.float32)
    for y in range(16):
        for x in range(16):
            v = (data[o + y * 8 + x // 2] >> (4 * (x & 1))) & 15
            # palette: 1 = brightest ink, 2-0xD antialias toward the shadow colour, 0xE = drop shadow
            a[y, x] = 0.0 if v in (0, SHADOW) else (14 - v) / 13.0
    return a


def norm(img):
    """img: float array, ink high. Crop to bbox, pad short side to keep thin glyphs thin, resize to NxN, unit vector."""
    ys, xs = np.nonzero(img > 0.2)
    if len(ys) == 0:
        return None
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    crop = img[y0:y1, x0:x1]
    h, w = crop.shape
    s = max(h, w)
    # keep aspect only for clearly thin glyphs (一, ｜); square kanji are stretched to fill
    if min(h, w) < s * 0.5:
        pad = np.zeros((s, s), np.float32)
        pad[(s - h) // 2:(s - h) // 2 + h, (s - w) // 2:(s - w) // 2 + w] = crop
        crop = pad
    im = Image.fromarray((np.clip(crop, 0, 1) * 255).astype(np.uint8)).resize((N, N), Image.BILINEAR)
    if BLUR:
        from PIL import ImageFilter
        im = im.filter(ImageFilter.GaussianBlur(BLUR))
    v = np.asarray(im, np.float32).ravel()
    v -= v.mean()
    n = np.linalg.norm(v)
    return v / n if n else None


def charset():
    out = []
    for hi in range(0x81, 0xF0):
        for lo in list(range(0x40, 0x7F)) + list(range(0x80, 0xFD)):
            try:
                ch = bytes([hi, lo]).decode("cp932")
            except UnicodeDecodeError:
                continue
            if len(ch) == 1 and (0x3040 <= ord(ch) <= 0x30FF or 0x4E00 <= ord(ch) <= 0x9FFF or 0xFF01 <= ord(ch) <= 0xFF5E
                                 or ch in "々〆ヶ○×△□◎☆★"):
                out.append(ch)
    return sorted(set(out))


@functools.lru_cache(None)
def templates():
    cache = ROOT / "work" / "ocr_templates.npz"
    if cache.exists():
        z = np.load(cache, allow_pickle=False)
        return list(z["chars"]), z["mat"]
    chars, rows = [], []
    for path in FONTS:
        font = ImageFont.truetype(path, 64)
        for ch in charset():
            im = Image.new("L", (80, 80), 0)
            ImageDraw.Draw(im).text((8, 8), ch, font=font, fill=255)
            # down to glyph scale then back, so stroke weight resembles a 16 px bitmap
            small = im.resize((20, 20), Image.BOX)
            v = norm(np.asarray(small, np.float32) / 255.0)
            if v is not None:
                chars.append(ch)
                rows.append(v)
    mat = np.stack(rows)
    cache.parent.mkdir(exist_ok=True)
    np.savez(cache, chars=np.array(chars), mat=mat)
    return chars, mat


def rank(g, top=5):
    chars, mat = templates()
    v = norm(g)
    if v is None:
        return []
    sc = mat @ v
    best = {}
    for i in np.argsort(-sc):
        ch = chars[i]
        if ch not in best:
            best[ch] = float(sc[i])
            if len(best) == top:
                break
    return list(best.items())


def test():
    import sys
    sys.path.insert(0, str(ROOT / "tools"))
    from mktbl import ROWS
    d = (ROOT / "work/disc/tree/FM16/MSG_CG.BIN").read_bytes()
    known = {}
    for first, s in ROWS:
        for i, ch in enumerate(s):
            known[first + i] = ch
    known.update({0x10E: "一", 0x176: "忍", 0x18D: "部"})
    ok = top5 = 0
    for code, ch in known.items():
        r = rank(glyph(d, code + 0xA6))
        hits = [c for c, _ in r]
        ok += bool(hits) and hits[0] == ch
        top5 += ch in hits
        if not hits or hits[0] != ch:
            print("%04X %s -> %s" % (code, ch, " ".join("%s%.2f" % x for x in r)))
    print("top1 %d/%d top5 %d" % (ok, len(known), top5))


def sheet(data, first, count, label_base, out, cols=16, zoom=4):
    """Black-on-white sheet (shadow dropped) with the code above every cell, for reading kanji by eye."""
    cw, chh = 16 * zoom + 8, 16 * zoom + 14
    rows = (count + cols - 1) // cols
    img = Image.new("L", (cols * cw, rows * chh), 255)
    dr = ImageDraw.Draw(img)
    for k in range(count):
        g = glyph(data, first + k)
        cell = Image.fromarray((255 - g * 255).astype(np.uint8)).resize((16 * zoom, 16 * zoom), Image.NEAREST)
        x, y = (k % cols) * cw, (k // cols) * chh
        img.paste(cell, (x + 4, y + 12))
        dr.text((x + 4, y), "%X" % (label_base + k), fill=0)
    img.save(out)
    print(out, count)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("font", nargs="?")
    ap.add_argument("--sheet", help="write a labelled PNG instead of guesses")
    ap.add_argument("--cols", type=int, default=16)
    ap.add_argument("--zoom", type=int, default=4)
    ap.add_argument("--first", type=lambda s: int(s, 0), default=0)
    ap.add_argument("--count", type=lambda s: int(s, 0))
    ap.add_argument("--label-base", type=lambda s: int(s, 0), default=0, help="code printed = label-base + (i - first)")
    ap.add_argument("--top", type=int, default=5)
    ap.add_argument("--test", action="store_true")
    a = ap.parse_args()
    if a.test:
        return test()
    d = Path(a.font).read_bytes()
    count = a.count if a.count is not None else len(d) // 128 - a.first
    if a.sheet:
        return sheet(d, a.first, count, a.label_base, a.sheet, a.cols, a.zoom)
    for k in range(count):
        r = rank(glyph(d, a.first + k), a.top)
        if r:
            print("%04X\t%s\t%.3f\t%s" % (a.label_base + k, r[0][0], r[0][1], " ".join("%s%.2f" % x for x in r[1:])))
        else:
            print("%04X\t\t0\t(blank)" % (a.label_base + k))


if __name__ == "__main__":
    main()
