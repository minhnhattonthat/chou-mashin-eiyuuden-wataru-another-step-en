"""stress.py: width-gate stress builds (docs/re/windows.md). Lines override script entries via build.py's qa
(in place, or '+ID' = run past the slot over the strings after it), then the warps that show them run.

    python -X utf8 tools/stress.py [--no-run]        dialogue box   -> work/qa/p5/stress/talk01
    python -X utf8 tools/stress.py --ui [--no-run]   menus/battle   -> work/qa/p5/stress_ui/<scene>

Dialogue (R01, shown one per circle press in talk01): 0E762 one 17-cell line (is cell 17 drawn?), 0E798 six lines
(how many per page?), 0E7CA + 0E820 the glyph torture line (all printable ASCII, then double spaces), 0E88E a full
17-cell third line (does the ▼ prompt overlap it?).
UI: a ruler (cell n shows RULER[2n:2n+2], so the last pair drawn is the cell count) in every box the warps reach:
fixed fields filled to their slot, sized boxes run past their JP text.
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build  # noqa: E402

ASCII = "".join(map(chr, range(0x20, 0x7F))) + " "
STRESS = {
    "R01:0E762": "1:\n" + "0123456789ABCDEFGHIJKLMNOPQRSTUVWX",  # 17 cells
    # 6 lines (2026-11-14): lines 4+ draw outside the 3-line window buffer and garble every later page: 3 is the cap
    "R01:0E798": "L1\nL2\nL3456789ABCDEFGHIJKLMN",
    "R01:0E7CA": ASCII[:32] + "\n" + ASCII[32:64],
    "R01:0E820": ASCII[64:] + "\n" + "a  b  c",
    "R01:0E88E": "3:\n2nd line\n" + "abcdefghijklmnopqrstuvwxyzABCDEFGH",
}
RULER = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghij"  # pairs = the marker build's digit and filler pairs


def ui():
    """Overrides for the menu and battle boxes."""
    qa = {
        # ふいうち！ battle message: the box is cells*16+32 px, centred (22 cells ran off both edges): 18 = 320 px
        "+BALLBAT:226C0": RULER[:36],
        "+TTL:054EC": RULER[:20],  # config label Ｒ１ボタン: 10 cells, does it reach the value column?
        "+TTL:05550": RULER[:32],  # config value なんでやねん: 16 cells to the screen edge
        "+FDS:18550": RULER[:32],  # field config voice list, first row: 16 cells
        # IQ battle box: the rules choice page two presses in (iq_page2; both gender variants, 25 words in place):
        # 19 cells + 2 short lines. Never spill ST:00140: a jump table follows at 0x150 (the game hung)
        "ST:00174": RULER[:38] + "\nL2\nL3",
        "ST:001A8": RULER[:38] + "\nL2\nL3",
    }
    for name in ["fds_places", "exe_key_item_desc", "exe_mashin_attacks"] + ["ene/" + p.stem for p in sorted((ROOT / "script/ene").glob("*.json"))]:
        for e in json.loads((ROOT / "script" / (name + ".json")).read_text(encoding="utf-8"))["entries"]:
            if e["jp"].strip("　\n"):  # fixed field: fill the slot (bname: one letter per 8x16 cell)
                qa[e["id"]] = RULER[:e["max"] * (1 if e.get("kind") == "bname" else 2)]
    qa["ENE01:034A4"] = RULER[:6]  # 3 cells: does the header (bname 034C8, 11 letters) stop at this record's count?
    return qa


if __name__ == "__main__":
    if "--ui" in sys.argv:
        qa, name, out, only = ui(), "stress_ui", "stress_ui", "battle_ball,title_config,menu_config,menu,menu_key,iq_page2,mashin_attack"
    else:
        qa, name, out, only = STRESS, "stress", "stress", "talk01"
    b, cue = build.build(name=name, qa=qa)
    print(b, build.sha1(b))
    if "--no-run" not in sys.argv:
        o = ROOT / "work/qa/p5" / out
        sys.exit(subprocess.call([sys.executable, "-X", "utf8", str(ROOT / "tools/debug/warp_all.py"), "--rom", str(cue),
                                  "--only", only, "--out", str(o), "--states", str(o / "states")]))
