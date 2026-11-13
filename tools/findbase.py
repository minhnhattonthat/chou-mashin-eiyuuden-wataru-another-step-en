"""findbase.py: guess an overlay's load address from its own 32-bit pointers to its text strings. Recon helper.

usage: python -X utf8 tools/findbase.py FILE [--exe]
For each base B (step 4) among `ptr - start` pairs, counts pointers that land on a string start found by msgscan
(--menu terminators), and prints the best bases with their hit counts, then the pointer-table runs at the best base.
"""
import collections
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import msgscan  # noqa: E402


def starts(d):
    msgscan.ENDS = (0x1000, 0x2000, 0xFFFF, 0x9999, 0x0000)
    return {o for o, _ in msgscan.scan(d)}


def main(argv):
    f = Path(argv[0])
    d = f.read_bytes()
    st = starts(d)
    words = struct.unpack_from("<%dI" % (len(d) // 4), d)
    ptrs = [(i * 4, w) for i, w in enumerate(words) if 0x80010000 <= w < 0x80200000 and not w & 1]
    votes = collections.Counter()
    for _, w in ptrs:
        for s in st:
            b = w - s
            if b & 3 == 0 and 0x80010000 <= b < 0x80200000:
                votes[b] += 1
    best = votes.most_common(5)
    for b, n in best:
        print(f"base 0x{b:08X}: {n} pointers land on string starts")
    if not best:
        return
    b = best[0][0]
    hits = sorted(o for o, w in ptrs if w - b in st)
    runs, cur = [], [hits[0]] if hits else []
    for o in hits[1:]:
        if o - cur[-1] <= 16:
            cur.append(o)
        else:
            runs.append(cur)
            cur = [o]
    if cur:
        runs.append(cur)
    for r in runs:
        print(f"  ptr run file 0x{r[0]:06X}-0x{r[-1] + 4:06X}: {len(r)} pointers")


if __name__ == "__main__":
    main(sys.argv[1:])
