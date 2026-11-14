"""extract.py: dump every Japanese string into script/*.json (docs/re/text.md). Never clobbers English.

    python -X utf8 tools/extract.py [--force]

Sources:
  - rooms/Rxx.json: every room page (tools/rooms.py), id `Rxx:OFFSET`, with its font, header kind and terminator.
  - <SRC>.json for the menu/battle streams (EXE, ST, BALLBAT, MACHINE, TTL, LVUP, FDS): STREAMS below gives each
    file's text ranges. A range splits into strings at every word that is not text (0xFFFF end, pointers, ...);
    0x9999 is the newline and 0x0000 a blank cell inside a string. Leading/trailing 0x0000 are padding, outside `jp`
    (`tail` = trailing pad words), except blanks right after a pointer target. A string is kept when a pointer
    (u32 or lui/addiu) aims at it or a msgscan run lies in it, and dropped inside tbl/menu_data.txt (tables that
    decode as text, checked by eye). BALLBAT.json also holds `kind: bfont` item names (jtext.battle_table).
  - <src>_<table>.json: fixed-width fields (FIXED below); `max` = cells, jp without the zero padding.
`uncovered(src)` lists text-like runs no entry covers (tests/test_extract.py wants none).
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
from jtext import Codec, battle_table, table  # noqa: E402

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
    "EXE": ("SLPS_013.68", 0x80017800, [(0x6AA10, 0x6ACA8), (0x77A80, 0x77BA0), (0x77C20, 0x77C58), (0x79EC0, 0x79F10),
                                         (0x7A4DC, 0x7CAB8)]),
    "ST": ("PRG/ST.BIN", 0x800D0000, [(0x100, 0x3D40)]),
    "BALLBAT": ("PRG/BALLBAT.BIN", 0x800D0000, [(0x21500, 0x22830), (0x252E0, 0x25320)]),
    "MACHINE": ("PRG/MACHINE.BIN", 0x800D0000, [(0x10190, 0x10930)]),
    "TTL": ("PRG/TTL.BIN", 0x800D0000, [(0x54E0, 0x5744)]),
    "LVUP": ("PRG/LVUP.BIN", 0x800D0000, [(0x1B68, 0x1C90)]),
    "FDS": ("FPRG/FDS.BIN", 0x800F7000, [(0x124F0, 0x12A78)]),
}
# Strings can sit back to back with no terminator (BALLBAT fixed fields, ST `０１２３４５６７８９` + `[9999]きおく..`):
# a string starts at every pointer target, and blank cells after the target are text (a cursor indent), not
# padding. BALLBAT cuts at u32 targets only: a code ref aims mid-string at 0x252E8 (リンリー|ン).
U32_CUTS_ONLY = {"BALLBAT"}
# BALLBAT item names in its own 8x16 font (jtext.battle_table): [u32 cells, u32 ptr] list at this offset, ptr 0 ends
BFONT = ("BALLBAT", 0x22AB4)
# BALLBAT draws names and messages for the cell count in a [u32 cells, u32 ptr] record (blocks 0x21530.., 0x21A7C..,
# 0x22384.., 0x22708.., BFONT), not to a terminator: the lose message stops at its record's 14 of 16 cells. `len_at`
# = that u32. The block 0x21E1C-0x21E94 is [u32 id, u32 ptr] (attack names, ids 3-6), not cells.
CELL_RECORDS = {"BALLBAT": (0x21E1C, 0x21E94)}
# Fixed-width fields: name -> (source, lo, hi, stride); slot i at lo + i*stride, the last slot cut at hi
# (docs/re/text.md "EXE text"). Written to <source>_<name>.json.
FIXED = {
    "key_items": ("EXE", 0x7CE18, 0x7CF28, 0x10),
    # 2 lines of 16 cells per key item (slot 2k, 2k+1 = item k); u32 table 0x7D3B4 points at each pair
    "key_item_desc": ("EXE", 0x7CF74, 0x7D3B4, 0x20),
    "consumables": ("EXE", 0x7D400, 0x7D7B0, 0x10),
    "item_effects": ("EXE", 0x7D7C0, 0x7DC5C, 0x14),
    "equipment": ("EXE", 0x7DC7C, 0x7E1FC, 0x10),
    "abilities": ("EXE", 0x7F84A, 0x7F9B6, 0x0E),
    "mashin_attacks": ("EXE", 0x80094, 0x801C0, 0x14),
    "enemies": ("EXE", 0x80300, 0x80558, 0x14),
    "shop_lines": ("EXE", 0x77BA0, 0x77C20, 0x20),  # 16-cell lines: confirm (10 + はい　いいえ), no money, ...
    "monpet_lines": ("EXE", 0x77C58, 0x77CC8, 0x20),  # monpet naming prompts; 0x77CC8+ is a number table
    # field pages ending 0x3000 after event data (not found as pages): 0x80043B88 shows the first at a map edge
    "no_way_back": ("EXE", 0x77808, 0x77828, 0x10),
    "places": ("FDS", 0x120D8, 0x124AC, 0x14),  # 10-cell place names; u32 table 0x124AC = first slot per episode
    "voices": ("FDS", 0x18550, 0x18596, 0x0E),  # 7-cell voice names (なんでやねん ..; TTL.json has its own copy)
}


# Battle enemy names (found by the phase-5 marker tour): YM/BR_02/ENE01-18.BIN, battle overlays loaded at ENE_BASE.
# Record [u32 cells<<8 | idx, u32 ptr8, u32 ptr name, ..]: the cell count is explicit, names sit back to back
# unterminated (ENE13 ラムネコップ|シェイクコップ). Written to ene/ENExx.json, `len_at` = the cell-count byte
# (record + 1). ptr8 = the battle-header name (`kind: bname`): bytes in the 8x16 battle font, NUL-terminated, in
# char[12] slots (ENE06 0x25D4: 8): `max` letters = slot - 1.
ENE_BASE = 0x80104800
ENE = [f"YM/BR_02/ENE{i:02d}.BIN" for i in range(1, 19)]


def ene_names(data):
    """{name offset: (cells, record offset)} of an ENE overlay's enemy names."""
    out = {}
    for k in range(0, len(data) - 11, 4):
        w, a, p = struct.unpack_from("<3I", data, k)
        n, p = w >> 8, p - ENE_BASE
        if w >> 16 or not 1 <= n <= 16 or a >> 20 != 0x801 or not 0 <= p <= len(data) - 2 * n or p % 2:
            continue
        cells = words(data, p, p + 2 * n)
        if all(1 <= x < 0x1A4 for x in cells) and sum(1 <= x < 0xAE for x in cells) >= 2:
            out.setdefault(p, (n, k))
    return out


