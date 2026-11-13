"""filetab.py: list the EXE's file table (0x20-byte records: name ptr + 7 words). Recon helper.

usage: python -X utf8 tools/filetab.py [EXE] [--grep TEXT]
Prints index, record address, name and the other words; the index is what file-load calls pass (guess until traced).
"""
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = 0x80017800  # RAM = file offset + BASE


def records(d):
    """Find the table by walking back from the R00.BIN record while entries point at '\\...;1' names."""
    def name(p):
        o = p - BASE
        if not (0x800 <= o < len(d)):
            return None
        e = d.find(b"\0", o)
        s = d[o:e]
        return s.decode("ascii") if s.startswith(b"\\") and s.endswith(b";1") else None

    start = 0x80078880 - BASE
    while name(struct.unpack_from("<I", d, start - 0x20)[0]):
        start -= 0x20
    o = start
    while name(struct.unpack_from("<I", d, o)[0]):
        w = struct.unpack_from("<8I", d, o)
        yield (o - start) // 0x20, o + BASE, name(w[0]), w[1:]
        o += 0x20


def main():
    a = sys.argv[1:]
    grep = None
    if "--grep" in a:
        i = a.index("--grep")
        grep = a[i + 1]
        del a[i:i + 2]
    exe = Path(a[0]) if a else ROOT / "work/disc/tree/SLPS_013.68"
    for i, addr, n, w in records(exe.read_bytes()):
        if grep is None or grep in n:
            print("%4d %08X %-26s %s" % (i, addr, n, " ".join("%08X" % x for x in w)))


if __name__ == "__main__":
    main()
