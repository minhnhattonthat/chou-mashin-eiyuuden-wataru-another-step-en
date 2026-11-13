"""chg.py: find VRAM-upload blocks in this game's graphics files and render them. Recon helper.

Most .CHG/.PX/.BIN graphics here are (optional typed header chunks) + a chain of uploads, each
`u16 x, y, w, h` (VRAM halfwords) + w*h*2 bytes of data, uncompressed (verified: OUT/CATCH01.CHG CLUT at
0x1078 -> (0,505,256,1), image at 0x1280 -> (896,0,128,256), 8bpp per its 0xC0000322 sprite list).

usage: python -X utf8 tools/chg.py FILE..            list blocks
       python -X utf8 tools/chg.py --render OUTDIR FILE..   one PNG per image block (+ index.tsv)
Depth: 8bpp when the file has a 256-wide CLUT, else 4bpp with its first 16-colour CLUT, else 4bpp grey.
Files with no block chain are rendered raw (4bpp grey, 512 px wide) and reported as `raw`.
--grey8 anywhere in argv: every image block, and raw files, as 8bpp grey (FR*/RxxMy.BIN room atlases, FK/FP).
"""
import struct
import sys
import zlib
from pathlib import Path


def _ok(d, o):
    if o + 8 > len(d):
        return None
    x, y, w, h = struct.unpack_from("<4H", d, o)
    if not (x < 1024 and y < 512 and w and h and x + w <= 1024 and y + h <= 512 and w * h >= 16):
        return None
    end = o + 8 + w * h * 2
    return (x, y, w, h, end) if end <= len(d) else None


def _tail_ok(d, end):
    # chain end: EOF, or only zero padding left (sector / 4-byte alignment)
    return end == len(d) or not d[end:].strip(b"\0")


def blocks(d):
    """Longest-start chains of upload blocks ending at EOF. Returns [(off, x, y, w, h)]."""
    good = {}  # offset -> True if a chain from here reaches the tail

    def valid(o, depth=0):
        if o in good:
            return good[o]
        good[o] = False
        b = _ok(d, o)
        if b and depth < 4000:
            end = b[4]
            good[o] = _tail_ok(d, end) or valid(end, depth + 1)
        return good[o]

    def chain(o):
        out = []
        while True:
            x, y, w, h, end = _ok(d, o)
            out.append((o, x, y, w, h))
            if _tail_ok(d, end):
                return out
            o = end

    # a lone big block can chain to EOF by chance from inside a tile map: the real chain has the most blocks
    best = []
    for o in range(0, len(d) - 8, 2):
        if _ok(d, o) and valid(o):
            c = chain(o)
            if len(c) > len(best):
                best = c
    return best


def _png(path, w, h, rows):
    raw = b"".join(b"\0" + bytes(r) for r in rows)
    def chunk(t, c):
        return struct.pack(">I", len(c)) + t + c + struct.pack(">I", zlib.crc32(t + c))
    Path(path).write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
                          + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))


def _rgb(c):
    return ((c & 31) * 255 // 31, (c >> 5 & 31) * 255 // 31, (c >> 10 & 31) * 255 // 31)


def render(d, blks, out, stem, grey8=False):
    # each image uses the CLUT uploaded last before it (CATCH*, TTL, HIT_MAIN: CLUT, image, CLUT, image...)
    bpp, lut = (8, [(i,) * 3 for i in range(256)]) if grey8 else (4, [(i * 17,) * 3 for i in range(16)])
    rows_out = []
    for i, (o, x, y, w, h) in enumerate(blks):
        if h <= 16 and w in (16, 256):
            bpp = 8 if w == 256 else 4
            lut = [_rgb(c) if c else (40, 0, 40) for c in struct.unpack_from(f"<{w}H", d, o + 8)]
            continue
        data = d[o + 8:o + 8 + w * h * 2]
        pw = w * 2 * (2 if bpp == 4 else 1)
        rows = []
        for r in range(h):
            line = data[r * w * 2:(r + 1) * w * 2]
            px = [n for b in line for n in (b & 15, b >> 4)] if bpp == 4 else list(line)
            rows.append([v for p in px for v in lut[p]])
        name = f"{stem}_{i:02d}.png"
        _png(Path(out) / name, pw, h, rows)
        rows_out.append(f"{name}\t0x{o:X}\t{x},{y},{w},{h}\t{bpp}bpp")
    return rows_out


def render_raw(d, out, stem, grey8=False):
    if grey8:
        w, h = 512, min(len(d) // 512, 1024)
        rows = [[v for b in d[r * w:(r + 1) * w] for v in (b,) * 3] for r in range(h)]
        name = f"{stem}_raw.png"
        _png(Path(out) / name, w, h, rows)
        return [f"{name}\t0x0\traw\t8bpp-grey"]
    w = 256  # bytes per row -> 512 px at 4bpp
    h = min(len(d) // w, 1024)
    rows = [[v for b in d[r * w:(r + 1) * w] for n in (b & 15, b >> 4) for v in (n * 17,) * 3] for r in range(h)]
    name = f"{stem}_raw.png"
    _png(Path(out) / name, w * 2, h, rows)
    return [f"{name}\t0x0\traw\t4bpp-grey"]


def main(argv):
    out = None
    grey8 = "--grey8" in argv  # CLUT-less 8bpp atlases (FR*/RxxMy.BIN room objects)
    argv = [a for a in argv if a != "--grey8"]
    if argv and argv[0] == "--render":
        out = Path(argv[1])
        out.mkdir(parents=True, exist_ok=True)
        argv = argv[2:]
    index = []
    for f in argv:
        d = Path(f).read_bytes()
        blks = blocks(d)
        stem = "_".join(Path(f).with_suffix("").parts[-2:])
        if out is None:
            print(f, "raw" if not blks else "")
            for o, x, y, w, h in blks:
                print(f"  0x{o:06X} ({x},{y}) {w}x{h}")
            continue
        index += render(d, blks, out, stem, grey8) if blks else render_raw(d, out, stem, grey8)
    if out is not None:
        (out / "index.tsv").write_text("\n".join(index) + "\n", encoding="utf-8")
        print(len(index), "images ->", out)


if __name__ == "__main__":
    main(sys.argv[1:])
