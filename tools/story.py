"""Story pass (phase 9): one chapter file per episode room file (+ ST, the IQ-battle hosts), reviewed by `codex exec`.

    python -X utf8 tools/story.py chapters          -> work/qa/story/chapters/<ch>.txt (then qa_gate init, see below)
    python -X utf8 tools/story.py review [CH ..] [--jobs 4]
        -> work/qa/story/reports/<ch>.md (docs/story-reviewer-brief.md applied to the chapter),
           work/qa/story/verdicts/<ch>_<time>.tsv ("ch<TAB>ok|issue<TAB>note" from its Assessment).
        The controller fixes Critical/Important (hand batch), puts Minors in docs/polish.md, re-runs `chapters` +
        qa_gate init, re-reviews changed chapters.
    qa_gate.py init work/qa/story/manifest.tsv work/qa/story/chapters --glob "*.txt"
    qa_gate.py check work/qa/story/manifest.tsv work/qa/story/verdicts

Order = file order (pointer/offset order: scenes in sequence, NPC and next-page text interleaved).
"""
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import batches  # noqa: E402
import tl_codex  # noqa: E402

STORY = ROOT / "work/qa/story"
CHAPTERS = [f"R{n:02d}" for n in (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 14)] + ["ST"]


def chapter_entries(ch):
    for path, _, entries in batches.docs():
        if path.stem == ch:
            return [e for e in entries if e.get("en") and e.get("jp", "").strip("　\n")]
    raise SystemExit(f"no script file {ch}.json")


def chapters():
    out = STORY / "chapters"
    out.mkdir(parents=True, exist_ok=True)
    for ch in CHAPTERS:
        rows = chapter_entries(ch)
        (out / f"{ch}.txt").write_text("".join(
            f">> {e['id']} | {batches.speaker(e['jp'])} | {batches.show(e['jp'])}\n   {e['en'].replace(chr(10), chr(92) + 'n')}\n"
            for e in rows), encoding="utf-8", newline="\n")
        print(ch, len(rows))
    return 0


def assessment(text):
    """('ok'|'issue', note) from the report's Assessment section; None if absent."""
    tail = text.split("Assessment", 1)[-1] if "Assessment" in text else ""
    m = re.search(r"\b(ok|issue)\b\W*(.*)", tail)
    return (m.group(1), m.group(2).strip().replace("\t", " ")[:300]) if m else None


def review(ch):
    rep = STORY / "reports" / f"{ch}.md"
    rep.parent.mkdir(parents=True, exist_ok=True)
    chap = (STORY / "chapters" / f"{ch}.txt").read_text(encoding="utf-8")
    ask = (f"=== docs/story-reviewer-brief.md ===\n{tl_codex.read('docs/story-reviewer-brief.md')}\n"
           f"=== docs/synopsis.md ===\n{tl_codex.read('docs/synopsis.md')}\n"
           f"=== docs/style-reference.md ===\n{tl_codex.read('docs/style-reference.md')}\n"
           f"=== glossary.md ===\n{tl_codex.read('glossary.md')}\n"
           f"=== chapter {ch} (work/qa/story/chapters/{ch}.txt) ===\n{chap}\n"
           "Do not use any tools. Reply with only the report the brief asks for.")
    text = tl_codex.codex(ask, rep)
    got = assessment(text)
    if not got:
        return ch, "no Assessment in report"
    vd = STORY / "verdicts"
    vd.mkdir(parents=True, exist_ok=True)
    (vd / f"{ch}_{time.strftime('%Y%m%d_%H%M%S')}.tsv").write_text(f"{ch}\t{got[0]}\tcodex: {got[1]}\n", encoding="utf-8")
    return ch, got[0]


def main(argv):
    if not argv or argv[0] not in ("chapters", "review"):
        print(__doc__)
        return 2
    if argv[0] == "chapters":
        return chapters()
    jobs = int(argv[argv.index("--jobs") + 1]) if "--jobs" in argv else 4
    names = [a for i, a in enumerate(argv[1:], 1) if not a.startswith("--") and argv[i - 1] != "--jobs"] or CHAPTERS
    with ThreadPoolExecutor(jobs) as ex:
        res = list(ex.map(review, names))
    for ch, v in res:
        print(ch, v)
    return 0 if all(v in ("ok", "issue") for _, v in res) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
