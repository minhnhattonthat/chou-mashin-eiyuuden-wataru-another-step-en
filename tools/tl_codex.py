"""Translate (or review) batches with `codex exec`, prompt-only: codex's Windows sandbox can't start processes here,
so it gets every file it needs inside the prompt and answers in its last message (-o).

    python -X utf8 tools/tl_codex.py tl b001 b002 .. [--jobs 6] [--tries 3]
        -> work/tl/bNNN.out.tsv (checked with batches.check_batch; failing ids are sent back with the problems)
           work/tl/bNNN.report.txt (NEW TERM / UNSURE lines)
    python -X utf8 tools/tl_codex.py review PAIRS.txt .. [--jobs 4]
        -> PAIRS.review.md (docs/reviewer-brief.md applied to one pairs file)
"""
import re
import shutil  # codex is codex.cmd on Windows: which() finds it, a bare name doesn't
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import batches  # noqa: E402

TL = ROOT / "work/tl"


def read(p):
    return (ROOT / p).read_text(encoding="utf-8")


def context():
    gl = read("glossary.md").split("## Characters")[0]
    return (f"=== docs/translator-brief.md ===\n{read('docs/translator-brief.md')}\n"
            f"=== glossary.md (rulings; the batch's term rows follow below) ===\n{gl}\n"
            f"=== docs/style-reference.md ===\n{read('docs/style-reference.md')}\n"
            f"=== docs/synopsis.md ===\n{read('docs/synopsis.md')}\n")


def codex(prompt, out):
    """One prompt-only codex run; returns its last message."""
    r = subprocess.run([shutil.which("codex") or "codex", "exec", "-s", "read-only", "--skip-git-repo-check", "--ephemeral", "-o", str(out), "-"],
                       input=prompt, capture_output=True, text=True, encoding="utf-8", cwd=ROOT, timeout=3600)
    if not out.exists():
        raise RuntimeError(f"codex failed ({r.returncode}): {r.stderr[-500:]}")
    return out.read_text(encoding="utf-8")


def parse(text, ids):
    rows = {}
    for line in text.splitlines():
        k, _, v = line.partition("\t")
        if k.strip() in ids and v:
            rows[k.strip()] = v.rstrip("\r")
    return rows


def translate(batch, tries):
    tsv = (TL / f"{batch}.tsv").read_text(encoding="utf-8")
    ids = [ln.split("\t")[0] for ln in tsv.splitlines() if ln.strip()]
    terms = (ROOT / f"build/terms_{batch}.txt").read_text(encoding="utf-8")
    ask = (context() + f"=== build/terms_{batch}.txt (binding: JP<TAB>EN<TAB>Avoid; speaker rows) ===\n{terms}\n"
           f"=== work/tl/{batch}.tsv ===\n{tsv}\n"
           "Do not use any tools. Translate every row. Reply with ONLY the output TSV (id<TAB>English, line breaks "
           "as the two characters \\n), every id once in order; after it, optional lines starting with "
           "'NEW TERM: ' or 'UNSURE: '.")
    rows, report = {}, []
    for attempt in range(tries):
        text = codex(ask, TL / f"{batch}.last.txt")
        rows.update(parse(text, set(ids)))
        report += [ln for ln in text.splitlines() if ln.startswith(("NEW TERM:", "UNSURE:"))]
        (TL / f"{batch}.out.tsv").write_text("".join(f"{i}\t{rows[i]}\n" for i in ids if i in rows), encoding="utf-8")
        bad, _ = batches.check_batch(batch, batches.index(), batches.glossary())
        missing = [i for i in ids if i not in rows]
        if not bad and not missing:
            break
        probs = {}
        for line in bad:
            m = re.match(r"([A-Z0-9]+:[0-9A-F]+): (.*)", line)
            if m:
                probs.setdefault(m[1], []).append(m[2])
        fix = [i for i in ids if i in probs or i not in rows]
        src = {ln.split("\t")[0]: ln for ln in tsv.splitlines() if ln.strip()}
        ask = (context() + f"=== build/terms_{batch}.txt ===\n{terms}\n"
               "These rows of your translation failed the check. Rows (input TSV), your English, the problems:\n" +
               "".join(f"{src[i]}\nEN: {rows.get(i, '(missing)')}\nPROBLEMS: {'; '.join(probs.get(i, ['missing']))}\n\n"
                       for i in fix) +
               "Do not use any tools. Reply with ONLY corrected TSV rows (id<TAB>English) for exactly these ids. Keep "
               "the meaning; re-break or rephrase to fit; never drop content.")
    (TL / f"{batch}.report.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    bad, _ = batches.check_batch(batch, batches.index(), batches.glossary())
    return batch, len(bad)


def review(pairs):
    p = Path(pairs)
    ask = (f"=== docs/reviewer-brief.md ===\n{read('docs/reviewer-brief.md')}\n"
           f"=== glossary.md ===\n{read('glossary.md')}\n=== docs/style-reference.md ===\n{read('docs/style-reference.md')}\n"
           f"=== docs/synopsis.md ===\n{read('docs/synopsis.md')}\n=== {p.name} ===\n{p.read_text(encoding='utf-8')}\n"
           "Do not use any tools. Reply with only the report the brief asks for.")
    codex(ask, p.with_suffix(".review.md"))
    return p.name, 0


def main(argv):
    if len(argv) < 2 or argv[0] not in ("tl", "review"):
        sys.exit(__doc__)
    opt = lambda k, d: int(argv[argv.index(k) + 1]) if k in argv else d  # noqa: E731
    names = [a for i, a in enumerate(argv[1:], 1) if not a.startswith("--") and not argv[i - 1].startswith("--")]
    jobs, tries = opt("--jobs", 6), opt("--tries", 3)
    work = (lambda b: translate(b, tries)) if argv[0] == "tl" else review

    def fn(name):
        try:
            return work(name)
        except Exception as exc:  # one failed run must not stop the others
            return name, f"error {exc}"
    with ThreadPoolExecutor(jobs) as ex:
        for name, nbad in ex.map(fn, names):
            print(f"{name}: {'OK' if not nbad else f'{nbad} problems left'}", flush=True)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main(sys.argv[1:])
