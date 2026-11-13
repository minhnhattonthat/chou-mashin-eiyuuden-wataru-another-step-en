"""prims.py: GPU sprite packets in a RAM dump (tools/lua/vdump.lua ram.bin) whose CLUT row is Y.

  python -X utf8 tools/prims.py RAM.bin CLUT_Y [--tpage-from RAM]
Prints address, code, x, y, u, v, clut x/16, w, h for every SPRT / SPRT8 / SPRT16 packet (codes 0x64-0x7F) found
by scanning: finds which atlas cells a screen draws and where (the field menu builds its labels per glyph).
"""
import struct
import sys


def prims(r, cy):
    out = []
    for o in range(4, len(r) - 16, 4):
        code = r[o + 3]
        if r[o - 1] not in (3, 4):  # OT tag before the packet: word count 3 (SPRT8/16) or 4 (SPRT)
            continue
        if 0x64 <= code <= 0x7F and code & 0x7C in (0x64, 0x74, 0x7C):
            cl = struct.unpack_from("<H", r, o + 10)[0]
            if cl >> 6 != cy:
                continue
            x, y = struct.unpack_from("<hh", r, o + 4)
            u, v = r[o + 8], r[o + 9]
            if code & 0x7C == 0x64:
                w, h = struct.unpack_from("<HH", r, o + 12)
            else:
                w = h = 8 if code & 0x7C == 0x74 else 16
            out.append((0x80000000 + o, code, x, y, u, v, cl & 0x3F, w, h))
    return out


if __name__ == "__main__":
    r = open(sys.argv[1], "rb").read()
    hits = prims(r, int(sys.argv[2]))
    print(len(hits))
    for a, code, *rest in hits:
        print(hex(a), hex(code), *rest)
