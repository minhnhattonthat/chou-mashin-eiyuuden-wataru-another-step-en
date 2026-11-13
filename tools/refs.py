"""refs.py: list every pointer target inside a file range of a menu source, with who points there and the text.

    python -X utf8 tools/refs.py SRC LO HI      e.g.  tools/refs.py BALLBAT 21500 22A70

SRC is a tools/extract.py STREAMS name. Each line: target, its refs (u<file offset> = u32 pointer, c<RAM address> =
lui/addiu in code), then the words up to the next target decoded with the menu codec. Recon helper (phase 4).
"""
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import extract  # noqa: E402
import rooms  # noqa: E402
from jtext import Codec, table  # noqa: E402


def main():
    name, lo, hi = sys.argv[1], int(sys.argv[2], 16), int(sys.argv[3], 16)
    path, base, _ = extract.STREAMS[name]
    data = (extract.TREE / path).read_bytes()
    refs = {}
    for k in range(0, len(data) - 3, 4):
        t = struct.unpack_from("<I", data, k)[0] - base
        if lo <= t < hi:
            refs.setdefault(t, []).append("u%X" % k)
    for k, a in rooms.re_consts(data, base):
        if lo <= a - base < hi:
            refs.setdefault(a - base, []).append("c%X" % k)
    c = Codec(table(), newline=extract.NL)
    ts = sorted(refs)
    for i, t in enumerate(ts):
        e = min(ts[i + 1] if i + 1 < len(ts) else hi, t + 120)
        print("%05X %-30s %s" % (t, ",".join(refs[t][:3]), c.decode(data[t:e]).replace("\n", "|")[:90]))


if __name__ == "__main__":
    main()
