"""The LoadImage pair-compose hook (tools/compose.py), run under unicorn with exact-PC asserts."""
import struct
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import compose as C  # noqa: E402
import digraph  # noqa: E402

uc = pytest.importorskip("unicorn")
import faulthandler  # noqa: E402
faulthandler.disable()  # unicorn's mem_map raises a handled access violation on Windows: not a failure
from unicorn import mips_const as M  # noqa: E402

PAIRS = ["He", "ll", "o!", "  ", "~ "]
RECT = 0x80100000


class Mu:
    """unicorn's MIPS maps kseg0 (0x80000000+) onto physical 0: memory calls take physical addresses."""
    def __init__(self):
        self.u = uc.Uc(uc.UC_ARCH_MIPS, uc.UC_MODE_MIPS32 + uc.UC_MODE_LITTLE_ENDIAN)
        self.u.mem_map(0, 0x200000)

    def mem_write(self, a, data):
        self.u.mem_write(a & 0x1FFFFFFF, data)

    def mem_read(self, a, n):
        return self.u.mem_read(a & 0x1FFFFFFF, n)

    def __getattr__(self, k):
        return getattr(self.u, k)


def machine():
    mu = Mu()
    mu.mem_write(C.HOOK, struct.pack("<%dI" % len(C.hook_words()), *C.hook_words()))
    mu.mem_write(C.FONT, C.font_bytes())
    mu.mem_write(C.TABLE, C.table_bytes(PAIRS))
    mu.reg_write(M.UC_MIPS_REG_SP, 0x801F0000)
    mu.reg_write(M.UC_MIPS_REG_S0, 0x1234)
    return mu


def call(mu, src, w=4, h=16):
    mu.mem_write(RECT, struct.pack("<4H", 768, 256, w, h))
    mu.reg_write(M.UC_MIPS_REG_A0, RECT)
    mu.reg_write(M.UC_MIPS_REG_A1, src)
    end = C.LOADIMAGE + 8
    mu.emu_start(C.HOOK, end, count=2000)
    assert mu.reg_read(M.UC_MIPS_REG_PC) == end  # left through LoadImage's third instruction
    assert mu.reg_read(M.UC_MIPS_REG_SP) == 0x801F0000 - 0x20
    assert struct.unpack("<I", mu.mem_read(0x801F0000 - 0x20 + 0x10, 4))[0] == 0x1234  # sw s0 ran
    mu.reg_write(M.UC_MIPS_REG_SP, 0x801F0000)
    return mu.reg_read(M.UC_MIPS_REG_A1)


def test_composes_pairs_into_the_ring():
    mu = machine()
    for k, p in enumerate(PAIRS):
        out = call(mu, C.SRC_LO + k * 128)
        assert out == C.RING + k * 128
        assert bytes(mu.mem_read(out, 128)) == C.compose(p) == digraph.cell(p)


def test_other_uploads_pass_through():
    mu = machine()
    for src, w, h in [(C.SRC_LO - 128, 4, 16), (C.SRC_HI, 4, 16), (C.SRC_LO, 8, 16), (C.SRC_LO, 4, 32),
                      (0x80115300, 4, 16)]:
        assert call(mu, src, w, h) == src
    assert struct.unpack("<I", mu.mem_read(C.POS, 4))[0] == 0  # the ring didn't move


def test_ring_wraps():
    mu = machine()
    mu.mem_write(C.POS, struct.pack("<I", C.RING_N - 1))
    assert call(mu, C.SRC_LO) == C.RING + (C.RING_N - 1) * 128
    assert call(mu, C.SRC_LO + 128) == C.RING


def test_layout():
    assert C.RING_N > 64  # libgpu queues up to 64 LoadImages
    assert C.patch_words()[0] >> 26 == 2 and (C.patch_words()[0] & 0x3FFFFFF) << 2 == C.HOOK & 0x0FFFFFFF
    assert C.HOOK + 4 * len(C.hook_words()) <= 0x80098C40  # inside the EXE zero run
