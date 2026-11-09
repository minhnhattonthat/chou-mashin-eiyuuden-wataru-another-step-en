"""peek.py: print a 16-bit LE token stream as text with tbl/jp_common.tbl. Recon helper.

usage: python -X utf8 tools/peek.py FILE OFFSET [COUNT_WORDS=64]
Codes not in the table print as [XXXX]; 1000 -> '/', 2000 -> '|' newline. OFFSET hex.
"""
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load():
    m = {}
    for line in (ROOT / "tbl" / "jp_common.tbl").read_text(encoding="utf-8").splitlines():
        if line and not line.startswith("#"):
            k, v = line.split("=", 1)
            b = bytes.fromhex(k)
            m[b[0] | b[1] << 8] = v
    return m


def render(words, m):
    out = []
    for w in words:
        if w == 0x1000:
            out.append("/")
        elif w == 0x2000:
            out.append("|\n")
        elif w in m:
            out.append(m[w])
        else:
            out.append("[%04X]" % w)
    return "".join(out)


if __name__ == "__main__":
    d = Path(sys.argv[1]).read_bytes()
    off = int(sys.argv[2], 16)
    n = int(sys.argv[3]) if len(sys.argv) > 3 else 64
    n = min(n, (len(d) - off) // 2)
    print(render(struct.unpack_from("<%dH" % n, d, off), load()))
