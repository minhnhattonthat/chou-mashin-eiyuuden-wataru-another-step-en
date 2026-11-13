"""vram.py: render a PS1 VRAM dump (1024x512 x 16-bit) to PNG.

  python -X utf8 tools/vram.py V.vram.bin OUT.png [--mode 4|16] [--zoom N] [--crop x,y,w,h]
--mode 4: every halfword as 4 grey 4bpp pixels (4096 px wide; crop x/w in those pixels). --mode 16: 15-bit colour.
"""
import argparse
import numpy as np
from PIL import Image


def render(raw, mode):
    v = np.frombuffer(raw[:0x100000], "<u2").reshape(512, 1024)  # this Redux build returns 2 MB; the 2nd half isn't VRAM
    if mode == 16:
        r, g, b = (v & 31) << 3, ((v >> 5) & 31) << 3, ((v >> 10) & 31) << 3
        return Image.fromarray(np.dstack([r, g, b]).astype(np.uint8))
    px = np.stack([(v >> s) & 15 for s in (0, 4, 8, 12)], axis=-1).reshape(512, 4096)
    return Image.fromarray((px * 17).astype(np.uint8))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("vram"), ap.add_argument("out")
    ap.add_argument("--mode", type=int, default=4)
    ap.add_argument("--zoom", type=int, default=1)
    ap.add_argument("--crop")
    a = ap.parse_args()
    im = render(open(a.vram, "rb").read(), a.mode)
    if a.crop:
        x, y, w, h = map(int, a.crop.split(","))
        im = im.crop((x, y, x + w, y + h))
    if a.zoom > 1:
        im = im.resize((im.width * a.zoom, im.height * a.zoom), Image.NEAREST)
    im.save(a.out)
