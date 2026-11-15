"""roompack.py: room overlay text (FPRG/Rxx.BIN) re-laid with English page lengths (docs/re/text.md "Room scripts").

A unit is a run of pages nothing points into except at page starts:
  - bank: one message bank (from its pointer in the bank array to the end of its last page); the engine walks a bank
    for the message id, so pages inside may change length;
  - ptr: an NPC message (a u32 pointer target, sometimes 16 zero bytes before the text) and the pages chained to it;
  - fixed: anything else (code-built blocks, event pages outside their bank): in place only, must not grow.
pack() rebuilds each unit with the new page words. A unit that still fits stays in place (zero-padded); a grown
bank/ptr unit moves to the end of the overlay file (the overlay area runs to FDS at 0x800F7000; the RAM after a
room's file holds only stale overlay leftovers, files.md) and every u32 slot aimed at a page start inside a rewritten
unit is re-aimed.
"""
import struct
import sys
from functools import lru_cache
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import rooms  # noqa: E402

LIMIT = 0x800F7000 - rooms.BASE  # overlay file size cap: FDS.BIN loads at 0x800F7000


def page_end(w, off, n, term):
    """Byte offset after a page's terminator, its args and any chained terminators (as rooms.pages walks)."""
    i = off // 2 + n
    i += 1 + rooms.TERM_ARGS.get(term, 0)
    while i < len(w) and w[i] in rooms.TERMS:
        i += 1 + rooms.TERM_ARGS.get(w[i], 0)
    return 2 * i


@lru_cache(None)
def units(name):
    """[{kind, start, end, pages: [(off, n)]}] for overlay `name` (R00..R14), in file order."""
    data = (rooms.FPRG / f"{name}.BIN").read_bytes()
    w = rooms.words(data)
    banks = sorted({b for ep, c in enumerate(rooms.CASES) if c[0] == name for b in rooms.banks(ep)})
    ptr = rooms.pointers(data)
    out, seen_banks = [], set()
    for off, n, term, hdr in rooms.pages(data):
        end = page_end(w, off, n, term)
        cur = out[-1] if out else None
        bank = max([b for b in banks if b <= off], default=None)
        if hdr == "next" and cur and cur["end"] == off:
            pass
        elif hdr in ("ptr", "event") and (off in ptr or off - 16 in ptr) and (not cur or cur["end"] <= off - 16 or
                                                                            cur["end"] <= off and off in ptr):
            start = off - 16 if off - 16 in ptr and (not cur or cur["end"] <= off - 16) else off
            cur = {"kind": "ptr", "start": start, "pages": []}
            out.append(cur)
        elif hdr == "event" and cur and cur["kind"] == "ptr" and 0 <= off - cur["end"] <= 32:
            pass  # an NPC message going on after an event command (`A000 n FFFF` <text>)
        elif hdr == "event" and cur and cur["kind"] == "bank" and cur["bank"] == bank:
            pass
        elif hdr == "event" and bank is not None and bank not in seen_banks and (not cur or cur["end"] <= bank):
            seen_banks.add(bank)
            cur = {"kind": "bank", "bank": bank, "start": bank, "pages": []}
            out.append(cur)
        else:
            cur = {"kind": "fixed", "start": off, "pages": []}
            out.append(cur)
        cur["pages"].append((off, n))
        cur["end"] = end
    tables = [arr - rooms.BASE for n, _, arr in rooms.CASES if n == name]  # bank pointer arrays: EXE-addressed, stay
    for a, b in zip(out, out[1:] + [None]):  # bytecode / padding up to the next unit (FBFF FFFF.., FEFF n..) travels along
        if a["kind"] not in ("bank", "ptr"):
            continue
        if b and b["kind"] in ("bank", "ptr") and 0 < b["start"] - a["end"] <= 64 and \
                not any(a["end"] <= t < b["start"] for t in tables):
            a["end"] = b["start"]
        elif any(0 < t - a["end"] <= 64 for t in tables):
            # a room's last bank ends `3000 0016 FFFB FFFF` before its pointer array: left behind when the bank moved,
            # the event ran into the next unit's text and hung (R00 village exit, after "Okay, we're off!")
            a["end"] = min(t for t in tables if 0 < t - a["end"] <= 64)
    return out


def unit_of(name, off):
    for u in units(name):
        if u["start"] <= off < u["end"]:
            return u
    return None


def growth(name, items):
    """{unit start: bytes gained} for items {off: (avail words, new words, id)}."""
    out = {}
    for off, (avail, new, _) in items.items():
        u = unit_of(name, off)
        out[u["start"] if u else off] = out.get(u["start"] if u else off, 0) + 2 * (len(new) - avail)
    return out


@lru_cache(None)
def pools(name):
    """Runs of bank/ptr units separated only by zero padding (<= 64 bytes): units are re-laid inside their pool."""
    data = (rooms.FPRG / f"{name}.BIN").read_bytes()
    out, cur = [], None
    for u in units(name):
        if u["kind"] not in ("bank", "ptr"):
            cur = None
        elif cur and u["start"] - cur[-1]["end"] <= 64 and not any(data[cur[-1]["end"]:u["start"]]):
            cur.append(u)
        else:
            cur = [u]
            out.append(cur)
    return out


