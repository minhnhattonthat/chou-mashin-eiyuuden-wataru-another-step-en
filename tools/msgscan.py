"""msgscan.py: find runs of this game's 16-bit text codes (kana 0x01-0xAD, kanji up to ~0x300) ending in 0x1000/0x2000.

usage: python -X utf8 tools/msgscan.py DIR|FILE [--show K] [--align 2]   Recon helper: counts message-like runs per file.
"""
import struct
import sys
from pathlib import Path

KANA = set(range(0x01, 0xAE))


def scan(data, align=2):
    out = []
    n = len(data) // 2
    hw = struct.unpack_from("<%dH" % n, data)
    i = 0
    while i < n:
        j = i
        k = 0
        while j < n and 1 <= hw[j] < 0x300:
            if hw[j] in KANA:
                k += 1
            j += 1
        if j - i >= 4 and k >= 3 and j < n and hw[j] in (0x1000, 0x2000):
            out.append((i * 2, hw[i:j]))
        i = j + 1
    return out


def main():
    root = Path(sys.argv[1])
    show = int(sys.argv[sys.argv.index("--show") + 1]) if "--show" in sys.argv else 0
    files = [root] if root.is_file() else sorted(p for p in root.rglob("*") if p.is_file())
    for p in files:
        if p.suffix.upper() in (".STR", ".VB", ".XA", ".SEQ", ".VH"):
            continue
        d = p.read_bytes()
        hits = scan(d) + [(o + 1, s) for o, s in scan(d[1:])]
        if hits:
            lo = min(o for o, _ in hits)
            hi = max(o + 2 * len(s) for o, s in hits)
            print(f"{len(hits):6d}  {lo:06X}-{hi:06X}  {p}")
            for o, s in hits[:show]:
                print("        %06X %s" % (o, " ".join("%x" % v for v in s[:16])))


if __name__ == "__main__":
    main()
