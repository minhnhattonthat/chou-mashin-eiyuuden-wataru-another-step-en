"""strpack.py: move English strings that outgrow their JP slot in the EXE and the PRG overlays (docs/re/text.md).

A unit is one string, or a page chain (EXE dialogue: a page and the `next` pages that follow it). A unit whose
English is longer than its slot is written to free space and every reference to each of its entries is re-aimed:
aligned u32 slots holding the entry's address ([u32 cells, u32 ptr] records, pointer tables) and lui + lo pairs
that build it (both immediates patched; a lui shared with another address refuses). Terminators and bytes between
chained pages travel with the unit; a count-drawn string (`len_at`) has none.
Free space (FREE): past the overlay's end up to the first address the overlay itself uses (trap-tested in battle,
docs/re/files.md), or for the EXE the zero run after the compose hook plus the old slots of the units that moved.
"""
import struct
import sys
from collections import defaultdict
from pathlib import Path
import importlib.util

sys.path.insert(0, str(Path(__file__).parent))
import compose  # noqa: E402
import rooms  # noqa: E402

_spec = importlib.util.spec_from_file_location("mipsre", Path(__file__).parent / "re.py")
_mipsre = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mipsre)

BASE = {"SLPS_013.68": 0x80017800, "PRG/ST.BIN": 0x800D0000, "PRG/BALLBAT.BIN": 0x800D0000,
        "PRG/MACHINE.BIN": 0x800D0000, "PRG/TTL.BIN": 0x800D0000}
# RAM end of the space past each overlay (first address the overlay's code builds past its end; ST: the font).
# Not TTL: strings past its end froze the title on the logo (BSS expected zero, 2026-11-14), so it uses holes only.
TAIL_END = {"PRG/ST.BIN": 0x80110000, "PRG/BALLBAT.BIN": 0x80109800, "PRG/MACHINE.BIN": 0x800F206C}
POOL = {"PRG/TTL.BIN"}  # one run of u32-table strings: re-laid back to back
EXE_FREE = (compose.HOOK + 4 * len(compose.hook_words()), 0x80098C40)  # rest of the EXE zero run
PAGE_TERMS = {0x2000, 0x3000, 0x4000, 0x5000, 0x6000, 0x7000, 0x8000, 0xA000, 0xC000, 0xD000, 0xE000, 0xF000}


def refs(data, base):
    """({offset: [u32 slot offsets]}, {offset: [(lui offset, lo offset)]}, {lui offset: {built addresses}})."""
    u32 = defaultdict(list)
    for k in range(0, len(data) - 3, 4):
        v = struct.unpack_from("<I", data, k)[0]
        if base <= v < base + len(data):
            u32[v - base].append(k)
    code, users = defaultdict(list), defaultdict(set)
    for lui, lo, a in _mipsre.pairs(data, base):
        code[a - base].append((lui - base, lo - base))
        users[lui - base].add(a)
    return u32, code, users


MENU_ENDS = {0xFFFF, 0x9999, 0x8888, 0x0000}


def term_len(data, e, off, avail):
    """Bytes of terminator after an entry's slot: page terminator + args (+ chained), one menu end word, 0 for a
    count-drawn string (`len_at`), None when the word after it is not a terminator (strings back to back)."""
    if "len_at" in e:
        return 0
    end = _end(e)
    if end is None:
        return None
    if end in MENU_ENDS:
        return 2
    if end in PAGE_TERMS or end == 0x1000 and e.get("kind") != "menu":
        return _page_end(rooms.words(data), off, avail, end) - off - 2 * avail
    if end == 0x1000:  # EXE menu strings end 0x1000
        return 2
    return None


def movable(e):
    """Kinds strpack may re-lay: referenced strings with a known end (not fixed-width table fields)."""
    if "max" in e or e.get("kind") not in ("menu", "bfont", "ptr", "next", "code"):
        return False
    if "len_at" in e:
        return True
    end = _end(e)
    return end in MENU_ENDS or end in PAGE_TERMS or end == 0x1000


def _end(e):
    """The entry's end word, or None (no `end`, or 'EOF')."""
    try:
        return int(e["end"], 16)
    except (KeyError, ValueError):
        return None


def _page_end(w, off, n, term):
    i = off // 2 + n
    i += 1 + rooms.TERM_ARGS.get(term, 0)
    while i < len(w) and w[i] in rooms.TERMS:
        i += 1 + rooms.TERM_ARGS.get(w[i], 0)
    return 2 * i


def units(data, items):
    """items [(off, avail, new words, entry)] sorted -> [[item, ..]]: `next` pages join the page before them."""
    out = []
    for it in items:
        off, avail, _, e = it
        prev = out[-1][-1] if out else None
        if e.get("kind") == "next" and prev and prev[0] + 2 * prev[1] + term_len(data, prev[3], prev[0], prev[1]) == off:
            out[-1].append(it)
        else:
            out.append([it])
    return out


def body_of(orig, u):
    """(bytes, {entry off: offset in bytes}): the unit's entries with their new words, terminators carried."""
    body, at_of = b"", {}
    for k, (off, avail, new, e) in enumerate(u):
        at_of[off] = len(body)
        body += struct.pack("<%dH" % len(new), *new)
        t = off + 2 * avail
        body += orig[t:u[k + 1][0] if k + 1 < len(u) else t + term_len(orig, e, off, avail)]
    return body, at_of


def coalesce(spans):
    out = []
    for a, b in sorted(s for s in spans if s[1] > s[0]):
        if out and a <= out[-1][1]:
            out[-1] = (out[-1][0], max(out[-1][1], b))
        else:
            out.append((a, b))
    return out


