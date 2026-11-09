"""fontview.py: render a raw glyph blob as a labelled grid PNG. Recon helper.

usage: python -X utf8 tools/fontview.py FILE OUT.png --w 16 --h 16 [--bpp 1|2|4] [--off 0] [--count N] [--cols 32]
       [--msb] [--zoom 2] [--first CODE]   (labels every row with the glyph index / code of its first cell)
"""
import argparse

from PIL import Image, ImageDraw


def glyph_bits(data, off, w, h, bpp, msb):
    row_bytes = (w * bpp + 7) // 8
    px = []
    for y in range(h):
        row = data[off + y * row_bytes: off + (y + 1) * row_bytes]
        vals = []
        for x in range(w):
            bit = x * bpp
            b = row[bit // 8] if bit // 8 < len(row) else 0
            if msb:
                v = (b >> (8 - bpp - bit % 8)) & ((1 << bpp) - 1)
            else:
                v = (b >> (bit % 8)) & ((1 << bpp) - 1)
            vals.append(v)
        px.append(vals)
    return px, row_bytes * h


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("out")
    ap.add_argument("--w", type=int, default=16)
    ap.add_argument("--h", type=int, default=16)
    ap.add_argument("--bpp", type=int, default=1)
    ap.add_argument("--off", type=lambda s: int(s, 0), default=0)
    ap.add_argument("--count", type=int, default=0)
    ap.add_argument("--cols", type=int, default=32)
    ap.add_argument("--msb", action="store_true")
    ap.add_argument("--zoom", type=int, default=2)
    ap.add_argument("--first", type=lambda s: int(s, 0), default=0)
    a = ap.parse_args()
    data = open(a.file, "rb").read()
    _, gsize = glyph_bits(data, 0, a.w, a.h, a.bpp, a.msb)
    n = a.count or (len(data) - a.off) // gsize
    rows = (n + a.cols - 1) // a.cols
    cw, ch, lab = a.w + 2, a.h + 2, 40
    img = Image.new("L", (lab + a.cols * cw, rows * ch), 40)
    d = ImageDraw.Draw(img)
    maxv = (1 << a.bpp) - 1
    for i in range(n):
        px, _ = glyph_bits(data, a.off + i * gsize, a.w, a.h, a.bpp, a.msb)
        gx, gy = lab + (i % a.cols) * cw, (i // a.cols) * ch
        for y in range(a.h):
            for x in range(a.w):
                img.putpixel((gx + x, gy + y), 255 * px[y][x] // maxv if px[y][x] else 0)
        if i % a.cols == 0:
            d.text((1, gy + 2), "%X" % (a.first + i), fill=200)
    img = img.resize((img.width * a.zoom, img.height * a.zoom), Image.NEAREST)
    img.save(a.out)
    print(a.out, n, "glyphs of", gsize, "bytes")


if __name__ == "__main__":
    main()
