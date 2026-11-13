"""insert.py: script/ -> the build's edits {disc path: new bytes} (tools/build.py calls edits()).

Every entry is written in place as two-letter cells (D8, tools/digraph.py): its `en`, or while it has none a marker:
its number (work/markers.tsv maps number -> id) in the first two glyph cells, then filler letters at the JP cell
count x2, keeping newlines, blank cells and inline controls (lowercase in room text, uppercase elsewhere; the letter
pair tells the column: ab = col 0, cd = col 1 .. yz = col 12, then ab again). Room and EXE pages take up to their JP
word count, menu strings their words + tail padding, fixed fields `max` cells, BALLBAT battle-font names (`bfont`)
one letter per 8x16 cell (Latin drawn over the kana of MSG_CG's 8x16 font, codes BF_FIRST+); ENE battle-header
names (`bname`) the same font as NUL-terminated bytes. `len_at` = the byte holding the drawn cell count: rewritten.
Pair codes per font context: pairs only room text uses go into that room's M16 font (codes 0x1A4+, ROOM_CAP), the
rest into MSG_CG's kanji slots (mirrored into CNF_MSG, the config screen's copy); when a room font overflows, the
pair most room fonts share moves to MSG_CG. In `en`, `[XXXX]` is a raw word (controls such as [B000][0003]).
Every write goes through put() and is logged in WRITES for romdiff (tests/test_insert.py).
Not text: ids in tbl/not_text.txt are never written.
"""
import json
import re
import struct
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import digraph  # noqa: E402
from jtext import Codec, battle_table, table  # noqa: E402

TREE = ROOT / "work" / "disc" / "tree"
SCRIPT = ROOT / "script"
CG_FIRST = 0xA6  # MSG_CG / CNF_MSG glyph index = code + 0xA6
CG_FREE = [c for c in range(0xE6, 0x1A4) if c != 0x181]  # kanji slots; kana, digits, icons and the ▼ 0x181 stay
ROOM_FIRST, ROOM_CAP = 0x1A4, 190  # room font at 0x80122500, up to 0x80128400
BF_FIRST = 0x0F  # battle font: '!' .. '~' -> 0x0F.. (over its kana; digits 1-10 stay), space = 0
INLINE = {0xB000: 1}
GLYPH_MAX = 0x262
FILL = {False: [chr(97 + i) + chr(98 + i) for i in range(0, 26, 2)]}
FILL[True] = [p.upper() for p in FILL[False]]
RAW = re.compile(r"\[([0-9A-F]{4})\]")
WRITES = {}  # disc path -> [(offset, orig bytes, new bytes, writer)]
OVERFLOW = []  # ids whose `en` is longer than the JP slot (marker shown instead; phase 7)
# Code patches: (path, offset, original u32, new u32, why). The battle header (BALLBAT 0x800DF310-0x800DF3C8) draws
# the 8-bit enemy name for the 16-bit name's cell count (0x800F1C00), which in English is half the letters: loop to
# the NUL instead (lbu v1,0(s1) for both count reads; the slt goes, bnez v1 tests the next byte). docs/re/windows.md.
CODE = [
    ("PRG/BALLBAT.BIN", 0xF340, 0x94631C00, 0x92230000, "header name: lbu v1,0(s1) (was lhu count)"),
    ("PRG/BALLBAT.BIN", 0xF390, 0x94631C00, 0x92230000, "header name: lbu v1,0(s1) (next byte)"),
    ("PRG/BALLBAT.BIN", 0xF398, 0x0203182A, 0x00000000, "header name: nop (was slt v1,s0,v1)"),
]


def not_text():
    out = set()
    for line in (ROOT / "tbl" / "not_text.txt").read_text(encoding="utf-8").splitlines():
        line = line.split("#")[0].split()
        if line:
            out.add(line[0])
    return out


