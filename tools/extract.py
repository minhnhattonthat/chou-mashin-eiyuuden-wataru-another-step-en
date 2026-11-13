"""extract.py: dump every Japanese string into script/*.json (docs/re/text.md). Never clobbers English.

    python -X utf8 tools/extract.py [--force]

Sources:
  - rooms/Rxx.json: every room page (tools/rooms.py), id `Rxx:OFFSET`, with its font, header kind and terminator.
  - <SRC>.json for the menu/battle streams (EXE, ST, BALLBAT, MACHINE, TTL, LVUP, FDS): STREAMS below gives each
    file's text ranges. A range splits into strings at every word that is not text (0xFFFF end, pointers, ...);
    0x9999 is the newline and 0x0000 a blank cell inside a string. Leading/trailing 0x0000 are padding, outside `jp`
    (`tail` = trailing pad words). A string is kept when a pointer (u32 or lui/addiu) aims at it or a msgscan run
    lies in it; `data` lists the ones that are tables, not text (checked by eye).
  - exe_<table>.json: the EXE's fixed-width name fields (FIXED below); `max` = cells, jp without the zero padding.
Existing files keep each id's `en`, `status` and `notes`; an id with English that would vanish stops the dump
unless --force. tests/test_extract.py checks roundtrip and coverage against the original files.
"""
import bisect
import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import msgscan  # noqa: E402
import rooms  # noqa: E402
from jtext import Codec, table  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
TREE = ROOT / "work" / "disc" / "tree"
SCRIPT = ROOT / "script"
NL = 0x9999
TEXTW = set(range(0, 0x1A4)) | {NL}
# name -> (file, base: RAM address of file offset 0, [(lo, hi)] text ranges in file offsets)
# Ranges from msgscan --menu clusters (2026-11-14); outside them runs decode to noise. The EXE's u32 "pointer arrays"
# at 0x6F364-0x7090C and 0x7532C-0x76764 aim at event records, not text. EXE dialogue (save lady 0x6AA10, shops
# 0x77A80, inn 0x79EC0, system/item messages 0x7A4DC) uses the room page grammar: see exe_pages().
STREAMS = {
    "EXE": ("SLPS_013.68", 0x80017800, [(0x6AA10, 0x6ACA8), (0x77A80, 0x77CC8), (0x79EC0, 0x79F10), (0x7A4DC, 0x7CAB8)]),
    "ST": ("PRG/ST.BIN", 0x800D0000, [(0x100, 0x3D40)]),
    "BALLBAT": ("PRG/BALLBAT.BIN", 0x800D0000, [(0x21500, 0x22A70), (0x252E0, 0x25320)]),
    "MACHINE": ("PRG/MACHINE.BIN", 0x800D0000, [(0x10190, 0x10930)]),
    "TTL": ("PRG/TTL.BIN", 0x800D0000, [(0x54E0, 0x5744)]),
    "LVUP": ("PRG/LVUP.BIN", 0x800D0000, [(0x1B68, 0x1C90)]),
    "FDS": ("FPRG/FDS.BIN", 0x800F7000, [(0x120D8, 0x12A78)]),
}
# EXE fixed-width name fields: name -> (lo, hi, stride); slot i at lo + i*stride (docs/re/text.md "EXE text")
FIXED = {
    "key_items": (0x7CE18, 0x7CF28, 0x10),
    "consumables": (0x7D400, 0x7D7B0, 0x10),
    "item_effects": (0x7D7C0, 0x7DC5C, 0x14),
    "equipment": (0x7DC7C, 0x7E1FC, 0x10),
    "abilities": (0x7F84A, 0x7F9B6, 0x0E),
    "mashin_attacks": (0x80094, 0x801C0, 0x14),
    "enemies": (0x80300, 0x80558, 0x14),
}


