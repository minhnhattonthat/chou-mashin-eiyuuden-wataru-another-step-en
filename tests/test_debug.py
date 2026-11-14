import importlib.util
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import loadcalls  # noqa: E402

_spec = importlib.util.spec_from_file_location("warp_all", ROOT / "tools" / "debug" / "warp_all.py")
warp_all = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(warp_all)


def test_scene_list_parses_and_names_are_unique():
    sc = warp_all.scenes(ROOT / "tools" / "debug" / "scenes.txt")
    names = [n for n, _ in sc]
    assert len(names) == len(set(names))
    want = {"title_menu", "title_config", "ep00", "ep14", "menu", "shop", "save", "battle_ball", "battle_mashin",
            "battle_iq", "levelup", "ending", "credits"}
    assert want <= set(names)
    for n, opts in sc:
        assert all(k in {"ep", "stop", "idle", "poke", "mode", "press", "atmode", "atstate", "room", "hold",
                         "frames", "every", "timeout", "wait", "mash", "mashkey", "god", "pokeloop", "late", "chest"} for k in opts), n


def test_room_match_needs_a_near_exact_head(tmp_path):
    (tmp_path / "R00.BIN").write_bytes(bytes(range(256)))
    (tmp_path / "R01.BIN").write_bytes(bytes(255 - i for i in range(256)))
    head = bytearray(range(256))
    head[0] = 0xEE  # one byte changed at runtime still matches
    assert warp_all.room_match(head.hex(), tmp_path) == "R00"
    assert warp_all.room_match(bytes(256).hex(), tmp_path) == "?"


def test_loadcalls_reads_index_from_delay_slot():
    jal = 0x0C000000 | ((loadcalls.LOAD & 0x0FFFFFFF) >> 2)
    code = struct.pack("<4I", 0, jal, 0x24040031, 0)  # jal load; addiu a0,zero,0x31
    assert list(loadcalls.calls(code, 0x800D0000)) == [(0x800D0004, 0x31)]
