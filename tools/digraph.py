"""digraph.py: English for the 16x16 text fonts as pre-rendered two-letter cells (docs/re/font.md).

Each 16x16 glyph cell of MSG_CG / M16_Rxx / CNF_MSG holds two 8x16 letters (Spleen 8x16, fonts/, BSD-2-Clause),
so a 16-px code carries two characters and every renderer and fixed field keeps working with no code change.
  python -X utf8 tools/digraph.py sheet OUT.png "text"   render a string the way the game will (for checking)

cell(pair) -> 128 bytes in the game's glyph format (4bpp, low nibble first, 8 bytes per row): body colour BODY,
drop shadow SHADOW one pixel right and down, like the original glyphs.
"""
import sys
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BDF = ROOT / "fonts" / "spleen-8x16.bdf"
BODY, SHADOW = 0x1, 0xE  # MSG_CG: 1 = glyph body, D/E = the dark edge right and below (read from Ａ, 0xD1)


@lru_cache(None)
def letters():
    """{char: 16 row bytes, bit 7 = leftmost pixel} for printable ASCII."""
    out, cur, rows = {}, None, None
    for line in BDF.read_text(encoding="ascii").splitlines():
        if line.startswith("ENCODING"):
            cur = int(line.split()[1])
        elif line.startswith("BBX"):
            assert line.split()[1:] == ["8", "16", "0", "-4"], line
        elif line == "BITMAP":
            rows = []
        elif line == "ENDCHAR":
            if 0x20 <= cur < 0x7F:
                out[chr(cur)] = bytes(rows)
            rows = None
        elif rows is not None:
            rows.append(int(line, 16) & 0xFE)  # 8th column off (only T and * use it): room for the shadow
    return out


def pixels(pair):
    """16x16 list of colour indices for a 1- or 2-char string (a lone char takes the left half)."""
    px = [[0] * 16 for _ in range(16)]
    for half, ch in enumerate(pair.ljust(2)):
        rows = letters()[ch]
        for y in range(16):
            for x in range(8):
                if rows[y] >> (7 - x) & 1:
                    px[y][half * 8 + x] = BODY
    return shadowed(px)


# Monpet element glyphs MSG_CG 0xB0-0xB2 水/雷/火: one 16x16 cell drawn by FDS code (0x801029A4 list, 0x80102C44
# detail), no room for a word there, so they become element icons (water drop, lightning bolt, flame).
ICONS = {
    0xB0: ["       ##       ", "       ##       ", "      ####      ", "      ####      ", "     ######     ",
           "    ########    ", "    ########    ", "   ##########   ", "   ##########   ", "  ############  ",
           "  ### #######   ", "  ### ######    ", "   ### ####     ", "    #######     ", "     #####      ",
           "                "],
    0xB1: ["        #####   ", "       #####    ", "      #####     ", "     #####      ", "    #####       ",
           "   ##########   ", "  ##########    ", "       #####    ", "      #####     ", "     #####      ",
           "    ####        ", "   ###          ", "  ##            ", " #              ", "                ",
           "                "],
    0xB2: ["       #        ", "       ##       ", "      ###   #   ", "      ####  ##  ", "  #  #####  ##  ",
           "  ## ###### ##  ", "  ############# ", " ############## ", " #####  ####### ", " ####    ###### ",
           " ####     ##### ", " ####  #  ##### ", "  ### ###  ###  ", "   ##########   ", "     ######     ",
           "                "],
}


def icon(code):
    """128 bytes (cell format) for an ICONS entry, shadowed like the letters."""
    px = shadowed([[BODY if c == "#" else 0 for c in row] for row in ICONS[code]])
    return bytes(px[y][x] | px[y][x + 1] << 4 for y in range(16) for x in range(0, 16, 2))


def shadowed(px):
    for y in range(15, -1, -1):  # shadow where the body pixel up-left of it is set
        for x in range(15, -1, -1):
            if not px[y][x] and y and x and px[y - 1][x - 1] == BODY:
                px[y][x] = SHADOW
    return px


def cell(pair):
    px = pixels(pair)
    return bytes(px[y][x] | px[y][x + 1] << 4 for y in range(16) for x in range(0, 16, 2))


def pairs(text):
    """Split one line into the two-char cells it is drawn with."""
    return [text[i:i + 2] for i in range(0, len(text), 2)]


def sheet(out, text, zoom=3):
    from PIL import Image
    lines = text.split("\n")
    w = max(len(pairs(l)) for l in lines) * 16
    im = Image.new("RGB", (w, 16 * len(lines)), (40, 40, 80))
    col = {BODY: (255, 255, 255), SHADOW: (0, 0, 0)}
    for ly, line in enumerate(lines):
        for i, p in enumerate(pairs(line)):
            for y, row in enumerate(pixels(p)):
                for x, c in enumerate(row):
                    if c:
                        im.putpixel((i * 16 + x, ly * 16 + y), col[c])
    im.resize((im.width * zoom, im.height * zoom), Image.NEAREST).save(out)


def selftest():
    assert len(letters()) == 95
    for ch, rows in letters().items():  # bit 0 = 8th column: a letter there would touch its neighbour (shadow)
        assert all(not r & 1 for r in rows), f"{ch!r} uses the 8th column"
    assert len(cell("ab")) == 128 and cell("  ") == bytes(128)


if __name__ == "__main__":
    selftest()
    if sys.argv[1:2] == ["sheet"]:
        sheet(sys.argv[2], sys.argv[3].replace("\\n", "\n"))
