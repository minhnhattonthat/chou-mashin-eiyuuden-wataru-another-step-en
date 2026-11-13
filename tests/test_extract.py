"""Phase 4: room text pages roundtrip through the codec and cover every text-like run (docs/re/text.md)."""
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import rooms  # noqa: E402
from jtext import Codec, load_rows, table  # noqa: E402

pytestmark = pytest.mark.skipif(not (rooms.FPRG / "R00.BIN").exists(), reason="disc not unpacked (tools/build.py)")


def waivers():
    out = {}
    for line in (ROOT / "tbl" / "room_data.txt").read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.startswith("#"):
            name, *offs = line.split()
            out[name] = {int(o, 16) for o in offs}
    return out


@pytest.mark.parametrize("name", rooms.OVERLAYS)
def test_room_pages(name):
    data = (rooms.FPRG / f"{name}.BIN").read_bytes()
    pages = rooms.pages(data)
    codecs = {}
    for o, n, term, _ in pages:
        f = rooms.font(name, o)
        c = codecs.setdefault(f, Codec(table(f)))
        text = c.decode(data[o:o + 2 * n])
        assert c.encode(text) == data[o:o + 2 * n], hex(o)
        assert not re.search(r"\[0[12][0-9A-F]{2}\]", text), f"{name} {o:#x}: code past the font: {text!r}"
    un = {o for o, _ in rooms.uncovered(data, [(o, n) for o, n, _, _ in pages])}
    assert un == waivers().get(name, set()), f"{name}: uncovered {sorted(map(hex, un))}"


@pytest.mark.parametrize("path", sorted((ROOT / "script").rglob("*.json")), ids=lambda p: p.stem)
def test_script_roundtrip(path):
    """Every jp in script/ re-encodes to the original bytes at its id's offset (zero padding for fixed fields)."""
    import json
    import extract
    from jtext import Codec
    doc = json.loads(path.read_text(encoding="utf-8"))
    data = (extract.TREE / doc["file"]).read_bytes()
    from jtext import battle_table
    menu, page, codecs = Codec(table(), newline=0x9999), Codec(table()), {}
    bfont = Codec(battle_table())
    for e in doc["entries"]:
        o = int(e["id"].split(":")[1], 16)
        if "font" in e:
            c = codecs.setdefault(e["font"], Codec(table("M16_" + e["font"])))
        elif e.get("kind") == "bfont":
            c = bfont
        else:
            c = menu if e.get("kind", "menu") == "menu" else page
        b = c.encode(e["jp"])
        if "max" in e:
            b += bytes(2 * e["max"] - len(b))
        b += bytes(2 * e.get("tail", 0))
        assert data[o:o + len(b)] == b, e["id"]


@pytest.mark.parametrize("name", ["EXE", "ST", "BALLBAT", "MACHINE", "TTL", "LVUP", "FDS"])
def test_menu_coverage(name):
    """Every text-like run in a menu source is inside an extracted entry or a tbl/menu_data.txt range."""
    import extract
    assert set(extract.STREAMS) == {"EXE", "ST", "BALLBAT", "MACHINE", "TTL", "LVUP", "FDS"}
    assert [hex(o) for o, _ in extract.uncovered(name)] == []


def test_menu_split():
    """Spot checks of the splits: glued fixed fields, records, battle-font names, kept cursor indent."""
    import json
    doc = {e["id"]: e for e in json.loads((ROOT / "script/BALLBAT.json").read_text(encoding="utf-8"))["entries"]}
    assert doc["BALLBAT:2156C"]["jp"] == "スポーツキャップ" and doc["BALLBAT:2157C"]["jp"] == "龍神のかんむり"
    assert "BALLBAT:21530" not in doc  # [u32 3, u32 ptr] record
    assert doc["BALLBAT:22830"] == {"id": "BALLBAT:22830", "kind": "bfont", "jp": "ホムライフル", "en": ""}
    assert doc["BALLBAT:252E0"]["jp"] == "リンリーン"  # a code ref mid-string must not cut
    st = {e["id"]: e for e in json.loads((ROOT / "script/ST.json").read_text(encoding="utf-8"))["entries"]}
    assert st["ST:00104"]["jp"].startswith("　バトルをつづける")


def test_kanji_rows_match_fonts():
    rows = load_rows()
    for font, r in rows.items():
        if font != "CG":
            n = len((ROOT / "work/disc/tree/FM16" / f"{font}.BIN").read_bytes()) // 128
            assert sorted(r) == list(range(0x1A4, 0x1A4 + n)), font