def ene_doc(path):
    data = (TREE / path).read_bytes()
    c = Codec(table())
    name = path.split("/")[-1][:-4]
    names = ene_names(data)
    entries = [{"id": f"{name}:{o:05X}", "kind": "ename", "max": n, "len_at": f"{k + 1:05X}",
                "jp": c.decode(data[o:o + 2 * n]), "en": ""} for o, (n, k) in sorted(names.items())]
    bc = Codec(battle_table())
    for a in sorted({struct.unpack_from("<I", data, k + 4)[0] - ENE_BASE for _, k in names.values()}):
        end = data.index(b"\0", a)
        z = end
        while z < min(len(data), a + 12) and not data[z]:
            z += 1
        entries.append({"id": f"{name}:{a:05X}", "kind": "bname", "max": z - a - 1,
                        "jp": "".join(bc.dec[x] for x in data[a:end]), "en": ""})
    return {"file": path, "base": "%08X" % ENE_BASE, "entries": sorted(entries, key=lambda e: e["id"])}


def words(data, lo=0, hi=None):
    hi = len(data) & ~1 if hi is None else hi
    return struct.unpack_from("<%dH" % ((hi - lo) // 2), data, lo)


def targets(data, base, code=True):
    """File offsets that code (lui/addiu) or u32 pointers aim at."""
    out = {a - base for _, a in rooms.re_consts(data, base)} if code else set()
    for k in range(0, len(data) - 3, 4):
        out.add(struct.unpack_from("<I", data, k)[0] - base)
    return {t for t in out if 0 <= t < len(data)}


def is_ptr(data, k):
    """u32 at k is a main-RAM address (records also point into the EXE, BALLBAT 0x217FC -> 0x80094D20)."""
    return k + 4 <= len(data) and 0x80010000 <= struct.unpack_from("<I", data, k)[0] < 0x80200000


def bfont_names():
    """[(offset, ncells)] of the BALLBAT battle-font item names (BFONT list)."""
    name, k = BFONT
    path, base, _ = STREAMS[name]
    data = (TREE / path).read_bytes()
    out = []
    while True:
        n, p = struct.unpack_from("<II", data, k)
        if not p:
            return out
        out.append((p - base, n))
        k += 8


def segments(data, lo, hi, cuts=(), hard=()):
    """[(start, nwords, tail, end_word)] for each run of text words in [lo, hi), zero padding trimmed. A run also
    ends before a pointer target (`cuts`) that follows a 0x0000: some menus end strings with 0x0000 (EXE 0x77B9E).
    hard: targets a run always ends before; one starting at a hard target keeps its leading blanks."""
    hi = len(data) & ~1 if hi is None else hi
    w = words(data, lo, hi)
    out, i = [], 0
    while i < len(w):
        if w[i] not in TEXTW:
            i += 1
            continue
        j = i + 1
        while j < len(w) and w[j] in TEXTW and not (lo + 2 * j in hard or lo + 2 * j in cuts and w[j - 1] == 0 and w[j]):
            j += 1
        a, b = i, j
        while a < b and w[a] == 0 and not (lo + 2 * a in hard and any(w[a:b])):
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
    hard = targets(data, base, code=False) if name in U32_CUTS_ONLY else tg
    marks = sorted(tg | {o for o, _ in msgscan.scan(data)})
    inpage = set()
    if name == "EXE":
        for o, n, _, _ in exe_pages(data):
            inpage.update(range(o, o + 2 * n + 2, 2))
    skip = data_ranges().get(name, [])
    out = []
    for lo, hi in ranges:
        for o, n, tail, end in segments(data, lo, hi, tg, hard):
            cells = [(o + 2 * k) for k, x in enumerate(words(data, o, o + 2 * n)) if x]
            if o in inpage or any(a <= o < b for a, b in skip):
                continue
            if len(cells) == 1 and cells[0] % 4 == 0 and is_ptr(data, cells[0] + 4):
                continue  # one "cell" then a pointer: a [u32 id, u32 ptr] record, not text
            # a pointer may aim at the zero padding before the string (up to 8 words)
            k = bisect.bisect_left(marks, o - 16)
            if k < len(marks) and marks[k] < o + 2 * n:
                out.append((o, n, tail, end))
    return data, out


def data_ranges():
    """{source: [(lo, hi)]} of file ranges that decode as text but are tables (tbl/menu_data.txt, `SRC LO-HI`)."""
    out = {}
    for line in (ROOT / "tbl" / "menu_data.txt").read_text(encoding="utf-8").splitlines():
        line = line.split("#")[0].split()
        if line:
            lo, hi = line[1].split("-")
            out.setdefault(line[0], []).append((int(lo, 16), int(hi, 16)))
    return out


def spans(name):
    """(data, {byte offsets}) every extracted entry of source `name` covers (text, padding and end word)."""
    path, base, ranges = STREAMS[name]
    data, strs = stream_strings(name)
    cov = set()
    for o, n, tail, _ in strs:
        cov.update(range(o, o + 2 * (n + tail) + 2))
    if name == "EXE":
        for o, n, _, _ in exe_pages(data):
            cov.update(range(o, o + 2 * n + 2))
    for src, lo, hi, _ in FIXED.values():
        if src == name:
            cov.update(range(lo, hi))
    if name == BFONT[0]:
        for o, n in bfont_names():
            cov.update(range(o, o + 2 * n))
    return data, cov


def uncovered(name):
    """Text-like runs (msgscan --menu, 2+ words outside every entry) left in source `name`: inside its text ranges
    any run, outside them runs of 6+ words (shorter ones there are code and table noise). Data ranges waive."""
    data, cov = spans(name)
    _, _, ranges = STREAMS[name]
    skip = data_ranges().get(name, [])
    msgscan.ENDS = (0x1000, 0x2000, 0xFFFF, NL, 0x0000)
    out = []
    for o, s in msgscan.scan(data):
        if sum(o + 2 * k not in cov for k in range(len(s))) < 2 or any(a <= o < b for a, b in skip):
            continue
        if len(s) >= 6 or any(lo <= o < hi for lo, hi in ranges):
            out.append((o, s))
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
        entries.append(e)
    if name == BFONT[0]:
        bc = Codec(battle_table())
        for o, n in bfont_names():
            e = {"id": f"{name}:{o:05X}", "kind": "bfont", "jp": bc.decode(data[o:o + 2 * n]), "en": ""}
            if n % 2:
                e["tail"] = 1
            entries.append(e)
    path, base, _ = STREAMS[name]
    if name in CELL_RECORDS:
        lo, hi = CELL_RECORDS[name]
        at = {e["id"]: e for e in entries}
        for k in range(0, len(data) - 7, 4):
            n, p = struct.unpack_from("<II", data, k)
            e = at.get(f"{name}:{p - base:05X}")
            if e and 1 <= n <= 40 and not lo <= k < hi:
                assert "len_at" not in e, e["id"]
                e["len_at"] = f"{k:05X}"
    return {"file": path, "base": "%08X" % base, "entries": entries}


def fixed_doc(tab):
    src, lo, hi, stride = FIXED[tab]
    path, base, _ = STREAMS[src]
    data = (TREE / path).read_bytes()
    c = Codec(table(), newline=NL)
    entries = []
    for i, o in enumerate(range(lo, hi, stride)):
        w = words(data, o, min(o + stride, hi))
        n = len(w)
        while n and w[n - 1] == 0:
            n -= 1
        entries.append({"id": f"{src}:{o:05X}", "slot": i, "max": len(w), "jp": c.decode(data[o:o + 2 * n]), "en": ""})
    return {"file": path, "base": "%08X" % base, "table": tab, "stride": stride, "entries": entries}


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
        yield f"{FIXED[tab][0].lower()}_{tab}.json", fixed_doc(tab)
    for path in ENE:
        yield f"ene/{path.split('/')[-1][:-4]}.json", ene_doc(path)


def main():
    force = "--force" in sys.argv
    bad = 0
    for rel, doc in all_docs():
        lost = write(rel, doc, force)
        print(f"{rel}: {len(doc['entries'])} strings" + (f"  REFUSED, would drop English of {lost[:5]}" if lost and not force else ""))
        bad += bool(lost and not force)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
