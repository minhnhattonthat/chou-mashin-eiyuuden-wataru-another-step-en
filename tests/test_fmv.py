"""script/fmv.tsv: well-formed, ordered, no overlaps, at most 2 rows that fit the 320 px frame inside the margins."""
import sys
from pathlib import Path

from PIL import ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import fmv  # noqa: E402

# shortcut: PIL's Arial Bold at 13 px stands in for libass's (libass draws a little smaller), plus the 1.5 px
# outline; upgrade to measuring a burnt frame if a line ever lands within a few px of the limit
ARIAL = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 13)


def test_lines_fit_and_do_not_overlap():
    subs = fmv.lines()
    assert set(subs) <= {"WATA01", "WATA02", "WATA03", "WATA04"}
    for movie, rows in subs.items():
        last = 0.0
        for a, b, en in rows:
            assert last <= a < b, (movie, a, b, en)
            last = b
            parts = en.split("\n")
            assert en.strip() and len(parts) <= 2, (movie, en)
            assert all(ARIAL.getlength(p) + 3 <= 320 - 16 for p in parts), (movie, en)


def test_ass_keeps_line_breaks():
    a = fmv.ass([(1.0, 2.5, "one\ntwo")], 208)
    assert "PlayResY: 208" in a and "Dialogue: 0,0:00:01.00,0:00:02.50,Default,,0,0,0,,one\\Ntwo" in a