def pack(path, orig, items):
    """items [(off, avail, new words, entry)] for one file -> (writes [(off, bytes, by)], moved entry ids).
    A unit that fits stays at its address (shrunk: terminator pulled in, the rest becomes free space); a unit that
    grows moves into free space (best fit). References to every entry whose address changed are re-aimed."""
    base = BASE[path]
    u32, code, users = refs(orig, base)
    writes, new_at = [], {}  # new_at: entry offset -> new offset
    free = [((len(orig) + 3) & ~3, TAIL_END[path] - base)] if path in TAIL_END else \
        [(EXE_FREE[0] - base, EXE_FREE[1] - base)] if path == "SLPS_013.68" else []
    grow = []
    if path in POOL:  # every string re-laid back to back (4-aligned) over the old run
        us = units(orig, sorted(items, key=lambda t: t[0]))
        cur, hi = us[0][0][0], 0
        for u in us:
            last = u[-1]
            hi = max(hi, last[0] + 2 * last[1] + term_len(orig, last[3], last[0], last[1]))
        hi = (hi + 3) & ~3
        assert not any(orig[a:b].strip(b"\0") for a, b in _gaps(us, orig)), f"{path}: data between pooled strings"
        laid = []
        for u in us:
            body, at_of = body_of(orig, u)
            laid.append((cur, body, u, at_of))
            cur = (cur + len(body) + 3) & ~3
        if cur > hi:
            raise SystemExit(f"strpack: {path}: pooled strings need {cur - us[0][0][0]} bytes, the run has "
                             f"{hi - us[0][0][0]}")
        all_items, items, pooled = items, [], laid
    else:
        all_items, pooled = items, []

    def emit(at, body, u, at_of):
        for k, (off, avail, new, e) in enumerate(u):  # one write per entry: its words + what follows it
            end = at_of[u[k + 1][0]] if k + 1 < len(u) else len(body)
            writes.append((at + at_of[off], body[at_of[off]:end], e["id"]))
            new_at[off] = at + at_of[off]

    for args in pooled:
        emit(*args)
    for u in units(orig, sorted(items, key=lambda t: t[0])):
        last = u[-1]
        tl = term_len(orig, last[3], last[0], last[1])
        if tl is None:  # strings back to back: in place, padded to the slot
            for off, avail, new, e in u:
                if len(new) > avail:
                    raise SystemExit(f"strpack: {e['id']} is longer than its slot and has no terminator")
                writes.append((off, struct.pack("<%dH" % avail, *(new + [0] * (avail - len(new)))), e["id"]))
            continue
        start, end = u[0][0], last[0] + 2 * last[1] + tl
        if end % 4 and orig[end:end + 2] == b"\0\0":  # the zero word padding the next string to 4 bytes
            end += 2
        body, at_of = body_of(orig, u)
        if len(body) <= end - start:
            emit(start, body, u, at_of)
            free.append((start + len(body), end))
        else:
            grow.append((u, body, at_of))
            free.append((start, end))
    free = [((a + 3) & ~3, b) for a, b in coalesce(free)]  # moved strings start 4-aligned, like the originals
    for u, body, at_of in sorted(grow, key=lambda g: -len(g[1])):
        fits = [i for i, (a, b) in enumerate(free) if b - a >= len(body)]
        if not fits:
            raise SystemExit(f"strpack: {path}: no free space for {len(body)} bytes ({u[0][3]['id']})")
        i = min(fits, key=lambda i: free[i][1] - free[i][0])  # best fit
        a, b = free[i]
        free[i] = (min((a + len(body) + 3) & ~3, b), b)
        emit(a, body, u, at_of)
    moved = [e["id"] for _, _, _, e in all_items if new_at.get(_off(e)) not in (None, _off(e))]
    for off, at in new_at.items():
        if at != off:
            for k in u32.get(off, []):
                writes.append((k, struct.pack("<I", base + at), f"ptr {k:X} -> {base + at:X}"))
    for lui, addrs in users.items():  # every lui whose built address moved: one hi for all its users
        news = {a: base + new_at.get(a - base, a - base) for a in addrs}
        if all(news[a] == a for a in addrs):
            continue
        his = set()
        for a in addrs:
            for l2, lo in code[a - base]:
                if l2 != lui:
                    continue
                lo_w = struct.unpack_from("<I", orig, lo)[0]
                hi, lo16 = (news[a] >> 16, news[a] & 0xFFFF) if lo_w >> 26 == 0x0D else compose.hi_lo(news[a])
                his.add(hi)
                if news[a] != a:
                    writes.append((lo, struct.pack("<I", lo_w & 0xFFFF0000 | lo16), f"lo {lo:X} -> {news[a]:X}"))
        if len(his) > 1:
            raise SystemExit(f"strpack: {path} lui 0x{lui:X} builds addresses that now need different his")
        hi_w, hi = struct.unpack_from("<I", orig, lui)[0], his.pop()
        if hi_w & 0xFFFF != hi:
            writes.append((lui, struct.pack("<I", hi_w & 0xFFFF0000 | hi), f"lui {lui:X} -> {hi:X}"))
    return writes, moved


def _gaps(us, orig):
    """Byte spans between consecutive units (terminators included in the units)."""
    ends = [u[-1][0] + 2 * u[-1][1] + term_len(orig, u[-1][3], u[-1][0], u[-1][1]) for u in us]
    return [(e, u[0][0]) for e, u in zip(ends, us[1:])]


def _off(e):
    return int(e["id"].split(":")[1], 16)
