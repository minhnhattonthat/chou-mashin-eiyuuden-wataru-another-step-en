"""fmv.py: burn English subtitles (script/fmv.tsv) into the STR movies PRG/WATA01-04.

usage: python -X utf8 tools/fmv.py [--force] [MOVIE ...]     (insert.edits() calls edits())
script/fmv.tsv: movie, start s, end s, Japanese, English (\\n = line break; no automatic wrap).
Per movie: copy the dumped STR to work/fmv/en/, index it and export every frame with jPSXdec (tools/jpsxdec/,
github.com/m35/jpsxdec v2.0), burn the lines with ffmpeg/libass in the black-matrix-00 style (ass()), then
jPSXdec -replaceframes with <partial-replace> on the text rect only, so the rest of each frame keeps its original
bitstream; frames whose text comes out starved are re-encoded whole (error()).
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
WORK = ROOT / "work/fmv"


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


def stamp_time(t):
    cs = round(t * 100)
    return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


def ass(subs, height):
    """The black-matrix-00 subtitle style (its movie.py): Arial 13 bold, white, 1.5 px black outline, no shadow, no
    box, bottom centre, margins 8/8/10; PlayRes = the frame so sizes are frame pixels. WrapStyle 2: \\n only."""
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 320
PlayResY: {height}
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,13,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,1.5,0,2,8,8,10,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    return head + "".join(f"Dialogue: 0,{stamp_time(a)},{stamp_time(b)},Default,,0,0,0,,{t.replace(chr(10), '\\N')}\n"
                          for a, b, t in subs)


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
    for k, p in enumerate(pngs):
        p.rename(frames / f"{k:04d}.png")  # image2 pattern input; jPSXdec names carry [] brackets
    height = Image.open(frames / "0000.png").height
    (WORK / f"{movie}.ass").write_text(ass(subs, height), encoding="utf-8")
    # libass renders the style (cwd = WORK: the subtitles filter needs no drive-letter escaping); rgb24 throughout
    # keeps every pixel off the text identical, so the diff box below is the text alone
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", f"{fps:.6f}", "-start_number", "0", "-i",
                    f"{frames.name}/%04d.png", "-vf", f"format=rgb24,subtitles={movie}.ass", "-pix_fmt", "rgb24",
                    "-start_number", "0", f"{done.name}/%04d.png"], cwd=WORK, check=True)
    import numpy as np
    rects = {}
    for a, b, _ in subs:
        for k in range(round(a * fps), min(round(b * fps), len(pngs))):
            diff = np.argwhere((np.asarray(Image.open(frames / f"{k:04d}.png").convert("RGB"), int) !=
                                np.asarray(Image.open(done / f"{k:04d}.png").convert("RGB"), int)).any(2))
            if len(diff):
                (t, l), (bt, r) = diff.min(0), diff.max(0) + 1
                rects[k] = (max(0, l - 2), max(0, t - 2), min(320, r + 2), min(height, bt + 2))
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
