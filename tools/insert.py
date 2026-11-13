"""insert.py: the build's edits, {disc path: new file bytes} (tools/build.py calls edits()).

Phase 5 engine spike: one ep01 page in place as digraph cells (tools/digraph.py), cells written over MSG_CG kanji
slots. The marker build and the real insert path replace this.
"""
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import digraph  # noqa: E402

TREE = ROOT / "work" / "disc" / "tree"
NL, END = 0x1000, 0x2000
CG_FIRST = 0xA6  # MSG_CG glyph index = code + 0xA6


def encode_cells(text, alloc):
    """Text -> 16-bit codes, one per two-char cell; alloc maps each new pair to a free code."""
    out = []
    for i, line in enumerate(text.split("\n")):
        if i:
            out.append(NL)
        out += [0 if p == "  " else alloc(p) for p in digraph.pairs(line)]
    return out


def edits():
    cg = bytearray((TREE / "FM16/MSG_CG.BIN").read_bytes())
    room = bytearray((TREE / "FPRG/R01.BIN").read_bytes())
    codes = {}

    def alloc(p):
        if p not in codes:
            c = 0xE6 + len(codes)  # spike: kanji slots of the common font
            codes[p] = c
            g = (c + CG_FIRST) * 128
            cg[g:g + 128] = digraph.cell(p)
        return codes[p]

    off = 0x0E7CA  # R01 page サクヤ：そういうおじさまだって… (35 words, then 2000)
    n = struct.unpack_from("<40H", room, off).index(END)
    assert n == 35, n
    words = encode_cells("Sakuya:\nThe quick brown fox jumped by\nthe lazy dog. 0123456789!?", alloc)
    assert len(words) <= n, len(words)
    words += [0] * (n - len(words))
    struct.pack_into(f"<{n}H", room, off, *words)
    return {"FM16/MSG_CG.BIN": bytes(cg), "FPRG/R01.BIN": bytes(room)}
