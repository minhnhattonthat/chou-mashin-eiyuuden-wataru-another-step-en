"""loadcalls.py: every `jal 0x8002505C` (load file by table index) in a code image, with the index when it is a
constant (addiu a0,zero,N in the delay slot or the instruction before). Recon helper.

usage: python -X utf8 tools/loadcalls.py FILE BASE      (EXE: SLPS_013.68 80017800; overlays: 800D0000 / 800CE000)
"""
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import filetab  # noqa: E402

LOAD = 0x8002505C


def calls(d, base):
    n = len(d) // 4
    w = struct.unpack_from("<%dI" % n, d)
    jal = 0x0C000000 | ((LOAD & 0x0FFFFFFF) >> 2)
    for i in range(n):
        if w[i] != jal:
            continue
        idx = None
        for j in (i + 1, i - 1, i - 2):  # delay slot first
            if 0 <= j < n and w[j] >> 16 == 0x2404:  # addiu a0, zero, imm
                idx = w[j] & 0xFFFF
                break
        yield base + 4 * i, idx


def main():
    f, base = Path(sys.argv[1]), int(sys.argv[2], 16)
    names = {i: nm for i, _, nm, _ in filetab.records((filetab.ROOT / "work/disc/tree/SLPS_013.68").read_bytes())}
    for a, idx in calls(f.read_bytes(), base):
        print("%08X %s %s" % (a, "-" if idx is None else idx, names.get(idx, "")))


if __name__ == "__main__":
    main()
