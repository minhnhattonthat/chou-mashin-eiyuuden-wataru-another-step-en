"""Relocation: every original reference (aligned u32, lui + lo) to a text entry follows it to its new address, no
reference is left inside a vacated slot, and the bytes after a non-entry target travel along (pipeline §Checks).
Files with text: the EXE, PRG overlays (strpack), FDS and the room overlays (roompack); EXE entries are also
checked against references from every other code file (overlays read EXE strings)."""
import struct
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import insert  # noqa: E402
import roompack  # noqa: E402
import rooms  # noqa: E402
import strpack  # noqa: E402

pytestmark = pytest.mark.skipif(not (insert.TREE / "SLPS_013.68").exists(), reason="disc not unpacked")

BASE = {**strpack.BASE, "PRG/ST.BIN": 0x800D0000, "PRG/LVUP.BIN": 0x800D0000, "FPRG/FDS.BIN": 0x800F7000,
        **{f"FPRG/{n}.BIN": rooms.BASE for n in rooms.OVERLAYS},
        **{f"YM/BR_02/ENE{i:02d}.BIN": insert.ENE_BASE for i in range(1, 19)}}
OTHER = {p: 0x800D0000 for p in ("PRG/MEMORY.BIN", "PRG/SBTTL.BIN", "PRG/MOVIE.BIN")}
# u32 values that look like room addresses but are actor-record fields [u32 xy, u32 0x80xx0218, u32 0xD5]
# (R08 has 0x80110218 / 0x80070218 in the same column): not pointers.
NOT_PTR = {("FPRG/R02.BIN", 0x12218), ("FPRG/R08.BIN", 0x22218),
           ("SLPS_013.68", 0x8102A),  # 0x8005C060: sh loop writing 24 u16 downward from 0x8009882A (ends below POS)
           # Table bases that land inside a string; a read watch of each in battle_ball/battle_menu (work/qa/p7/rdA,
           # rdB, 2026-11-14) saw no access:
           ("PRG/BALLBAT.BIN", 0x21C1C),  # 0x800E1730: [u32 cells, u32 ptr] records at base + 8*idx, idx >= 1 (0x21C24+)
           ("PRG/BALLBAT.BIN", 0x252E8)}  # 0x800E5EAC: lhu base + 12*i + 4*j (i = byte 0x800F2DE1, j = 0x8009C726)


def refs(data, base):
    """[(kind, at, target address)]: aligned u32 in [base, base + len) and every lui + lo pair (re.pairs)."""
    out = [("u32", k, v) for k in range(0, len(data) - 3, 4)
           if base <= (v := struct.unpack_from("<I", data, k)[0]) < base + len(data)]
    out += [("lui", (lui - base, lo - base), a) for lui, lo, a in strpack._mipsre.pairs(data, base)]
    return out


def value(data, kind, at):
    """The address a reference holds in `data` now."""
    if kind == "u32":
        return struct.unpack_from("<I", data, at)[0]
    hi_w, lo_w = struct.unpack_from("<I", data, at[0])[0], struct.unpack_from("<I", data, at[1])[0]
    lo = lo_w & 0xFFFF
    if lo_w >> 26 != 0x0D and lo & 0x8000:
        lo -= 0x10000
    return ((hi_w & 0xFFFF) << 16) + lo & 0xFFFFFFFF


def layout(built):
    """{path: ({old entry offset: new offset}, [(old start, old end)] of moved entries)}."""
    out = {}
    for e, path, off, words, avail, nl, ctx in insert.entries():
        new, moved = out.setdefault(path, ({}, []))
        at = next((o for o, _, _, by in insert.WRITES.get(path, []) if by == e["id"]), off)
        new[off] = at
        if at != off:
            moved.append((off, off + 2 * avail))
    return out


def test_references_follow_entries(built):
    bad = []
    lay = layout(built)
    for path, (new, moved) in lay.items():
        base, orig = BASE[path], (insert.TREE / path).read_bytes()
        now = built.get(path, orig)
        starts = sorted(new)
        aimed = {o + i for o, _, d, by in insert.WRITES.get(path, [])
                 if " ptr " in f" {by}" or by.endswith(" cells") or by.startswith("code strip") or
                 by.startswith("strip ") or by.startswith("gfx rec ") or by == "name grid" for i in range(len(d))}
        patched = {o for o, _, _, by in insert.WRITES.get(path, []) if by.startswith("code ")}
        slots = [s for s in moved]
        slots += [(o, o + 2 * av) for e, p, o, w, av, *_ in insert.entries() if p == path and (o, o + 2 * av) not in moved]
        units = [(u["start"], u["end"]) for u in roompack.units(Path(path).stem)] if path.startswith("FPRG/R") else []
        for kind, at, a in refs(orig, base):
            t = a - base
            if not 0 <= t < len(orig) or (path, t) in NOT_PTR:
                continue
            if kind == "u32" and any(lo <= at < hi for lo, hi in units):
                continue  # words of a room text unit that happen to read as an address (R13 `A000 800D`)
            if kind == "lui" and set(at) & patched:
                continue  # an instruction the build patches on purpose (insert.CODE, strip list/count immediates)
            v = value(now, kind, at)
            host = next((s for s in slots if s[0] < t < s[1]), None)
            if t in new:
                if v != base + new[t]:
                    bad.append(f"{path} {kind} {at}: {a:X} -> {v:X}, entry now at {base + new[t]:X}")
            elif host and (host in moved or now[host[0]:t] != orig[host[0]:t]):
                # a reader starting mid-string: fine only while the cells before it are unchanged (a kept blank)
                bad.append(f"{path} {kind} {at}: {a:X} points inside entry {host[0]:X}")
            elif not host:  # not an entry: whatever it points at must be there still (data travelling with a room
                # unit), except record fields the build rewrites on purpose (re-aimed pointers, cell counts, strips)
                nxt = min([s for s in starts if s > t] + [t + 16, len(orig)])
                n, w = nxt - t, v - base
                if not 0 <= w <= len(now) - n or any(now[w + i] != orig[t + i] for i in range(n)
                                                     if w + i not in aimed):
                    bad.append(f"{path} {kind} {at}: {a:X} -> {v:X}, bytes there changed")
    assert not bad, (len(bad), bad[:10])


def test_exe_strings_have_no_reader_left_in_other_files(built):
    """Overlays and ENE files read EXE strings by absolute address: any reference to a moved EXE entry is re-aimed."""
    new, moved = layout(built)[insert.EXE]
    base = BASE[insert.EXE]
    old = {base + o: base + n for o, n in new.items() if o != n}
    bad = []
    for path, pbase in {**BASE, **OTHER}.items():
        if path == insert.EXE:
            continue
        orig = (insert.TREE / path).read_bytes()
        now = built.get(path, orig)
        for kind, at, a in refs(orig, pbase) + [("u32", k, struct.unpack_from("<I", orig, k)[0])
                                               for k in range(0, len(orig) - 3, 4)]:
            if a in old and value(now, kind, at) != old[a]:
                bad.append(f"{path} {kind} {at}: still {a:X} (moved to {old[a]:X})")
            elif any(base + lo < a < base + hi for lo, hi in moved):
                bad.append(f"{path} {kind} {at}: {a:X} inside a moved EXE entry")
    assert not bad, (len(bad), bad[:10])


def test_roompack_invariants():
    roompack.selftest()
