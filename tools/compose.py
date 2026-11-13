"""compose.py: English glyphs composed at run time from two 8x16 letters (docs/re/font.md, "Pair composer").

Every 16x16 glyph reaches VRAM through LoadImage (EXE 0x80072074, a0 = RECT*, a1 = src), src = 0x80115300 + code*128.
English pair codes are PAIR_FIRST.. (one per distinct two-letter cell in the whole script, assigned by insert.py),
whose src lands past every real font. A hook at LoadImage's entry sees a 16x16 4bpp upload (w 4, h 16) from that
range, looks the pair up in TABLE (u16: left letter | right letter << 8, letter = ASCII - 0x20), copies the two
8x16 letters (4 bytes per row each, FONT) side by side into the next RING slot and uploads that instead. LoadImage
is queued, so a slot must outlive the queue: RING_N slots, more than libgpu's 64 queue entries.

Data (FONT, RING, TABLE) sits in MSG_CG's kanji slots (codes 0xE6-0x1A3, unused once the text is English; the
prompt glyph 0x181 stays) and the same offsets of CNF_MSG (the config screen's copy at the same address). The hook
code and the ring index live in the EXE (an all-zero run), so a LoadImage before MSG_CG is loaded never reads
them: non-glyph uploads fall straight through.
"""
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import digraph  # noqa: E402

GLYPH_BASE = 0x80115300
PAIR_FIRST = 0x263  # past the room fonts (0x1A4-0x262)
SRC_LO, SRC_HI = GLYPH_BASE + PAIR_FIRST * 128, GLYPH_BASE + 0x1000 * 128  # codes 0x1000+ are controls
FONT_RAM = 0x80110000  # MSG_CG / CNF_MSG load address (file offset = RAM - FONT_RAM)
FONT = 0x8011C600  # code 0xE6's glyph: 95 letters x 64 bytes
RING = FONT + 95 * 64
RING_N = (0x80121380 - RING) // 128  # up to the ▼ prompt glyph (code 0x181)
TABLE = 0x80121400  # code 0x182's glyph .. the room font at 0x80122500
TABLE_MAX = (0x80122500 - TABLE) // 2
EXE_BASE = 0x80018000 - 0x800  # EXE file offset = RAM - EXE_BASE
POS = 0x8009882C  # ring index (u32); EXE zero run 0x8009882C-0x80098C3F, no writes seen (font.md)
HOOK = POS + 4
LOADIMAGE = 0x80072074
LOADIMAGE_HEAD = (0x27BDFFE0, 0xAFB00010)  # addiu sp,sp,-0x20 ; sw s0,0x10(sp)

R = {n: i for i, n in enumerate("zero at v0 v1 a0 a1 a2 a3 t0 t1 t2 t3 t4 t5 t6 t7 s0 s1 s2 s3 s4 s5 s6 s7 t8 t9 "
                                "k0 k1 gp sp fp ra".split())}


def _i(op, rs, rt, imm):
    return op << 26 | R[rs] << 21 | R[rt] << 16 | imm & 0xFFFF


def _r(funct, rs="zero", rt="zero", rd="zero", sh=0):
    return R[rs] << 21 | R[rt] << 16 | R[rd] << 11 | sh << 6 | funct


def hi_lo(addr):
    """(hi, lo) for lui hi + signed lo."""
    lo = addr & 0xFFFF
    return (addr + 0x8000) >> 16 & 0xFFFF, lo


def assemble(prog, base):
    """prog: list of (op, args..) or a label string -> list of u32."""
    labels, pc = {}, base
    for ins in prog:
        if isinstance(ins, str):
            labels[ins] = pc
        else:
            pc += 4
    out, pc = [], base
    for ins in prog:
        if isinstance(ins, str):
            continue
        op, *a = ins
        if op in ("beq", "bne"):
            off = (labels[a[2]] - pc - 4) >> 2
            w = _i(4 if op == "beq" else 5, a[0], a[1], off)
        elif op == "j":
            w = 2 << 26 | (a[0] & 0x0FFFFFFF) >> 2
        elif op in ("lui",):
            w = _i(0x0F, "zero", a[0], a[1])
        elif op in ("addiu", "ori", "andi", "sltiu"):
            w = _i({"addiu": 9, "ori": 0x0D, "andi": 0x0C, "sltiu": 0x0B}[op], a[1], a[0], a[2])
        elif op in ("lw", "lhu", "sw"):
            w = _i({"lw": 0x23, "lhu": 0x25, "sw": 0x2B}[op], a[2], a[0], a[1])
        elif op in ("sll", "srl"):
            w = _r(0 if op == "sll" else 2, rt=a[1], rd=a[0], sh=a[2])
        elif op in ("addu", "subu", "sltu", "or"):
            w = _r({"addu": 0x21, "subu": 0x23, "sltu": 0x2B, "or": 0x25}[op], rs=a[1], rt=a[2], rd=a[0])
        elif op == "nop":
            w = 0
        else:
            raise ValueError(op)
        out.append(w)
        pc += 4
    return out


