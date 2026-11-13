"""build.py: original disc -> build/wataru_en.bin + .cue.

usage: python -X utf8 tools/build.py [--out DIR] [--name NAME]
Checks the dump against rom.sha1, unpacks it once with dumpsxiso into work/disc/ (tree/ + layout.xml, redone when
the stamp doesn't match the dump), then repacks with mkpsxiso. Phase 3: no edits yet, so the output is
byte-identical to the original (tests/test_identity.py). The EXE's file table gets LBAs at boot, so files may move.
"""
import argparse
import hashlib
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


def repack(out_bin, out_cue):
    out_bin.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([str(MKPSX / "mkpsxiso.exe"), "-q", "-y", "-o", str(out_bin.resolve()), "-c", str(out_cue.resolve()),
                    "layout.xml"], cwd=DISC, check=True)
    # mkpsxiso writes the bin's path as given; a cue next to its bin wants the bare file name.
    out_cue.write_text(f'FILE "{out_bin.name}" BINARY\n  TRACK 01 MODE2/2352\n    INDEX 01 00:00:00\n')


def build(out_dir=ROOT / "build", name="wataru_en"):
    check_rom.check()
    unpack()
    out_bin, out_cue = Path(out_dir) / f"{name}.bin", Path(out_dir) / f"{name}.cue"
    repack(out_bin, out_cue)
    return out_bin, out_cue


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default=str(ROOT / "build"))
    ap.add_argument("--name", default="wataru_en")
    a = ap.parse_args()
    b, c = build(a.out, a.name)
    h = sha1(b)
    print(f"{b} {b.stat().st_size} bytes sha1 {h}" + (" (identical to the original)" if h == rom_sha1() else ""))
