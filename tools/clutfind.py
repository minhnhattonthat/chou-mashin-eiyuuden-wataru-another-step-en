"""clutfind.py: which 4bpp CLUT in a VRAM dump draws an atlas rect the way a screenshot shows it.

  python -X utf8 tools/clutfind.py V.vram.bin PAGE_X,PAGE_Y PX,PY,W,H SHOT.png SX,SY,SW,SH [--top 5]
PAGE_X,PAGE_Y: the 4bpp texture's VRAM origin (halfwords); PX..: atlas rect in 4bpp pixels from that origin;
SHOT rect: where the same glyphs show on screen. Every 16-colour CLUT (x multiple of 16) in VRAM is scored by the
share of the rect's opaque colours that appear (within 24 per channel) on screen, ties broken by colours used.
Prints the best: CLUT x,y and its 16 colours (15-bit hex).
"""
import argparse

import numpy as np
from PIL import Image


def rgb(c):
    return ((c & 31) << 3, (c >> 5 & 31) << 3, (c >> 10 & 31) << 3)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("vram"), ap.add_argument("page"), ap.add_argument("rect"), ap.add_argument("shot")
    ap.add_argument("srect"), ap.add_argument("--top", type=int, default=5)
    a = ap.parse_args()
    v = np.frombuffer(open(a.vram, "rb").read()[:0x100000], "<u2").reshape(512, 1024)
    px0, py0 = map(int, a.page.split(","))
    x, y, w, h = map(int, a.rect.split(","))
    idx = {int(v[py0 + j, px0 + (x + i) // 4] >> (4 * ((x + i) % 4)) & 15) for j in range(y, y + h) for i in range(w)}
    sx, sy, sw, sh = map(int, a.srect.split(","))
    shot = np.array(Image.open(a.shot).convert("RGB"))[sy:sy + sh, sx:sx + sw].reshape(-1, 3).astype(int)
    seen = np.unique(shot, axis=0)
    out = []
    for cy in range(512):
        for cx in range(0, 1024, 16):
            row = v[cy, cx:cx + 16]
            cols = [rgb(int(row[i])) for i in idx if row[i]]
            if len(set(cols)) < 2:
                continue
            hit = sum(np.min(np.max(np.abs(seen - c), axis=1)) <= 24 for c in cols)
            out.append((hit / len(cols), len(set(cols)), cx, cy, row))
    out.sort(key=lambda t: (-t[0], -t[1]))
    print("indices used:", sorted(idx))
    for score, n, cx, cy, row in out[:a.top]:
        print(f"clut ({cx},{cy}) score {score:.2f} colours {n}:", " ".join(f"{int(c):04X}" for c in row))


if __name__ == "__main__":
    main()