def hook_words():
    th, tl = hi_lo(TABLE)
    fh, fl = hi_lo(FONT)
    ph, pl = hi_lo(POS)
    rh, rl = hi_lo(RING)
    prog = [
        ("lui", "t0", SRC_LO >> 16), ("ori", "t0", "t0", SRC_LO & 0xFFFF),
        ("sltu", "t1", "a1", "t0"), ("bne", "t1", "zero", "out"),
        ("lui", "t2", SRC_HI >> 16),
        ("ori", "t2", "t2", SRC_HI & 0xFFFF), ("sltu", "t1", "a1", "t2"), ("beq", "t1", "zero", "out"),
        ("lhu", "t3", 4, "a0"),  # w (not used at "out": no load-delay hazard)
        ("lhu", "t4", 6, "a0"),  # h
        ("addiu", "t3", "t3", -4), ("bne", "t3", "zero", "out"),
        ("addiu", "t4", "t4", -16),
        ("bne", "t4", "zero", "out"),
        ("subu", "t1", "a1", "t0"),
        ("srl", "t1", "t1", 7), ("sll", "t1", "t1", 1),
        ("lui", "t2", th), ("addu", "t1", "t1", "t2"), ("lhu", "t1", tl, "t1"),  # pair: left | right << 8
        ("lui", "t2", fh), ("addiu", "t2", "t2", fl),
        ("andi", "t3", "t1", 0xFF), ("sll", "t3", "t3", 6), ("addu", "t3", "t3", "t2"),
        ("srl", "t4", "t1", 8), ("sll", "t4", "t4", 6), ("addu", "t4", "t4", "t2"),
        ("lui", "t5", ph), ("lw", "t6", pl, "t5"), ("nop",),
        ("addiu", "t7", "t6", 1), ("sltiu", "t8", "t7", RING_N), ("bne", "t8", "zero", "keep"), ("nop",),
        ("or", "t7", "zero", "zero"),
        "keep",
        ("sw", "t7", pl, "t5"),
        ("sll", "t6", "t6", 7), ("lui", "t5", rh), ("addiu", "t5", "t5", rl), ("addu", "t6", "t6", "t5"),
        ("or", "a1", "t6", "zero"), ("addiu", "t9", "t6", 128),
        "row",
        ("lw", "t1", 0, "t3"), ("lw", "t2", 0, "t4"), ("addiu", "t3", "t3", 4), ("addiu", "t4", "t4", 4),
        ("sw", "t1", 0, "t6"), ("sw", "t2", 4, "t6"), ("addiu", "t6", "t6", 8),
        ("bne", "t6", "t9", "row"), ("nop",),
        "out",
        ("addiu", "sp", "sp", -0x20), ("j", LOADIMAGE + 8), ("sw", "s0", 0x10, "sp"),  # LoadImage's first two
    ]
    return assemble(prog, HOOK)


def patch_words():
    """LoadImage's first two instructions -> j HOOK ; nop."""
    return [2 << 26 | (HOOK & 0x0FFFFFFF) >> 2, 0]


def letter(ch):
    """8x16 letter tile, 4 bytes per row (the left half of digraph's cell: same pixels, shadow included)."""
    px = digraph.pixels(ch)
    return bytes(px[y][x] | px[y][x + 1] << 4 for y in range(16) for x in range(0, 8, 2))


def font_bytes():
    return b"".join(letter(chr(c)) for c in range(0x20, 0x7F))


def table_bytes(pairs):
    """pairs in code order (PAIR_FIRST + i) -> TABLE bytes."""
    assert len(pairs) <= TABLE_MAX, f"{len(pairs)} letter pairs, the table holds {TABLE_MAX}"
    return b"".join(struct.pack("<BB", ord(p[0]) - 0x20, ord(p[1]) - 0x20) for p in pairs)


def compose(pair):
    """What the hook builds for a pair (for tests): 128 bytes."""
    f = font_bytes()
    a, b = (ord(c) - 0x20 for c in pair)
    return b"".join(f[a * 64 + r * 4:a * 64 + r * 4 + 4] + f[b * 64 + r * 4:b * 64 + r * 4 + 4] for r in range(16))


assert RING_N > 64 and FONT + 95 * 64 <= RING and RING + RING_N * 128 <= 0x80121380
