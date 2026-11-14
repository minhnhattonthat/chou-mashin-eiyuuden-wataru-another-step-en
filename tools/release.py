"""release.py: the release gate (references/pipeline.md, Release), stops at the first failure: build, tests, smoke,
jp_left (every disc file; runs not in docs/jp_known.tsv fail), qa_gate on every work/qa/**/manifest.tsv (visual tour
and story pass), textcover, polish.md all ticked, README placeholders, xdelta patch, re-apply and compare, zip.

A rebuild that changes the disc stops at qa_gate (STALE): re-run the scenes that show the change (docs/status.md
recipe) and re-merge the coverage logs (cover_remap), then run this again.
Debug off: the warp tool only pokes RAM from Lua (tools/debug/warp.lua) and this script builds with no --qa, so
nothing of it is on the disc. Publishing is the owner's call: this ends at release/<zip>. The image stays in build/.

usage: python -X utf8 tools/release.py [--version 1.0] [--force]   (--force overwrites that version's files)
"""
import argparse
import hashlib
import re
import subprocess
import sys
import zipfile
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build  # noqa: E402
import check_rom  # noqa: E402
from skill import SKILL  # noqa: E402

OUT = ROOT / "release"
TOOLS = Path(SKILL) / "scripts"
PY = [sys.executable, "-X", "utf8"]
BUILT = ROOT / "build/wataru_en.bin"
KNOWN = ROOT / "docs/jp_known.tsv"
TEMPLATE = ROOT / "docs/release-readme.txt"
WINDOW = str(1 << 30)  # past the whole 486 MB image: a smaller window misses every match behind moved files


def step(name, *cmd):
    print("==", name, flush=True)
    if subprocess.run([str(c) for c in cmd], cwd=ROOT).returncode:
        sys.exit(f"release stopped: {name} failed")


def hashes(path):
    """(size, CRC32, MD5, SHA-1) of a file, as text."""
    crc, md5, sha = 0, hashlib.md5(), hashlib.sha1()
    with open(path, "rb") as f:
        while chunk := f.read(1 << 22):
            crc = zlib.crc32(chunk, crc)
            md5.update(chunk)
            sha.update(chunk)
    return str(Path(path).stat().st_size), f"{crc:08X}", md5.hexdigest().upper(), sha.hexdigest().upper()


def jp_runs():
    """{(disc path, offset)} of Japanese-looking runs in the built disc files. Files the build rewrote (work/disc/en)
    count only runs unchanged from the original (min 4 codes); untouched files hold no script text, so they are
    scanned for longer stray runs (min 6)."""
    tree, en = build.DISC / "tree", build.DISC / "en"
    found = set()
    for f in sorted(p for p in tree.rglob("*") if p.is_file()):
        rel = f.relative_to(tree).as_posix()
        new = en / rel
        # subtitled movies (tools/fmv.py) hold no script text: scanned as untouched, else video noise reads as text
        args = [new, "--orig", f, "--min", "4"] if new.exists() and f.suffix != ".STR" else [f, "--min", "6"]
        r = subprocess.run([*PY, TOOLS / "jp_left.py", *args, "--tbl", ROOT / "tbl/jp_common.tbl", "--le16",
                            "--limit", "100000"], capture_output=True, text=True, encoding="utf-8", cwd=ROOT)
        found |= {(rel, int(m.group(1), 16)) for m in re.finditer(r"^0x([0-9A-F]+)\s", r.stdout, re.M)}
    return found


def known():
    rows = [ln.split("\t") for ln in KNOWN.read_text(encoding="utf-8").splitlines() if ln and not ln.startswith("#")]
    return {(r[0], int(r[1], 16)) for r in rows}


def unticked(text):
    return [line for line in text.splitlines() if line.startswith("- [ ]")]


def placeholders(text):
    return re.findall(r"<[A-Za-z][^>\n]*>", text)


def gates():
    step("build", *PY, ROOT / "tools/build.py")
    step("tests", *PY, ROOT / "tools/check.py")
    step("smoke", *PY, TOOLS / "emu.py", BUILT.with_suffix(".cue"), "--out", "work/qa/smoke", "--route",
         "tools/routes/boot.txt", "--smoke")
    print("== jp_left", flush=True)
    left = sorted(jp_runs() - known())
    if left:
        sys.exit("release stopped: Japanese runs not in docs/jp_known.tsv:\n" + "\n".join(f"{f}\t{o:06X}" for f, o in left))
    for manifest in sorted((ROOT / "work/qa").rglob("manifest.tsv")):
        step(f"qa_gate {manifest.relative_to(ROOT)}", *PY, TOOLS / "qa_gate.py", "check", manifest, manifest.parent / "verdicts")
    step("textcover", *PY, TOOLS / "textcover.py", "work/qa/cover_now", "build/wataru_en.strings.tsv", "--waive",
         "docs/text_unshown.tsv")
    if left := unticked((ROOT / "docs/polish.md").read_text(encoding="utf-8")):
        sys.exit(f"release stopped: {len(left)} unticked lines in docs/polish.md")
    if found := placeholders((ROOT / "README.md").read_text(encoding="utf-8")):
        sys.exit(f"release stopped: README.md placeholders {found}")


def patch(name):
    """Encode, then apply to the clean dump and compare with the build."""
    source, out = build.CUE.with_suffix(".bin"), OUT / name
    step("xdelta", "xdelta3", "-e", "-f", "-9", "-S", "djw", "-B", WINDOW, "-s", source, BUILT, out)
    back = OUT / "reapply.bin"
    step("re-apply", "xdelta3", "-d", "-f", "-B", WINDOW, "-s", source, out, back)
    same = hashes(back) == hashes(BUILT)
    back.unlink()
    if not same:
        sys.exit("release stopped: the patched disc differs from the build")
    print("re-applied, identical:", name, flush=True)


def readme(version, name):
    fields = {"version": version, "patch": name}
    for tag, path in (("base", build.CUE.with_suffix(".bin")), ("patched", BUILT)):
        fields |= dict(zip((f"{tag}_size", f"{tag}_crc", f"{tag}_md5", f"{tag}_sha1"), hashes(path)))
    fields["base_sha1_lower"] = fields["base_sha1"].lower()
    return TEMPLATE.read_text(encoding="utf-8").format(**fields)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--version", default="1.0")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    name = f"Wataru-Another-Step_EN_v{a.version}.xdelta"
    final = OUT / f"Wataru-Another-Step_EN_v{a.version}.zip"
    if not a.force and (final.exists() or (OUT / name).exists()):
        sys.exit(f"{final.name} or its patch exists: --force to overwrite")
    check_rom.check()
    gates()
    OUT.mkdir(exist_ok=True)
    patch(name)
    (OUT / "README.txt").write_text(readme(a.version, name), encoding="utf-8", newline="\r\n")
    with zipfile.ZipFile(final, "w", zipfile.ZIP_STORED) as z:
        for f in (name, "README.txt"):
            z.write(OUT / f, f)
    print(final, *hashes(final))


if __name__ == "__main__":
    assert unticked("- [ ] a\n- [x] b\n") == ["- [ ] a"]
    assert placeholders("x <Game title> [![a](b)](c)") == ["<Game title>"]
    main()
