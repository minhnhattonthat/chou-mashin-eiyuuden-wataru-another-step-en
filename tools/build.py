"""build.py: original disc -> build/wataru_en.bin + .cue.

usage: python -X utf8 tools/build.py [--out DIR] [--name NAME]
Checks the dump against rom.sha1, unpacks it once with dumpsxiso into work/disc/ (tree/ + layout.xml, redone when
the stamp doesn't match the dump), then repacks with mkpsxiso. Phase 3: no edits yet, so the output is
byte-identical to the original (tests/test_identity.py). The EXE's file table gets LBAs at boot, so files may move.
"""
import argparse
import hashlib
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import check_rom  # noqa: E402

MKPSX = ROOT / "tools/mkpsxiso/mkpsxiso-2.30-win64"
CUE = ROOT / "rom/Chou Mashin Eiyuuden Wataru - Another Step (Japan).cue"
DISC = ROOT / "work/disc"


def rom_sha1():
    line = next(l for l in (ROOT / "rom.sha1").read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#"))
    return line.split()[0].lower()


def sha1(path):
    with open(path, "rb") as f:
        return hashlib.file_digest(f, "sha1").hexdigest()


def unpack():
    """Extract the disc into work/disc/ unless the stamp says this dump is already there."""
    stamp = DISC / "unpacked.sha1"
    want = rom_sha1()
    if stamp.is_file() and stamp.read_text().strip() == want and (DISC / "layout.xml").is_file():
        return
    if (DISC / "tree").exists():
        shutil.rmtree(DISC / "tree")
    DISC.mkdir(parents=True, exist_ok=True)
    subprocess.run([str(MKPSX / "dumpsxiso.exe"), "-q", "-x", "tree", "-s", "layout.xml", str(CUE)], cwd=DISC, check=True)
    stamp.write_text(want + "\n")


def repack(out_bin, out_cue, layout="layout.xml"):
    out_bin.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([str(MKPSX / "mkpsxiso.exe"), "-q", "-y", "-o", str(out_bin.resolve()), "-c", str(out_cue.resolve()),
                    layout], cwd=DISC, check=True)
    # mkpsxiso writes the bin's path as given; a cue next to its bin wants the bare file name.
    out_cue.write_text(f'FILE "{out_bin.name}" BINARY\n  TRACK 01 MODE2/2352\n    INDEX 01 00:00:00\n')


def edited_layout(edits):
    """Write work/disc/layout_en.xml: layout.xml with each edited file's entry pointed at work/disc/en/<path>."""
    en, out, stack, done = DISC / "en", [], [], set()
    for line in (DISC / "layout.xml").read_text(encoding="utf-8").splitlines():
        m = re.search(r'<(dir|file) name="([^"]+)"', line)
        if m and m[1] == "dir" and not line.rstrip().endswith("/>"):
            stack.append(m[2])
        elif "</dir>" in line:
            stack.pop()
        elif m and m[1] == "file" and "/".join(stack + [m[2]]) in edits:
            rel = "/".join(stack + [m[2]])
            dst = en / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(edits[rel])
            line = line.replace(f'name="{m[2]}"', f'name="{m[2]}" source="{dst.as_posix()}"', 1)
            done.add(rel)
        out.append(line)
    if done != set(edits):
        raise SystemExit(f"layout has no entry for {sorted(set(edits) - done)}")
    (DISC / "layout_en.xml").write_text("\n".join(out) + "\n", encoding="utf-8")
    return "layout_en.xml"


def build(out_dir=ROOT / "build", name="wataru_en", edits=None, qa=None):
    """edits: {disc path: new bytes}; None = insert.edits(qa) (the translation), {} = identity build."""
    check_rom.check()
    unpack()
    if edits is None:
        import insert
        edits = insert.edits(qa)
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        (Path(out_dir) / f"{name}.strings.tsv").write_text(insert.strings(), encoding="utf-8")  # textcover.py
    out_bin, out_cue = Path(out_dir) / f"{name}.bin", Path(out_dir) / f"{name}.cue"
    repack(out_bin, out_cue, edited_layout(edits) if edits else "layout.xml")
    return out_bin, out_cue


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default=str(ROOT / "build"))
    ap.add_argument("--name", default="wataru_en")
    ap.add_argument("--identity", action="store_true", help="no edits: rebuild the original disc")
    ap.add_argument("--qa", action="append", default=[], metavar="ID=TEXT",
                    help="override one entry's text (\\n = newline), e.g. a stress line for the width gate")
    a = ap.parse_args()
    qa = dict(q.replace("\\n", "\n").split("=", 1) for q in a.qa)
    b, c = build(a.out, a.name, {} if a.identity else None, qa)
    h = sha1(b)
    print(f"{b} {b.stat().st_size} bytes sha1 {h}" + (" (identical to the original)" if h == rom_sha1() else ""))
