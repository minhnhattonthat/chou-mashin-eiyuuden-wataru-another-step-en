import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import importlib.util  # noqa: E402

_spec = importlib.util.spec_from_file_location("re_tool", Path(__file__).resolve().parents[1] / "tools" / "re.py")
re_tool = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(re_tool)


def test_consts_lui_addiu_signed_and_indexed():
    code = [
        0x3C03800A,  # lui v1,0x800a
        0x2463C9D0,  # addiu v1,v1,-0x3630 -> 0x8009C9D0
        0x3C01800A,  # lui at,0x800a
        0x00220821,  # addu at,at,v0 (index; base kept)
        0x8C22A3D4,  # lw v0,-0x5c2c(at) -> 0x8009A3D4
        0x3C04800D,  # lui a0,0x800d
        0x00402021,  # addu a0,v0,zero (a0 overwritten)
        0x24840010,  # addiu a0,a0,0x10: not a const
    ]
    got = list(re_tool.consts(struct.pack("<%dI" % len(code), *code), 0x80010000))
    assert got == [(0x80010004, 0x8009C9D0), (0x80010010, 0x8009A3D4)]
