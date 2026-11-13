"""Translate (or review) batches with `codex exec`, prompt-only: codex's Windows sandbox can't start processes here,
so it gets every file it needs inside the prompt and answers in its last message (-o).

    python -X utf8 tools/tl_codex.py tl b001 b002 .. [--jobs 6] [--tries 3]
        -> work/tl/bNNN.out.tsv (checked with batches.check_batch; failing ids are sent back with the problems)
           work/tl/bNNN.report.txt (NEW TERM / UNSURE lines)
    python -X utf8 tools/tl_codex.py review PAIRS.txt .. [--jobs 4]
        -> PAIRS.review.md (docs/reviewer-brief.md applied to one pairs file)
    python -X utf8 tools/tl_codex.py fix bNNN ..      merged English -> .out.tsv, failing rows back through codex
    python -X utf8 tools/tl_codex.py revise bNNN ..   Critical/Important of work/tl/bNNN.pairs.review.md back
        through codex (then the check loop); Minor lines appended to docs/polish.md. Merge with --overwrite after.
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
    out = TL / f"{batch}.out.tsv"
    rows = parse(out.read_text(encoding="utf-8"), set(ids)) if out.exists() else {}
    report = []
    for attempt in range(tries):
        if attempt or len(rows) < len(ids):  # a complete .out.tsv (fix mode) goes straight to the check
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
    if report or not (TL / f"{batch}.report.txt").exists():
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


ID = re.compile(r"\b(?:R\d\d|EXE|ST|TTL|LVUP|FDS|BALLBAT|MACHINE|ENE\d\d):[0-9A-F]{5}\b")


def findings(text):
    """(Critical+Important lines, Minor lines) of a review report."""
    major, minor, sec = [], [], None
    for line in text.splitlines():
        h = line.lstrip("#").strip().lower()
        if line.startswith("#"):
            sec = "major" if h.startswith(("critical", "important")) else "minor" if h.startswith("minor") else None
        elif sec and ID.search(line):
            (major if sec == "major" else minor).append(line.strip())
    return major, minor


def revise(batch, tries):
    """Critical/Important review findings back through codex, then the usual check loop. Minors -> docs/polish.md."""
    rev = TL / f"{batch}.pairs.review.md"
    major, minor = findings(rev.read_text(encoding="utf-8"))
    if minor:
        with (ROOT / "docs/polish.md").open("a", encoding="utf-8", newline="\n") as f:
            f.write("".join(f"- [ ] {batch} {m.lstrip('-* ')}\n" for m in minor))
    refresh(batch)
    if major:
        tsv = {ln.split("\t")[0]: ln for ln in (TL / f"{batch}.tsv").read_text(encoding="utf-8").splitlines() if ln}
        out = TL / f"{batch}.out.tsv"
        rows = parse(out.read_text(encoding="utf-8"), set(tsv))
        hit = [i for i in tsv if any(i in m for m in major)]
        terms = (ROOT / f"build/terms_{batch}.txt").read_text(encoding="utf-8")
        ask = (context() + f"=== build/terms_{batch}.txt ===\n{terms}\n"
               "A reviewer flagged these rows. Rows (input TSV) with the current English:\n" +
               "".join(f"{tsv[i]}\nEN: {rows[i]}\n\n" for i in hit) + "Findings:\n" + "\n".join(major) +
               "\n\nDo not use any tools. Reply with ONLY corrected TSV rows (id<TAB>English) for these ids, fixing "
               "each finding (the suggestion is a guide; keep every limit).")
        rows.update(parse(codex(ask, TL / f"{batch}.last.txt"), set(hit)))
        out.write_text("".join(f"{i}\t{rows[i]}\n" for i in tsv if i in rows), encoding="utf-8")
    return translate(batch, tries)


def refresh(batch):
    """fix mode: .out.tsv from the English merged in script/, so the check runs on what ships."""
    ix = batches.index()
    ids = [r[0] for r in batches.read_tsv(TL / f"{batch}.tsv")]
    if not all(ix[i].get("en") for i in ids):  # never blank an unmerged batch's .out.tsv (lost 10 batches once)
        raise RuntimeError(f"{batch} is not fully merged: merge it before fix/revise")
    (TL / f"{batch}.out.tsv").write_text("".join(f"{i}\t" + ix[i]["en"].replace("\n", "\\n") + "\n"
                                                 for i in ids), encoding="utf-8")


def main(argv):
    if len(argv) < 2 or argv[0] not in ("tl", "review", "fix", "revise"):
        sys.exit(__doc__)
    if argv[0] == "fix":  # failing merged rows back through codex, then merged over the old English
        for b in [a for a in argv[1:] if a.startswith("b")]:
            refresh(b)
        argv = ["tl"] + argv[1:]
    opt = lambda k, d: int(argv[argv.index(k) + 1]) if k in argv else d  # noqa: E731
    names = [a for i, a in enumerate(argv[1:], 1) if not a.startswith("--") and not argv[i - 1].startswith("--")]
    jobs, tries = opt("--jobs", 6), opt("--tries", 3)
    work = {"tl": lambda b: translate(b, tries), "revise": lambda b: revise(b, tries), "review": review}[argv[0]]

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
