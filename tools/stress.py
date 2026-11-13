"""stress.py: width-gate stress build. Overrides a few ep01 opening pages (in place) with lines that probe the
dialogue box limits, builds build/stress.bin and runs the talk01 warp (tools/debug/scenes.txt) on it.

    python -X utf8 tools/stress.py [--no-run]      -> work/qa/p5/stress/talk01/f*.png + sheet

Pages (R01, shown one per circle press in talk01): 0E762 one 17-cell line (is cell 17 drawn?), 0E798 six lines
(how many per page?), 0E7CA + 0E820 the glyph torture line (all printable ASCII, then double spaces), 0E88E a full
17-cell third line (does the ▼ prompt overlap it?).
"""
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

if __name__ == "__main__":
    b, cue = build.build(name="stress", qa=STRESS)
    print(b, build.sha1(b))
    if "--no-run" not in sys.argv:
        sys.exit(subprocess.call([sys.executable, "-X", "utf8", str(ROOT / "tools/debug/warp_all.py"), "--rom", str(cue),
                                  "--only", "talk01", "--out", str(ROOT / "work/qa/p5/stress"),
                                  "--states", str(ROOT / "work/qa/p5/stress/states")]))
