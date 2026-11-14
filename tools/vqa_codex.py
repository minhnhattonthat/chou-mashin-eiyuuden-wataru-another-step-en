"""Visual-QA verdicts with `codex exec` (read-only, prompt-only: codex's sandbox can't run Python here).

    python -X utf8 tools/vqa_codex.py work/qa/chunks/chunk_001.txt .. [--jobs 3] [--jp work/qa/tour_jp_full]

Feed it full-scale sheets (tools/tour_sheets.py): at emu.py's half scale codex flags clean 6x12 labels as garbled.

Each chunk file (qa_gate.py todo --out-dir) lists "id<TAB>path" lines. Every sheet goes to codex as an image, with the
original's sheet of the same scene (same path under --jp) and docs/visual-qa-brief.md; codex returns
"id<TAB>ok|issue<TAB>note" lines, written to work/qa/verdicts/<chunk>.tsv. A chunk whose answer lacks an id fails and writes nothing.
"""
import argparse
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRIEF = ROOT / "docs" / "visual-qa-brief.md"


def run(chunk, a):
    rows = [ln.split("\t") for ln in Path(chunk).read_text(encoding="utf-8").splitlines() if ln.strip()]
    ids, paths = [r[0] for r in rows], [Path(r[-1]) for r in rows]  # qa_gate todo: "id<TAB>path"
    imgs, lines = [], []
    for i, (p, sid) in enumerate(zip(paths, ids)):
        imgs.append(str(p))
        jp = Path(a.jp) / (sid + ".png")
        if jp.exists():
            imgs.append(str(jp))
            lines.append(f"{sid}: image {len(imgs) - 1} (translated), image {len(imgs)} (original Japanese, same scene)")
        else:
            lines.append(f"{sid}: image {len(imgs)} (translated; no original sheet)")
    ask = (BRIEF.read_text(encoding="utf-8") +
           "\n\n## This dispatch\nYou cannot run commands: judge from the attached images (numbered in attach order). "
           "Each sheet is a contact sheet of one warp scene, frames in time order. The game is Japanese; the "
           "translated build should show English wherever the original shows Japanese text, except the "
           "standing non-bugs above. Sheets:\n" + "\n".join(lines) +
           "\n\nAnswer with exactly one line per sheet id, `id<TAB>ok|issue<TAB>note`, nothing else.")
    out = Path(a.verdicts) / (Path(chunk).stem + ".last.txt")
    cmd = [shutil.which("codex") or "codex", "exec", "-s", "read-only", "--skip-git-repo-check", "--ephemeral",
           "-o", str(out)]
    for im in imgs:
        cmd += ["-i", im]
    r = subprocess.run(cmd + ["-"], input=ask, capture_output=True, text=True, encoding="utf-8", cwd=ROOT)
    if r.returncode or not out.exists():
        return chunk, f"codex failed ({r.returncode}): {r.stderr[-300:]}"
    got = {}
    for ln in out.read_text(encoding="utf-8").splitlines():
        f = ln.strip().strip("`").split("\t")
        if len(f) >= 2 and f[0] in ids and f[1] in ("ok", "issue"):
            got[f[0]] = (f[1], f[2] if len(f) > 2 else "")
    miss = [i for i in ids if i not in got]
    if miss:
        return chunk, "missing ids: " + ", ".join(miss)
    (Path(a.verdicts) / (Path(chunk).stem + ".tsv")).write_text(
        "".join(f"{i}\t{got[i][0]}\tcodex: {got[i][1]}\n" for i in ids), encoding="utf-8")
    return chunk, "%d ok, %d issue" % (sum(v[0] == "ok" for v in got.values()), sum(v[0] == "issue" for v in got.values()))


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("chunks", nargs="+")
    p.add_argument("--jobs", type=int, default=3)
    p.add_argument("--jp", default=str(ROOT / "work" / "qa" / "tour_jp_full"))  # tools/tour_sheets.py
    p.add_argument("--verdicts", default=str(ROOT / "work" / "qa" / "verdicts"))
    a = p.parse_args()
    Path(a.verdicts).mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(a.jobs) as ex:
        res = list(ex.map(lambda c: run(c, a), a.chunks))
    for c, msg in res:
        print(f"{Path(c).stem}\t{msg}")
    sys.exit(1 if any(m.startswith(("codex failed", "missing")) for _, m in res) else 0)


if __name__ == "__main__":
    main()
