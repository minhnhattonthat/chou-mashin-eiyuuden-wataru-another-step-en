"""jtext.py: the game's 16-bit text codec and its per-font tables (docs/re/text.md).

Codes 0x0001-0x01A3 are the common font (tbl/jp_common.tbl via tools/mktbl.py); 0x01A4+ index a room font
FM16/M16_Rxx.BIN (read by eye into tbl/kanji_rows.txt). Unknown words decode as [XXXX] and encode back, so
encode(decode(b)) == b. A code whose glyph repeats a character already in the table decodes as [XXXX] too, to keep
the roundtrip exact (listed by `python -X utf8 tools/jtext.py`).

    from jtext import Codec, table
    c = Codec(table("M16_R00"))
    text = c.decode(words)          # words: bytes, little-endian u16 stream
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FM16 = ROOT / "work" / "disc" / "tree" / "FM16"
ROW = re.compile(r"\{[^}]*\}\??|.\??")
TOKEN = re.compile(r"\[([0-9A-F]{4})(?::[^\]]+)?\]")
# episode index (0x8009C90C) -> room font, verified (docs/re/text.md "Room font per episode index")
EPISODE_FONT = ["M16_R00", "M16_R00", "M16_R02", "M16_R02", "M16_R04", "M16_R04", "M16_R06", "M16_R07", "M16_R08",
                "M16_R09", "M16_R0A", "M16_R11", "M16_R12", "M16_R13", "M16_R0E"]


def load_rows():
    """{font: {code: (char, unsure)}} from tbl/kanji_rows.txt; font 'CG' = common codes."""
    out = {}
    for n, line in enumerate((ROOT / "tbl" / "kanji_rows.txt").read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip() or line.startswith("#"):
            continue
        font, first, chars = line.split(" ", 2)
        code = int(first, 16)
        for tok in ROW.findall(chars):
            unsure = tok.endswith("?") and len(tok) > 1
            ch = tok[:-1] if unsure else tok
            if code in out.setdefault(font, {}):
                raise ValueError(f"kanji_rows.txt:{n}: code {code:X} of {font} given twice")
            out[font][code] = (ch, unsure)
            code += 1
    return out


def common():
    t = {}
    for line in (ROOT / "tbl" / "jp_common.tbl").read_text(encoding="utf-8").splitlines():
        if line and not line.startswith("#"):
            k, v = line.split("=", 1)
            b = bytes.fromhex(k)
            t[b[0] | b[1] << 8] = v
    t[0] = "　"  # blank cell (R08 quiz indents, ST.BIN choice items); menu extractors strip 0x0000 padding first
    return t


def glyphs(font):
    d = (FM16 / f"{font}.BIN").read_bytes()
    return [d[i:i + 128] for i in range(0, len(d), 128)]


def room_rows(font, rows=None):
    """Readings for a room font; a font with no rows of its own (M16_R14) borrows them by identical bitmap."""
    rows = rows or load_rows()
    if font in rows:
        return rows[font]
    known = {}
    for f, r in rows.items():
        if f != "CG":
            for i, g in enumerate(glyphs(f)):
                if 0x1A4 + i in r:
                    known.setdefault(g, r[0x1A4 + i])
    return {0x1A4 + i: known[g] for i, g in enumerate(glyphs(font)) if g in known}


def table(font=None):
    """code -> text for the common font plus one room font (None = common only). A glyph repeating a character
    already tabled (the fonts hold real duplicates: R02 先 twice) decodes as [XXXX:字] so it still roundtrips."""
    t = common()
    if font:
        seen = set(t.values())
        for code, (ch, _) in sorted(room_rows(font).items()):
            t[code] = "[%04X:%s]" % (code, ch) if ch in seen else ch
            seen.add(ch)
    return t


class Codec:
    """Word codec. newline: the code shown as a real newline (0x1000 in room scripts, 0x9999 in menus/battle)."""

    def __init__(self, tab, newline=0x1000, names=None):
        self.dec = dict(tab)
        self.dec[newline] = "\n"
        for code, name in (names or {}).items():
            self.dec[code] = "{%s}" % name
        self.enc = {}
        for code, s in self.dec.items():
            self.enc.setdefault(s, code)
        self.maxlen = max(map(len, self.enc))

    def decode(self, data):
        out = []
        for i in range(0, len(data) - 1, 2):
            w = data[i] | data[i + 1] << 8
            s = self.dec.get(w)
            out.append(s if s is not None and self.enc[s] == w else "[%04X]" % w)
        return "".join(out)

    def encode(self, text):
        out, i = bytearray(), 0
        while i < len(text):
            m = TOKEN.match(text, i)
            if m:
                w = int(m[1], 16)
                i = m.end()
            else:
                for k in range(min(self.maxlen, len(text) - i), 0, -1):
                    if text[i:i + k] in self.enc:
                        w = self.enc[text[i:i + k]]
                        i += k
                        break
                else:
                    raise ValueError(f"unencodable {text[i]!r} at {i} in {text!r}")
            out += bytes((w & 0xFF, w >> 8))
        return bytes(out)


def report():
    """Readings to check: unsure marks, characters read twice in one font, identical bitmaps read differently."""
    rows = load_rows()
    by_bitmap = {}
    for font, r in rows.items():
        if font == "CG":
            continue
        gl = glyphs(font)
        assert len(gl) == len(r), f"{font}: {len(gl)} glyphs, {len(r)} readings"
        chars = {}
        for code, (ch, unsure) in sorted(r.items()):
            by_bitmap.setdefault(gl[code - 0x1A4], set()).add(ch)
            if ch in chars and ch not in ("{blank}",):
                print(f"{font} {code:X} {ch}: also {chars[ch]:X}")
            chars.setdefault(ch, code)
    for g, chs in by_bitmap.items():
        if len(chs) > 1:
            print("same bitmap, read as", "/".join(sorted(chs)))
    r14 = room_rows("M16_R14", rows)
    print("M16_R14 unread:", " ".join("%X" % (0x1A4 + i) for i in range(len(glyphs("M16_R14"))) if 0x1A4 + i not in r14))
    uns = [(f, c, ch) for f, r in rows.items() for c, (ch, u) in r.items() if u]
    print(len(uns), "unsure:", " ".join(f"{f[-3:]}:{c:X}{ch}" for f, c, ch in uns))


def doubt_sheet(items, out, zoom=5, cols=12):
    """PNG of (font, code) glyphs, labelled 'Rxx:code reading', for a second look at doubtful readings."""
    import numpy as np
    from PIL import Image, ImageDraw
    sys.path.insert(0, str(ROOT / "tools"))
    from kanjiocr import glyph
    rows = load_rows()
    cw, chh = 16 * zoom + 24, 16 * zoom + 14
    img = Image.new("L", (cols * cw, (len(items) + cols - 1) // cols * chh), 255)
    dr = ImageDraw.Draw(img)
    for k, (font, code) in enumerate(items):
        data = (FM16 / f"{'MSG_CG' if font == 'CG' else font}.BIN").read_bytes()
        g = glyph(data, code + 0xA6 if font == "CG" else code - 0x1A4)
        cell = Image.fromarray((255 - g * 255).astype(np.uint8)).resize((16 * zoom, 16 * zoom), Image.NEAREST)
        x, y = (k % cols) * cw, (k // cols) * chh
        img.paste(cell, (x + 4, y + 12))
        dr.text((x + 4, y), "%d %s:%X" % (k, font[-3:], code), fill=0)
    img.save(out)
    print(out, len(items))


def contexts(want=None, n=3, width=6):
    """Up to n decoded uses (+-width chars) of every unsure room/common reading, or of `want` {(font, code)}
    (font 'CG' = common), to settle a reading from the words around it."""
    import rooms
    rows = load_rows()
    uses, codecs = {}, {}
    for name in rooms.OVERLAYS:
        data = (rooms.FPRG / f"{name}.BIN").read_bytes()
        for o, nw, _, _ in rooms.pages(data):
            f = rooms.font(name, o)
            r = {**{c: v for c, v in rows["CG"].items()}, **rows.get(f, {})}
            c = codecs.setdefault(f, Codec(table(f)))
            toks = [c.decode(data[o + 2 * k:o + 2 * k + 2]).replace("\n", "/") for k in range(nw)]
            for k, code in enumerate(rooms.words(data[o:o + 2 * nw])):
                key = ("CG" if code < 0x1A4 else f, code)
                hit = key in want if want else code in r and r[code][1]
                if hit and len(uses.setdefault((f, code), [])) < n:
                    toks[k] = "<" + toks[k] + ">"
                    uses[(f, code)].append(f"{name}:{o:X} " + "".join(toks[max(0, k - width):k + width + 1]))
                    toks[k] = toks[k][1:-1]
    for (f, code), u in sorted(uses.items()):
        if u:
            print(f"{f[-3:]}:{code:X} {rows['CG' if code < 0x1A4 else f][code][0]}  |  " + "  |  ".join(u))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "ctx":  # jtext.py ctx [R04:1E1 CG:121 ...]
        sys.path.insert(0, str(ROOT / "tools"))
        contexts({("CG" if f == "CG" else "M16_" + f, int(c, 16)) for f, c in (a.split(":") for a in sys.argv[2:])},
                 n=6, width=10) if sys.argv[2:] else contexts()
    elif len(sys.argv) > 2 and sys.argv[1] == "sheet":  # jtext.py sheet OUT.png R00:1F8 CG:121 ...
        doubt_sheet([("CG" if f == "CG" else "M16_" + f, int(c, 16)) for f, c in
                     (a.split(":") for a in sys.argv[3:])], sys.argv[2])
    else:
        sys.exit(report())
