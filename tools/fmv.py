"""fmv.py: burn English subtitles (script/fmv.tsv) into the STR movies PRG/WATA01-04.

usage: python -X utf8 tools/fmv.py [--force] [MOVIE ...]     (insert.edits() calls edits())
script/fmv.tsv: movie, start s, end s, Japanese, English (\\n = line break; wrapped to the frame otherwise).
Per movie: copy the dumped STR to work/fmv/en/, index it and export every frame with jPSXdec (tools/jpsxdec/,
github.com/m35/jpsxdec v2.0), draw the lines on the frames they span, then jPSXdec -replaceframes with
<partial-replace> on the text rect only, so the rest of each frame keeps its original bitstream.
Cached: work/fmv/en/<movie>.stamp holds a hash of the movie's lines and this file; same hash = no re-encode.
"""
import hashlib
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JAR = ROOT / "tools/jpsxdec/jpsxdec_v2.0/jpsxdec.jar"
TSV = ROOT / "script/fmv.tsv"
FONT = ROOT / "fonts/liberation/LiberationSans-Bold.ttf"
WORK = ROOT / "work/fmv"
SIZE, BOTTOM, MAXW = 14, 6, 300  # px: font, gap under the last line, wrap width


def lines():
    out = {}
    for row in TSV.read_text(encoding="utf-8").splitlines()[1:]:
        if row.strip():
            m, a, b, _jp, en = row.split("\t")
            out.setdefault(m, []).append((float(a), float(b), en.replace("\\n", "\n")))
    return out


def jpsx(*args):
    WORK.mkdir(parents=True, exist_ok=True)  # jPSXdec writes its *.log files into the cwd
    r = subprocess.run(["java", "-jar", str(JAR), *map(str, args)], capture_output=True, text=True, cwd=WORK)
    if r.returncode or "ERROR" in r.stdout:
        raise SystemExit(f"jPSXdec {args}: {r.stdout[-2000:]}{r.stderr[-2000:]}")
    return r.stdout


def wrap(draw, font, text):
    out = []
    for para in text.split("\n"):
        cur = ""
        for w in para.split():
            if cur and draw.textlength(cur + " " + w, font=font) > MAXW:
                out.append(cur)
                cur = w
            else:
                cur = (cur + " " + w).strip()
        out.append(cur)
    return out


