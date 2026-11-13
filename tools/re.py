"""re.py: MIPS recon helpers for this game (capstone).

  python -X utf8 tools/re.py consts FILE BASE [--lo HEX --hi HEX]   addresses built by lui + addiu/ori/load/store
  python -X utf8 tools/re.py strrefs FILE BASE                        which 16-bit text runs (msgscan --menu) get a ref

FILE is a raw code image whose offset 0 sits at BASE (PRG overlays 800D0000, rooms 800CE000, FDS 800F7000); for the
EXE pass SLPS_013.68 and BASE 80017800 (header 0x800 bytes before t_addr 0x80018000).
"""
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import msgscan  # noqa: E402


def consts(data, base):
    """Yield (insn_addr, built_addr) for lui rX,hi followed within 16 insns by addiu/ori/lw/sw.. rY,lo(rX)."""
    n = len(data) // 4
    words = struct.unpack_from("<%dI" % n, data)
    for i, w in enumerate(words):
        if w >> 26 != 0x0F:  # lui
            continue
        rt = (w >> 16) & 31
        hi = (w & 0xFFFF) << 16
        for j in range(i + 1, min(i + 17, n)):
            v = words[j]
            op, rs, rt2, imm = v >> 26, (v >> 21) & 31, (v >> 16) & 31, v & 0xFFFF
            if rs == rt and op in (0x09, 0x0D, 0x20, 0x21, 0x23, 0x24, 0x25, 0x28, 0x29, 0x2B):
                lo = imm if op == 0x0D else (imm - 0x10000 if imm & 0x8000 else imm)
                yield base + j * 4, (hi + lo) & 0xFFFFFFFF
            if op == 0 and v & 0x3F == 0x21 and (v >> 11) & 31 == rt and rt in (rs, rt2):
                continue  # addu rX,rX,idx: indexed table, rX still holds the base
            if (op == 0 and (v >> 11) & 31 == rt and v & 0x3F not in (0x08, 0x09)) or (op not in (0, 2, 3, 4, 5, 0x2B, 0x28, 0x29) and rt2 == rt):
                break  # rX overwritten


def main():
    cmd, f, base = sys.argv[1], Path(sys.argv[2]), int(sys.argv[3], 16)
    data = f.read_bytes()
    cs = list(consts(data, base))
    if cmd == "consts":
        lo = int(sys.argv[sys.argv.index("--lo") + 1], 16) if "--lo" in sys.argv else base
        hi = int(sys.argv[sys.argv.index("--hi") + 1], 16) if "--hi" in sys.argv else base + len(data)
        for at, a in cs:
            if lo <= a < hi:
                print(f"{at:08X} -> {a:08X}")
    elif cmd == "strrefs":
        msgscan.ENDS = (0x1000, 0x2000, 0xFFFF, 0x9999, 0x0000)
        runs = msgscan.scan(data)
        targets = {}
        for at, a in cs:
            targets.setdefault(a - base, []).append(at)
        ptrs = set(struct.unpack_from("<%dI" % (len(data) // 4), data))
        hit = 0
        for o, s in runs:
            # a ref may point at the run, or up to 8 bytes before it (header words)
            r = [(k, targets[o - k]) for k in range(0, 10, 2) if o - k in targets]
            p = (base + o) in ptrs
            hit += bool(r or p)
            print(f"{o:06X} len{len(s):4d} {'PTR' if p else '   '} {r[:2] if r else ''}")
        print(f"# {hit}/{len(runs)} runs referenced")


if __name__ == "__main__":
    main()
