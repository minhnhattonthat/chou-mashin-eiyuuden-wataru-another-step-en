"""script/fmv.tsv: well-formed, ordered, no overlaps, every line fits the 320x208 frame in at most 2 rows."""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import fmv  # noqa: E402


def test_lines_fit_and_do_not_overlap():
    font = ImageFont.truetype(str(fmv.FONT), fmv.SIZE)
    d = ImageDraw.Draw(Image.new("RGB", (320, 208)))
    subs = fmv.lines()
    assert set(subs) <= {"WATA01", "WATA02", "WATA03", "WATA04"}
    for movie, rows in subs.items():
        last = 0.0
        for a, b, en in rows:
            assert last <= a < b, (movie, a, b, en)
            last = b
            assert en.strip() and len(fmv.wrap(d, font, en)) <= 2, (movie, en)
            fmv.draw(Image.new("RGB", (320, 208)), en)  # asserts the inked box stays inside the frame