def draw(img, text):
    """Centred lines at the bottom of the frame on a black box snapped to the 16x16 macroblock grid; returns the
    box (l, t, r, b). The flat box costs fewer bits than the picture it covers: outlined text straight on busy
    frames overran their sector budget and jPSXdec starved those blocks into a smear (tools/fmv_err.py)."""
    from PIL import ImageDraw, ImageFont
    font = ImageFont.truetype(str(FONT), SIZE)
    d = ImageDraw.Draw(img)
    rows = wrap(d, font, text)
    step = SIZE + 2
    y = img.height - BOTTOM - step * len(rows)
    ink = []
    for i, row in enumerate(rows):
        x = (img.width - round(d.textlength(row, font=font))) // 2
        ink.append(((x, y + i * step), row, d.textbbox((x, y + i * step), row, font=font)))
    l = min(b[0] for *_, b in ink) - 4
    r = max(b[2] for *_, b in ink) + 4
    t = min(b[1] for *_, b in ink) - 3
    box = (l // 16 * 16, t // 16 * 16, min(img.width, -(-r // 16) * 16), img.height)
    assert box[0] >= 0 and r <= img.width, f"subtitle too wide: {text!r}"
    d.rectangle((box[0], box[1], box[2] - 1, box[3] - 1), fill=(0, 0, 0))
    for at, row, _ in ink:
        d.text(at, row, font=font, fill=(255, 255, 255))
    return box


def burn(movie, subs, force=False):
    from PIL import Image
    src = ROOT / f"work/disc/tree/PRG/{movie}.STR"
    en = WORK / "en"
    en.mkdir(parents=True, exist_ok=True)
    out, stamp = en / f"{movie}.STR", en / f"{movie}.stamp"
    key = hashlib.sha1((repr(subs) + Path(__file__).read_text(encoding="utf-8")).encode()).hexdigest()
    if not force and out.is_file() and stamp.is_file() and stamp.read_text().strip() == key:
        return out
    shutil.copyfile(src, out)
    idx, frames, done = en / f"{movie}.idx", WORK / f"{movie}_fr", WORK / f"{movie}_sub"
    jpsx("-f", out, "-x", idx)
    head = next(l for l in idx.read_text().splitlines() if "Type:Video" in l)
    num, den = map(int, re.search(r"Sectors/Frame:(\d+)/(\d+)", head).groups())
    fps = 150 * den / num  # 2x CD: 150 sectors/s
    shutil.rmtree(frames, ignore_errors=True)
    shutil.rmtree(done, ignore_errors=True)
    done.mkdir()
    jpsx("-x", idx, "-i", 0, "-vf", "png", "-quality", "psx", "-dir", frames)
    pngs = sorted(frames.glob("*.png"))
    rects = {}
    for a, b, text in subs:
        for k in range(round(a * fps), min(round(b * fps), len(pngs))):
            img = Image.open(pngs[k]).convert("RGB")
            rects[k] = draw(img, text)
            img.save(done / f"{k:04d}.png")
    full, errs = set(), {}
    for _ in range(2):  # pass 2: frames whose subtitle came out starved get a full-frame re-encode instead
        if _:
            shutil.copyfile(src, out)
        xml = ['<?xml version="1.0"?>', '<str-replace version="0.3">']
        for k, (l, t, r, bt) in rects.items():
            p = (done / f"{k:04d}.png").as_posix()
            xml.append(f'<replace frame="{k}">{p}</replace>' if k in full else
                       f'<partial-replace frame="{k}" rect="{l},{t},{r - l},{bt - t}">{p}</partial-replace>')
        (en / f"{movie}.xml").write_text("\n".join(xml + ["</str-replace>"]) + "\n", encoding="utf-8")
        jpsx("-x", idx, "-i", 0, "-replaceframes", en / f"{movie}.xml")
        errs = error(movie, idx, rects)
        full = {k for k, e in errs.items() if e > LIMIT}
        if not full:
            break
    worst = sorted(errs.items(), key=lambda kv: -kv[1])[:5]
    (en / f"{movie}.log").write_text("".join(f"{k}\t{e:.1f}\n" for k, e in sorted(errs.items())), encoding="utf-8")
    print(movie, f"{len(rects)} frames subtitled; worst error {[(k, round(e, 1)) for k, e in worst]}")
    assert out.stat().st_size == src.stat().st_size
    stamp.write_text(key + "\n")
    return out


LIMIT = 12.0  # mean abs RGB error in the subtitle box; a starved (smeared) box measured 16-74, a clean one ~1


def error(movie, idx, rects):
    """{frame: mean abs error between jPSXdec's decode of the patched movie and the intended frame, in the box}."""
    import numpy as np
    from PIL import Image
    dec = WORK / f"{movie}_dec"
    shutil.rmtree(dec, ignore_errors=True)
    jpsx("-x", idx, "-i", 0, "-vf", "png", "-quality", "psx", "-dir", dec)
    pngs = sorted(dec.glob("*.png"))
    out = {}
    for k, (l, t, r, b) in rects.items():
        a = np.asarray(Image.open(pngs[k]).convert("RGB"), float)[t:b, l:r]
        want = np.asarray(Image.open(WORK / f"{movie}_sub/{k:04d}.png").convert("RGB"), float)[t:b, l:r]
        out[k] = float(np.abs(a - want).mean())
    return out


def edits(force=False, only=None):
    return {f"PRG/{m}.STR": burn(m, s, force).read_bytes() for m, s in lines().items() if not only or m in only}


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--force"]
    for p in edits("--force" in sys.argv, args):
        print(p, "ok")
