"""textcover_run.py: show every room text page in the emulator with tools/lua/textview.lua, for textcover.py.

    python -X utf8 tools/textcover_run.py [--only 1,2] [--chunk 30] [--jobs 3] [--out work/qa/cover]

Per episode (work/states/epNN.sstate, the warp to that episode), the pages of build/wataru_en.strings.tsv not yet
logged under --out are cut into chunks; each chunk is one emu.py run (textview.lua + textlog.lua, mashing Circle) in
<out>/epNN_<k>/, so one hung event costs one chunk, not the episode. Re-running resumes: pages already logged are
dropped. HOST = the episode's first 'event' page with a real 7-word header, for textview's pointer-redirect pass.
Then: python -X utf8 "$SKILL/scripts/textcover.py" work/qa/cover build/wataru_en.strings.tsv --waive docs/text_unshown.tsv
"""
import argparse
import struct
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from skill import SKILL  # noqa: E402

BASE = 0x800CE000


def logged(out):
    keys = set()
    for f in Path(out).rglob("log.txt"):
        for ln in f.read_text(encoding="utf-8", errors="replace").splitlines():
            if ln.startswith("TEXT "):
                keys.add(int(ln.split()[1], 16))
    return keys


def has_header(ovl, addr):
    """The 7 words before the page: w7 or w4 = 0x7FFF, w1 = 0xFFFF or a small id (textview.lua header())."""
    d = (ROOT / "work" / "disc" / "en" / "FPRG" / f"{ovl}.BIN").read_bytes()
    w = struct.unpack_from("<7H", d, addr - (BASE & 0xFFFFFF) - 14)
    return (w[6] == 0x7FFF or w[3] == 0x7FFF) and (w[0] == 0xFFFF or w[0] < 0x300)


def run(job, a):
    ep, k, rows, host = job
    out = Path(a.out) / f"ep{ep:02d}_{k:03d}"
    lst = Path(a.out) / f"ep{ep:02d}_{k:03d}.txt"
    lst.write_text("".join(f"{addr:06X} {kind}\n" for addr, kind in rows), encoding="utf-8")
    cmd = [sys.executable, "-X", "utf8", str(Path(SKILL) / "scripts" / "emu.py"), str(ROOT / "build" / "wataru_en.cue"),
           "--out", str(out), "--state-in", str(ROOT / "work" / "states" / f"ep{ep:02d}.sstate"),
           "--script", str(ROOT / "tools" / "lua" / "textview.lua"), "--script", str(ROOT / "tools" / "lua" / "textlog.lua"),
           "--var", f"LIST='{lst.as_posix()}'", "--var", f"SNAP='{(Path(a.out) / f'ep{ep:02d}_{k:03d}.sstate').as_posix()}'",
           "--var", f"HOST=0x{host:06X}", "--mash", "8", "--mash-key", "circle", "--frames", "200000",
           "--timeout", str(a.timeout)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return f"ep{ep:02d}_{k:03d} {len(rows)} pages: " + (r.stdout.strip().splitlines() or ["?"])[-1][:90]


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--only", default="")
    p.add_argument("--chunk", type=int, default=30)
    p.add_argument("--jobs", type=int, default=3)
    p.add_argument("--timeout", type=int, default=150)  # a chunk takes ~20 s; a hang (NPC text into an A000 item command) never ends
    p.add_argument("--out", default=str(ROOT / "work" / "qa" / "cover"))
    a = p.parse_args()
    Path(a.out).mkdir(parents=True, exist_ok=True)
    seen = logged(a.out)
    eps = {}
    for ln in (ROOT / "build" / "wataru_en.strings.tsv").read_text(encoding="utf-8").splitlines():
        pid, key, kind = ln.split("\t")[:3]
        key = int(key, 16)
        if kind == "menu":  # menu/battle sources: tools/lua/readlog.lua over the warp scenes
            continue
        eps.setdefault(key >> 24, []).append((pid[:3], key & 0xFFFFFF, kind, key in seen))
    only = {int(x) for x in a.only.split(",") if x}
    jobs = []
    for ep, pages in sorted(eps.items()):
        if only and ep not in only:
            continue
        host = next((addr for ovl, addr, kind, _ in pages if kind == "event" and has_header(ovl, addr)), None)
        todo = [(addr, kind) for _, addr, kind, s in pages if not s]
        print(f"ep{ep:02d}: {len(pages) - len(todo)}/{len(pages)} logged, host {host:06X}")
        first = len([d for d in Path(a.out).glob(f"ep{ep:02d}_*") if d.is_dir()])  # earlier runs keep their dirs
        for k in range(0, len(todo), a.chunk):
            jobs.append((ep, first + k // a.chunk, todo[k:k + a.chunk], host))
    with ThreadPoolExecutor(a.jobs) as ex:
        for line in ex.map(lambda j: run(j, a), jobs):
            print(line, flush=True)


if __name__ == "__main__":
    main()
