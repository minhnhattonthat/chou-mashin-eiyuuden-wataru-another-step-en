import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import chg  # noqa: E402


def test_blocks_finds_clut_then_image_after_header_noise():
    clut = struct.pack("<4H", 0, 505, 256, 1) + bytes(512)
    img = struct.pack("<4H", 896, 0, 4, 8) + bytes(range(64))
    junk = struct.pack("<4H", 1, 2, 3, 4) + b"\x55" * 30  # typed-header chunk stand-in
    d = junk + clut + img + bytes(6)  # trailing zero padding
    assert chg.blocks(d) == [(len(junk), 0, 505, 256, 1), (len(junk) + len(clut), 896, 0, 4, 8)]