def words(data, lo=0, hi=None):
    hi = len(data) & ~1 if hi is None else hi
    return struct.unpack_from("<%dH" % ((hi - lo) // 2), data, lo)


def targets(data, base):
    """File offsets that code or u32 pointers aim at."""
    out = {a - base for _, a in rooms.re_consts(data, base)}
    for k in range(0, len(data) - 3, 4):
        out.add(struct.unpack_from("<I", data, k)[0] - base)
    return {t for t in out if 0 <= t < len(data)}


def segments(data, lo, hi, cuts=()):
    """[(start, nwords, tail, end_word)] for each run of text words in [lo, hi), zero padding trimmed. A run also
    ends before a pointer target (`cuts`) that follows a 0x0000: some menus end strings with 0x0000 (EXE 0x77B9E)."""
    hi = len(data) & ~1 if hi is None else hi
    w = words(data, lo, hi)
    out, i = [], 0
    while i < len(w):
        if w[i] not in TEXTW:
            i += 1
            continue
        j = i + 1
        while j < len(w) and w[j] in TEXTW and not (w[j - 1] == 0 and w[j] and lo + 2 * j in cuts):
            j += 1
        a, b = i, j
        while a < b and w[a] == 0:
            a += 1
        while b > a and w[b - 1] == 0:
            b -= 1
        if b > a:
            out.append((lo + 2 * a, b - a, j - b, w[j] if j < len(w) else None))
        i = j
    return out


def exe_pages(data):
    """EXE dialogue pages (room grammar) inside the EXE text ranges; single-cell 'pages' are event data."""
    path, base, ranges = STREAMS["EXE"]
    return [(o, n, t, h) for o, n, t, h in rooms.pages(data, base)
            if any(lo <= o < hi for lo, hi in ranges) and sum(1 <= x < 0x1A4 for x in words(data, o, o + 2 * n)) >= 2]


def stream_strings(name):
    """(data, [(offset, nwords, tail, end)]) of the menu strings kept for a stream source; words inside EXE dialogue
    pages are left to exe_pages()."""
    path, base, ranges = STREAMS[name]
    data = (TREE / path).read_bytes()
    msgscan.ENDS = (0x1000, 0x2000, 0xFFFF, NL, 0x0000)
    tg = targets(data, base)
    marks = sorted(tg | {o for o, _ in msgscan.scan(data)})
    inpage = set()
    if name == "EXE":
        for o, n, _, _ in exe_pages(data):
            inpage.update(range(o, o + 2 * n + 2, 2))
    out = []
    for lo, hi in ranges:
        for o, n, tail, end in segments(data, lo, hi, tg):
            if o in inpage:
                continue
            # a pointer may aim at the zero padding before the string (up to 8 words)
            k = bisect.bisect_left(marks, o - 16)
            if k < len(marks) and marks[k] < o + 2 * n:
                out.append((o, n, tail, end))
    return data, out


def load_data_marks():
    """{source: {offset}} of strings that are tables, not text (tbl/menu_data.txt)."""
    out = {}
    p = ROOT / "tbl" / "menu_data.txt"
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            if line.strip() and not line.startswith("#"):
                src, *offs = line.split()
                out.setdefault(src, set()).update(int(o, 16) for o in offs)
    return out


def room_doc(name):
    data = (rooms.FPRG / f"{name}.BIN").read_bytes()
    codecs, entries = {}, []
    for o, n, term, hdr in rooms.pages(data):
        f = rooms.font(name, o)
        c = codecs.setdefault(f, Codec(table(f)))
        entries.append({"id": f"{name}:{o:05X}", "font": f[4:], "kind": hdr, "end": f"{term:04X}",
                        "jp": c.decode(data[o:o + 2 * n]), "en": ""})
    return {"file": f"FPRG/{name}.BIN", "base": "800CE000", "entries": entries}


def stream_doc(name):
    data, strs = stream_strings(name)
    c = Codec(table(), newline=NL)
    marks = load_data_marks().get(name, set())
    entries = []
    if name == "EXE":
        pc = Codec(table())
        strs += [(o, n, None, (t, h)) for o, n, t, h in exe_pages(data)]
        strs.sort()
    for o, n, tail, end in strs:
        if tail is None:  # an EXE dialogue page: newline 0x1000, page terminator as in the rooms
            entries.append({"id": f"{name}:{o:05X}", "kind": end[1], "end": "%04X" % end[0],
                            "jp": pc.decode(data[o:o + 2 * n]), "en": ""})
            continue
        e = {"id": f"{name}:{o:05X}", "kind": "menu", "jp": c.decode(data[o:o + 2 * n]), "en": ""}
        if tail:
            e["tail"] = tail
        e["end"] = "%04X" % end if end is not None else "EOF"
        if o in marks:
            e["data"] = True
        entries.append(e)
    path, base, _ = STREAMS[name]
    return {"file": path, "base": "%08X" % base, "entries": entries}


def fixed_doc(tab):
    lo, hi, stride = FIXED[tab]
    data = (TREE / STREAMS["EXE"][0]).read_bytes()
    c = Codec(table(), newline=NL)
    entries = []
    for i, o in enumerate(range(lo, hi, stride)):
        w = words(data, o, o + stride)
        n = len(w)
        while n and w[n - 1] == 0:
            n -= 1
        entries.append({"id": f"EXE:{o:05X}", "slot": i, "max": len(w), "jp": c.decode(data[o:o + 2 * n]), "en": ""})
    return {"file": STREAMS["EXE"][0], "base": "%08X" % STREAMS["EXE"][1], "table": tab, "stride": stride,
            "entries": entries}


KEEP = ("en", "status", "notes")


def write(rel, doc, force=False):
    """Write script/<rel>, carrying over KEEP fields by id. Returns ids with English that the new dump lacks."""
    p = SCRIPT / rel
    lost = []
    if p.exists():
        old = {e["id"]: e for e in json.loads(p.read_text(encoding="utf-8"))["entries"]}
        new_ids = {e["id"] for e in doc["entries"]}
        lost = [i for i, e in old.items() if e.get("en") and i not in new_ids]
        if lost and not force:
            return lost
        for e in doc["entries"]:
            for k in KEEP:
                if old.get(e["id"], {}).get(k):
                    e[k] = old[e["id"]][k]
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
        f.write("\n")
    return lost


def all_docs():
    for name in rooms.OVERLAYS:
        yield f"rooms/{name}.json", room_doc(name)
    for name in STREAMS:
        yield f"{name}.json", stream_doc(name)
    for tab in FIXED:
        yield f"exe_{tab}.json", fixed_doc(tab)


def main():
    force = "--force" in sys.argv
    bad = 0
    for rel, doc in all_docs():
        lost = write(rel, doc, force)
        n = sum(not e.get("data") for e in doc["entries"])
        print(f"{rel}: {n} strings" + (f"  REFUSED, would drop English of {lost[:5]}" if lost and not force else ""))
        bad += bool(lost and not force)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
