"""rooms.py: locate every text page in the room overlays FPRG/R00-R14.BIN (docs/re/text.md "Room scripts").

A page is a run of text words (codes 0x0000-0x0261, 0x1000 newline; 0x0000 is a blank cell: the R08 music quiz
indents its choices with it) ended by a terminator word 0xN000 (N 2-F but B), which stays out of `jp`:
  0x2000 next page, 0x3000 end of message, 0x4000 after a choice list (answer text follows),
  0x8000 + 1 arg word, 0xA000 + args (item get), 0xC000/0xD000/0xF000 + args (event commands after the text).
  0xB000 n inside a page is an inline control (INLINE), kept in `jp` as a [B000][xxxx] pair.
A page counts as text when what precedes it is a page header (verified static, 2026-11-14):
  - event-bytecode pages (message banks, reached by the EXE switch at 0x800321A0, CASES below):
    `FFFF .. 7FFF` <text>, `FFFF .. 7FFF 01xx face voice` <text> (0x01xx = portrait command, 2 args), or
    `FFFF 0000 <id 0x1000+>` <text>;
  - follow-on pages: right after another page's terminator;
  - NPC talk: targets of u32 pointers (the first one after 0x0000 padding);
  - blocks whose address the overlay's own code builds (lui/addiu: R08 0x163C0, R13 0x16780, R14 0x1BCA0).

    python -X utf8 tools/rooms.py     counts per overlay and every text-like run no page covers
"""
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import msgscan  # noqa: E402
import importlib.util  # noqa: E402

_spec = importlib.util.spec_from_file_location("mipsre", Path(__file__).parent / "re.py")  # tools/re.py, not stdlib re
_mipsre = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mipsre)
re_consts = _mipsre.consts

ROOT = Path(__file__).resolve().parents[1]
FPRG = ROOT / "work" / "disc" / "tree" / "FPRG"
BASE = 0x800CE000
# episode index -> (overlay, idx table, bank pointer array), RAM addresses built in each switch case
CASES = [("R00", 0x800DC5E4, 0x800DC5D8), ("R01", 0x800DE900, 0x800DE8CC), ("R02", 0x800E39D0, 0x800E3994),
         ("R03", 0x800DDB90, 0x800DDB74), ("R04", 0x800E3FCC, 0x800E3FA0), ("R05", 0x800E1838, 0x800E1814),
         ("R06", 0x800E6E6C, 0x800E6E3C), ("R07", 0x800E8C0C, 0x800E8BC8), ("R08", 0x800E8C40, 0x800E8C00),
         ("R09", 0x800DFAC0, 0x800DFA90), ("R10", 0x800DBFEC, 0x800DBFBC), ("R11", 0x800DED70, 0x800DED28),
         ("R13", 0x800ECDB0, 0x800ECD9C), ("R13", 0x800E9248, 0x800E9210), ("R14", 0x800EDEB4, 0x800EDE7C)]
OVERLAYS = sorted({c[0] for c in CASES})
NL, PORTRAIT = 0x1000, 0x0100
TERMS = tuple(n << 12 for n in range(2, 16) if n != 0xB)  # 0x7000/0x9000: R08 music-quiz layout (0x16700)
# args after a terminator; they can read as text (R08 0x1670A `8000 ご 7000`), so a page never starts on them
TERM_ARGS = {0x4000: 1, 0x8000: 1, 0xC000: 2, 0xF000: 1}  # 4000 n: R00 0x1129E `4000 01B0 ボーリング..`
TEXT = set(range(0, 0x262)) | {NL}  # 0x0000 = blank cell
INLINE = {0xB000: 1}  # in-page control + arg count: B000 n (guess: wait n frames; R03 0xE3A2 after a speaker name)


def font(name, offset):
    """Room font for a page: by episode index (jtext.EPISODE_FONT); R13.BIN is shared by episodes 12 and 13.
    R13 split (2026-11-14): pages using codes > 0x204 (past M16_R12's 97 glyphs) all fall outside the ep-12 ranges,
    and 【】 decode as M16_R12 0x1F8/0x1F9 inside them: ep-12 banks 0x1DAB0+ up to the ep-13 NPC block at 0x212D8,
    and the ep-12 NPC block from 0x22D78. The shared minigame block at 0x16780 has no room kanji."""
    from jtext import EPISODE_FONT
    if name == "R13":
        return "M16_R12" if 0x1DAB0 <= offset < 0x212D8 or offset >= 0x22D78 else "M16_R13"
    return EPISODE_FONT[[c[0] for c in CASES].index(name)]