def entries():
    """[(entry, disc path, offset, original words, avail words, newline, context)], numbered by list order
    (number = index + 1). Context: 'M16_Rxx' room font, 'CG' common, 'BF' battle font."""
    codecs, out, skip = {}, [], not_text()
    for p in sorted(SCRIPT.glob("rooms/*.json")) + sorted(SCRIPT.glob("*.json")) + sorted(SCRIPT.glob("ene/*.json")):
        doc = json.loads(p.read_text(encoding="utf-8"))
        for e in doc["entries"]:
            if not e["jp"].strip("　\n") or e["id"] in skip:
                continue
            kind = e.get("kind")
            if "font" in e:
                ctx, tab, nl = "M16_" + e["font"], "M16_" + e["font"], 0x1000
            elif kind in ("bfont", "bname"):
                ctx, tab, nl = "BF", "BF", None
            elif "table" in doc or kind == "menu":
                ctx, tab, nl = "CG", None, 0x9999
            else:  # EXE dialogue pages
                ctx, tab, nl = "CG", None, 0x1000
            key = (tab, nl)
            if key not in codecs:
                codecs[key] = Codec(battle_table()) if tab == "BF" else Codec(table(tab), newline=nl or 0x1000)
            b = codecs[key].encode(e["jp"])
            words = list(struct.unpack("<%dH" % (len(b) // 2), b))
            avail = e["max"] if "max" in e else len(words) + (e.get("tail", 0) if kind == "menu" else 0)
            out.append((e, doc["file"], int(e["id"].split(":")[1], 16), words, avail, nl, ctx))
    return out


def marker(words, num, nl, upper):
    """Marker text for one entry from its original words (see module doc)."""
    digits = ["%02d" % (num // 100 % 100), "%02d" % (num % 100)]
    fill = FILL[upper]
    out, col, k, i = [], 0, 0, 0
    while i < len(words):
        w = words[i]
        if w == nl:
            out.append("\n")
            col = -1
        elif w == 0:
            out.append("  ")
        elif w in INLINE:
            out.append("".join("[%04X]" % x for x in words[i:i + 1 + INLINE[w]]))
            i += INLINE[w]
            col -= 1
        elif w < GLYPH_MAX:
            out.append(digits[k] if k < 2 else fill[col % len(fill)])
            k += 1
        else:
            out.append("[%04X]" % w)
            col -= 1
        col += 1
        i += 1
    return "".join(out)


def cells(text, nl):
    """Text -> list of raw words (int) and two-char pairs (str, '  ' = blank cell)."""
    out = []
    for n, line in enumerate(text.split("\n")):
        if n:
            out.append(nl)
        pos = 0
        for m in RAW.finditer(line):
            out += [p.ljust(2) for p in digraph.pairs(line[pos:m.start()])]
            out.append(int(m[1], 16))
            pos = m.end()
        out += [p.ljust(2) for p in digraph.pairs(line[pos:])]
    return out


def bf_code(ch):
    return 0 if ch == " " else BF_FIRST + ord(ch) - 0x21


def allocate(uses):
    """uses {context: set of pairs} -> {context: {pair: code}} (see module doc)."""
    cg = set(uses.get("CG", ())) - {"  "}
    rooms = {c: set(s) - cg - {"  "} for c, s in uses.items() if c.startswith("M16")}
    while True:
        over = [s for s in rooms.values() if len(s) > ROOM_CAP]
        if not over:
            break
        shared = Counter(p for s in rooms.values() for p in s)
        best = max(set().union(*over), key=lambda p: (shared[p], p))
        cg.add(best)
        for s in rooms.values():
            s.discard(best)
    if len(cg) > len(CG_FREE):
        raise SystemExit(f"insert: {len(cg)} common pairs, MSG_CG has {len(CG_FREE)} free codes")
    cgmap = dict(zip(sorted(cg), CG_FREE))
    out = {"CG": cgmap}
    for c, s in rooms.items():
        out[c] = {**cgmap, **{p: ROOM_FIRST + i for i, p in enumerate(sorted(s))}}
    return out


def put(bufs, orig, path, off, data, by):
    """The one write path: logs (offset, original bytes, new bytes, writer) for romdiff."""
    buf = bufs.setdefault(path, bytearray(orig[path]))
    if len(buf) < off + len(data):
        buf.extend(b"\xff" * (off + len(data) - len(buf)))
    old = orig[path][off:off + len(data)].ljust(len(data), b"\xff")
    WRITES.setdefault(path, []).append((off, old, bytes(data), by))
    buf[off:off + len(data)] = data


def edits(qa=None):
    """{disc path: new bytes}. qa: {id: text} overrides (stress lines for the width gate), still in place;
    a key '+ID' may run past the slot over the strings after it (tools/stress.py)."""
    WRITES.clear()
    OVERFLOW.clear()
    qa = qa or {}
    ents = entries()
    texts, uses, rows = [], {}, []
    for num, (e, path, off, words, avail, nl, ctx) in enumerate(ents, 1):
        text = qa.get(e["id"]) or qa.get("+" + e["id"]) or e.get("en") or None
        if text and e["id"] not in qa and "+" + e["id"] not in qa and \
                (len(text) if ctx == "BF" else len(cells(text, nl))) > avail:
            # shortcut: English past its JP slot shows the marker until phase 7 grows slots (work/overflow.tsv)
            OVERFLOW.append(e["id"])
            text = None
        if text is None:
            text = marker(words, num, nl, not ctx.startswith("M16")) if ctx != "BF" else \
                ("%04d" % num + "".join(FILL[True])[4:])[:avail]
        texts.append(text)
        rows.append(f"{num}\t{e['id']}\t{e['jp']!r}")
        if ctx != "BF":
            uses.setdefault(ctx, set()).update(c for c in cells(text, nl) if isinstance(c, str))
    codes = allocate(uses)
    orig, bufs, errors = {}, {}, []

    def load(path):
        if path not in orig:
            orig[path] = (TREE / path).read_bytes()
        return path

    spills = []
    for (e, path, off, words, avail, nl, ctx), text in zip(ents, texts):
        if ctx == "BF":
            new = [bf_code(ch) for ch in text]
        else:
            new = [c if isinstance(c, int) else codes[ctx].get(c, 0) for c in cells(text, nl)]
        spill = len(new) > avail and "+" + e["id"] in qa  # stress only: runs over the next strings, ends 0xFFFF
        if len(new) > avail and not spill:
            errors.append(f"{e['id']}: {len(new)} words, room for {avail}")
            continue
        if "len_at" in e:  # the drawn cell count: ENE record byte 1, BALLBAT [u32 cells, u32 ptr]
            k = int(e["len_at"], 16)
            assert e.get("kind") != "ename" or orig[load(path)][k] == e["max"], e["id"]
            put(bufs, orig, load(path), k, bytes([len(new)]), e["id"] + " cells")
        if spill:
            spills.append((load(path), off, struct.pack("<%dH" % (len(new) + 1), *new, 0xFFFF), e["id"]))
            continue
        if e.get("kind") == "bname":  # ENE battle-header name: bytes, NUL-terminated in its slot
            put(bufs, orig, load(path), off, bytes(new + [0] * (avail + 1 - len(new))), e["id"])
            continue
        new += [0] * (avail - len(new))
        put(bufs, orig, load(path), off, struct.pack("<%dH" % avail, *new), e["id"])
    if errors:
        raise SystemExit("insert: text too long\n  " + "\n  ".join(errors))
    for path, off, data, by in spills:  # after every in-place write, so the spill wins
        put(bufs, orig, path, off, data, by + " spill")
    for path, off, old, new, why in CODE:
        assert struct.unpack_from("<I", orig[load(path)], off)[0] == old, (path, hex(off))
        put(bufs, orig, path, off, struct.pack("<I", new), "code " + why)
    cg, cnf = load("FM16/MSG_CG.BIN"), load("OUT/CNF_MSG.BIN")
    for p, c in codes["CG"].items():
        g = digraph.cell(p)
        put(bufs, orig, cg, (c + CG_FIRST) * 128, g, f"cg {p!r}")
        put(bufs, orig, cnf, (c + CG_FIRST) * 128, g, f"cnf {p!r}")
    for ctx, m in codes.items():
        if ctx != "CG":
            f = load(f"FM16/{ctx}.BIN")
            for p, c in m.items():
                if c >= ROOM_FIRST:
                    put(bufs, orig, f, (c - ROOM_FIRST) * 128, digraph.cell(p), f"{ctx} {p!r}")
    if any(ctx == "BF" for *_, ctx in ents):
        for k in range(0x21, 0x7F):
            put(bufs, orig, cg, bf_code(chr(k)) * 64, bf_cell(chr(k)), f"bf {chr(k)!r}")
    out = ROOT / "work" / "markers.tsv"
    out.parent.mkdir(exist_ok=True)
    out.write_text("\n".join(rows) + "\n", encoding="utf-8")
    (out.parent / "overflow.tsv").write_text("".join(i + "\n" for i in OVERFLOW), encoding="utf-8")
    return {p: bytes(b) for p, b in bufs.items()}


def bf_cell(ch):
    """8x16 cell (64 bytes, 4 bytes per row) for the battle font: the left half of the 16x16 digraph cell."""
    px = digraph.pixels(ch)
    return bytes(px[y][x] | px[y][x + 1] << 4 for y in range(16) for x in range(0, 8, 2))


def log_lines(path):
    return ["%X %s %s %s" % (o, a.hex(), b.hex(), by) for o, a, b, by in WRITES.get(path, [])]
