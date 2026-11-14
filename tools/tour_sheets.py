"""tour_sheets.py: full-scale contact sheets of every warp scene, for visual QA.

    python -X utf8 tools/tour_sheets.py [--src work/qa/warp] [--out work/qa/tour]

emu.py --sheet halves every frame (sheet.py --div 2): the 6x12 / 8x16 English strokes break up at that scale and
reviewers flag clean labels as garbled. This writes <out>/<scene>/sheet*.png at --div 1 (8 tiles a page) from the
frames a warp_all.py run left in <src>/<scene>/. Run it on the EN tour and on the original's (work/qa/tour_jp ->
work/qa/tour_jp_full), then qa_gate.py init on <out>.
"""
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from skill import SKILL  # noqa: E402


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--src", default=str(ROOT / "work" / "qa" / "warp"))
    p.add_argument("--out", default=str(ROOT / "work" / "qa" / "tour"))
    a = p.parse_args()
    bad = 0
    for d in sorted(x for x in Path(a.src).iterdir() if x.is_dir() and any(x.glob("f*.png"))):
        out = Path(a.out) / d.name
        out.mkdir(parents=True, exist_ok=True)  # sheet.py doesn't create --out's directory
        r = subprocess.run([sys.executable, "-X", "utf8", str(Path(SKILL) / "scripts" / "sheet.py"), str(d),
                            "--div", "1", "--max", "8", "--cols", "4", "--out", str(out / "sheet.png")],
                           capture_output=True, text=True)
        if r.returncode:
            bad += 1
            print(d.name, r.stderr[-200:])
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
