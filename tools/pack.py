"""pack.py: shelf-pack PNGs of mixed sizes into pages (sheet.py gives every tile the largest image's size).

usage: python tools/pack.py OUT_PREFIX PNG.. [--page 1600]
Writes OUT_PREFIX_N.png pages and OUT_PREFIX.tsv (page, x, y, w, h, file) to find a tile's source.
"""
import sys
from pathlib import Path

from PIL import Image


def main(argv):
    page = 1600
    if "--page" in argv:
        i = argv.index("--page")
        page = int(argv[i + 1])
        del argv[i:i + 2]
    prefix, files = Path(argv[0]), argv[1:]
    imgs = sorted(((Image.open(f).convert("RGB"), f) for f in files), key=lambda t: -t[0].height)
    pages, rows, n = [], [], 0
    x = y = shelf = 0
    cur = Image.new("RGB", (page, page), (0, 0, 0))
    for im, f in imgs:
        w, h = min(im.width, page), min(im.height, page)
        if x + w > page:
            x, y, shelf = 0, y + shelf + 2, 0
        if y + h > page:
            pages.append(cur)
            cur, x, y, shelf = Image.new("RGB", (page, page), (0, 0, 0)), 0, 0, 0
        cur.paste(im, (x, y))
        rows.append(f"{len(pages) + 1}\t{x}\t{y}\t{w}\t{h}\t{Path(f).name}")
        x, shelf = x + w + 2, max(shelf, h)
    pages.append(cur)
    for i, p in enumerate(pages, 1):
        bb = p.getbbox() or (0, 0, 1, 1)
        p.crop((0, 0, bb[2], bb[3])).save(f"{prefix}_{i}.png")
    Path(f"{prefix}.tsv").write_text("\n".join(rows) + "\n", encoding="utf-8")
    print(len(pages), "pages ->", prefix)


if __name__ == "__main__":
    main(sys.argv[1:])