def segments(u, items):
    """(segments, new length): ('v', old_start, old_end) verbatim bytes, ('e', off, avail, new words, id)."""
    segs, pos = [], u["start"]
    for o, (avail, new, eid) in sorted((o, v) for o, v in items.items() if u["start"] <= o < u["end"]):
        if o > pos:
            segs.append(("v", pos, o))
        segs.append(("e", o, avail, new, eid))
        pos = o + 2 * avail
    if pos < u["end"]:
        segs.append(("v", pos, u["end"]))
    return segs, sum(s[2] - s[1] if s[0] == "v" else 2 * len(s[3]) for s in segs)


def pack(name, orig, items):
    """Writes [(offset, bytes, by)] for every unit holding an item (and every unit its pool shifts). Raises if a
    fixed unit grows or the overlay passes LIMIT."""
    tail = (len(orig) + 3) & ~3
    writes, remap = [], {}  # remap: old pointer target -> new offset
    starts = set(rooms.pointers(orig)) | {u["start"] for u in units(name)}  # targets in moved bytes move along

    def emit(u, dest, segs):
        at = dest
        for s in segs:
            if s[0] == "v":
                if at != s[1]:
                    writes.append((at, orig[s[1]:s[2]], f"{name} unit {u['start']:X} moved"))
                for p in starts:
                    if s[1] <= p < s[2]:
                        remap[p] = at + p - s[1]
                at += s[2] - s[1]
            else:
                writes.append((at, struct.pack("<%dH" % len(s[3]), *s[3]), s[4]))
                remap[s[1]] = at
                at += 2 * len(s[3])
        remap[u["start"]] = dest
        return at

    for u in units(name):
        if u["kind"] not in ("bank", "ptr") and any(u["start"] <= o < u["end"] for o in items):
            segs, n = segments(u, items)
            if n > u["end"] - u["start"]:
                raise SystemExit(f"roompack: {name} fixed unit 0x{u['start']:X} grows by {n - u['end'] + u['start']}")
            end = emit(u, u["start"], segs)
            if end < u["end"]:
                writes.append((end, bytes(u["end"] - end), f"{name} unit {u['start']:X} pad"))
    for pool in pools(name):
        lo, hi = pool[0]["start"], pool[-1]["end"]
        laid = [(u, *segments(u, items)) for u in pool]
        if all(n == u["end"] - u["start"] for u, _, n in laid):  # no length change: entries in place
            for u, segs, _ in laid:
                emit(u, u["start"], segs)
            continue
        cur = lo
        for u, segs, n in laid:
            if cur + n <= hi:
                dest, cur = cur, cur + n
            else:  # past the pool: the overlay's end
                dest, tail = tail, (tail + n + 3) & ~3
                if tail > LIMIT:
                    raise SystemExit(f"roompack: {name} needs 0x{tail:X} bytes, the overlay area holds 0x{LIMIT:X}")
            emit(u, dest, segs)
        if cur < hi:
            writes.append((cur, bytes(hi - cur), f"{name} pool {lo:X} pad"))
    spans = [(u["start"], u["end"]) for u in units(name)]
    for target, slots in rooms.pointers(orig).items():
        if target in remap and remap[target] != target:
            for k in slots:
                if not any(a <= k < b for a, b in spans):
                    writes.append((k, struct.pack("<I", rooms.BASE + remap[target]), f"{name} ptr {k:X}"))
    return writes


def selftest():
    for name in rooms.OVERLAYS:
        us = units(name)
        assert all(a["end"] <= b["start"] for a, b in zip(us, us[1:])), name  # units never overlap
        data = (rooms.FPRG / f"{name}.BIN").read_bytes()
        ptr = rooms.pointers(data)
        assert all(b["start"] in ptr for b in us if b["kind"] in ("bank", "ptr")), name
        inside = lambda x: any(u["start"] <= x < u["end"] for u in us)  # noqa: E731
        assert not any(inside(k) and inside(t) for t, ks in ptr.items() for k in ks), name  # no text pointer moves
        for _, _, arr in (c for c in rooms.CASES if c[0] == name):  # a bank's tail bytecode moves with it
            last = max((u["end"] for u in us if u["end"] <= arr - rooms.BASE), default=0)
            assert arr - rooms.BASE - last > 64 or not any(data[last:arr - rooms.BASE]), name
    assert unit_of("R00", 0xE5D2)["end"] == 0xE5D8  # village exit: `0016 FFFB FFFF` after "Okay, we're off!"


if __name__ == "__main__":
    selftest()
    for name in rooms.OVERLAYS:
        us = units(name)
        print(name, len(us), {k: sum(u["kind"] == k for u in us) for k in ("bank", "ptr", "fixed")})