def words(data):
    return struct.unpack_from("<%dH" % (len(data) // 2), data)


def banks(ep):
    """Sorted distinct file offsets of episode `ep`'s message banks."""
    name, idx, arr = CASES[ep]
    data = (FPRG / f"{name}.BIN").read_bytes()
    ptrs = struct.unpack_from("<%dI" % ((idx - arr) // 4), data, arr - BASE)
    return sorted({p - BASE for p in ptrs if p})


def pointers(data):
    """{target file offset: [slot offsets]} for every aligned u32 that points inside the overlay."""
    out = {}
    for k in range(0, len(data) - 3, 4):
        p = struct.unpack_from("<I", data, k)[0] - BASE
        if 0 <= p < len(data):
            out.setdefault(p, []).append(k)
    return out


def after_command(w, i):
    """`A000|D000.. args FFFF` right before i: a message that follows an event command (up to 4 arg words)."""
    return w[i - 1] == 0xFFFF and any(x in TERMS for x in w[max(0, i - 6):i - 1])


def pages(data):
    """[(offset, nwords, terminator, header)] of every text page; header = 'event', 'next' or 'ptr'."""
    w = words(data)
    ptr = pointers(data)
    code = {a - BASE for _, a in re_consts(data, BASE)}
    bank_starts = {o for ep, c in enumerate(CASES) if (FPRG / f"{c[0]}.BIN").read_bytes() == data for o in banks(ep)}
    out = []
    ends = set()  # word index right after an accepted page's terminator and its args: where a 'next' page may start
    i = 1
    while i < len(w):
        if (w[i] in TEXT or w[i] in INLINE) and (w[i - 1] not in TEXT or i in ends):
            start = i
            if w[i - 1] == 0x7FFF and 0x0100 <= w[i] < 0x0200 and (w[i + 1] not in TEXT or w[i + 2] not in TEXT):
                start = i + 3  # `7FFF 01xx face voice` <text> (a line may start with a 0x01xx kanji: 龍神 0x142)
            elif i >= 2 and w[i - 2] == PORTRAIT and 0x0300 <= w[i - 1] < 0x1000:
                start = i + 1  # `0100 face voice` with a voice id that reads as text
            elif after_command(w, i):
                start = i + 1 if w[i] == 0 else i  # `A000|D000 args FFFF [0000]` <text>: message after an event command
            j = start
            while j < len(w):
                if w[j] in INLINE:
                    j += 1 + INLINE[w[j]]
                elif w[j] in TEXT:
                    j += 1
                else:
                    break
            if j > start and j < len(w) and w[j] in TERMS:
                lead = start
                while lead < j and w[lead] == 0:
                    lead += 1
                if lead > start and (2 * lead in ptr or 2 * lead - 16 in ptr) and w[start - 1] != 0x7FFF:
                    start = lead  # NPC message after 0x0000 padding (the pointer may aim at the 16 zero bytes)
                    ptr.setdefault(2 * lead, [])
                if (w[start - 1] == 0x7FFF or (start >= 4 and 0x0100 <= w[start - 3] < 0x0200 and w[start - 4] == 0x7FFF)
                        or (start >= 3 and w[start - 1] >= 0x1000 and w[start - 2] == 0 and w[start - 3] == 0xFFFF)
                        or after_command(w, i)):
                    hdr = "event"
                elif start in ends:
                    hdr = "next"
                elif sum(1 <= x <= 0xAD for x in w[start:j]) < 2 or 2 * start in bank_starts or w[start] == 0 and 2 * start + 2 not in ptr:
                    hdr = None  # pointer targets must read as text: bank starts and table data don't
                elif 2 * start in ptr:
                    hdr = "ptr"
                elif 2 * start in code:
                    hdr = "code"
                else:
                    hdr = None
                if hdr and 2 * w[start:j].count(0) > j - start:
                    hdr = None  # mostly blank cells: MIPS code (R01 0x8E6), not a page
                if hdr and j > start:
                    out.append((2 * start, j - start, w[j], hdr))
                    i = j + 1 + TERM_ARGS.get(w[j], 0)
                    while i < len(w) and w[i] in TERMS:  # empty pages / command chains: `C000 a b 3000` <text>
                        i += 1 + TERM_ARGS.get(w[i], 0)
                    ends.add(i)
                    continue
            i = max(j, i + 1)
            continue
        i += 1
    return out


def uncovered(data, spans):
    """Text-like runs (msgscan) with 2+ words no span covers (one word may be a header id that reads as kana)."""
    cov = set()
    for o, n in spans:
        cov.update(range(o, o + 2 * n + 2, 2))
    msgscan.ENDS = (NL,) + TERMS
    return [(o, s) for o, s in msgscan.scan(data) if sum(o + 2 * k not in cov for k in range(len(s))) > 1]


def main():
    tot = 0
    for name in OVERLAYS:
        data = (FPRG / f"{name}.BIN").read_bytes()
        p = pages(data)
        tot += len(p)
        un = uncovered(data, [(o, n) for o, n, _, _ in p])
        print(name, "pages", len(p), "uncovered", len(un), " ".join("%X" % o for o, _ in un[:14]))
    print("total", tot)


if __name__ == "__main__":
    main()
