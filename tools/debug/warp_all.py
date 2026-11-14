"""warp_all.py: run every scene in tools/debug/scenes.txt from a cold boot, keep a shot + savestate of each.

usage: python -X utf8 tools/debug/warp_all.py [--rom CUE] [--only a,b] [--jobs 3] [--out work/qa/warp]
         [--states work/states] [--no-sheet] [--script probe.lua --var NAME=LUA ...]

Each scene runs tools/debug/warp.lua in its own emu.py process (blank memory card), must log "DONE <scene>", and,
when the scene has room=Rnn, the overlay at 0x800CE000 must match FPRG/Rnn.BIN (work/disc/tree). Writes
<out>/<scene>/final.png (+ sheet), <states>/<scene>.sstate and <out>/summary.tsv. Exit 1 if any scene failed.
Regenerate the states after every rebuild that changes code, fonts, graphics or file LBAs.
"""
import argparse
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from skill import SKILL  # noqa: E402

ORIG = ROOT / "rom" / "Chou Mashin Eiyuuden Wataru - Another Step (Japan).cue"


def scenes(path):
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].split()
        if line:
            out.append((line[0], dict(kv.split("=", 1) for kv in line[1:])))
    return out


def room_match(head_hex, tree):
    """Name of the FPRG/R*.BIN whose first 256 bytes best match the logged overlay head."""
    head = bytes.fromhex(head_hex)
    best = max(((sum(a == b for a, b in zip(head, f.read_bytes()[:256])), f.stem) for f in tree.glob("R*.BIN")))
    return best[1] if best[0] >= 240 else "?"


def run(name, opts, a):
    out = Path(a.out) / name
    states = Path(a.states)
    states.mkdir(parents=True, exist_ok=True)
    frames = int(opts.get("frames", 12000))
    cmd = [sys.executable, "-X", "utf8", str(Path(SKILL) / "scripts" / "emu.py"), str(a.rom), "--out", str(out),
           "--sav", str(ROOT / "tools" / "debug" / "blank.mcd"), "--script", str(ROOT / "tools" / "debug" / "warp.lua"),
           "--var", "SCENE='%s'" % name, "--frames", str(frames), "--shot-every", opts.get("every", "300"),
           "--state-out", str(states / (name + ".sstate")), "--timeout", str(max(300, frames // (8 if a.debugger else 20)))]  # the debugger runs ~15 fps
    if not a.no_sheet:
        cmd.append("--sheet")
    for s in a.script:
        cmd += ["--script", s]
    if a.debugger:  # exec/read/write breakpoints in a probe (L.on_exec ...)
        cmd.append("--debugger")
    for v in a.var:
        cmd += ["--var", v]
    with open(out.with_suffix(".out"), "w", encoding="utf-8") as fh:
        rc = subprocess.call(cmd, stdout=fh, stderr=subprocess.STDOUT)
    log = (out / "log.txt").read_text(encoding="utf-8", errors="replace") if (out / "log.txt").exists() else ""
    ok = rc == 0 and ("DONE " + name) in log
    room = "-"
    for line in log.splitlines():
        if line.startswith("ROOMHEAD "):
            room = room_match(line.split()[1], ROOT / "work" / "disc" / "tree" / "FPRG")
    if "room" in opts and room != opts["room"]:
        ok = False
    at = next((ln.split()[2] for ln in log.splitlines() if ln.startswith("AT ")), "-")
    return name, ok, rc, at, room


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--rom", default=str(ROOT / "build" / "wataru_en.cue") if (ROOT / "build" / "wataru_en.cue").exists()
                   else str(ORIG))
    p.add_argument("--only")
    p.add_argument("--jobs", type=int, default=3)
    p.add_argument("--out", default=str(ROOT / "work" / "qa" / "warp"))
    p.add_argument("--states", default=str(ROOT / "work" / "states"))
    p.add_argument("--no-sheet", action="store_true")
    p.add_argument("--debugger", action="store_true", help="emu.py --debugger (probes with L.on_exec)")
    p.add_argument("--script", action="append", default=[], help="extra probe for every run (e.g. tools/lua/trapwatch.lua)")
    p.add_argument("--var", action="append", default=[], help="extra emu.py --var for every run")
    a = p.parse_args()
    todo = scenes(ROOT / "tools" / "debug" / "scenes.txt")
    if a.only:
        want = set(a.only.split(","))
        todo = [s for s in todo if s[0] in want]
    Path(a.out).mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(a.jobs) as ex:
        res = list(ex.map(lambda s: run(s[0], s[1], a), todo))
    lines = ["scene\tok\trc\tat\troom"] + ["%s\t%s\t%s\t%s\t%s" % r for r in res]
    (Path(a.out) / "summary.tsv").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    bad = [r[0] for r in res if not r[1]]
    print("FAILED: " + ", ".join(bad) if bad else "all %d scenes reached" % len(res))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
