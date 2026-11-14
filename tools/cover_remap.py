"""cover_remap.py: carry text-coverage logs across a rebuild that moved strings (text edits re-lay room pages).

    python -X utf8 tools/cover_remap.py OLD_STRINGS.tsv LOGDIR [LOGDIR ..] --out work/qa/cover_now
        [--new build/wataru_en.strings.tsv]

Every "TEXT <key>" in LOGDIR/**/log.txt is matched against OLD_STRINGS.tsv (the strings.tsv of the build those runs
used) to the string id it showed; <out>/log.txt then lists the same ids under their keys in --new. Then:
    python -X utf8 "$SKILL/scripts/textcover.py" work/qa/cover_now build/wataru_en.strings.tsv --waive docs/text_unshown.tsv
A page id is the same page after a text edit, so the event that reached it still does.
"""
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def keys(path):
    """strings.tsv -> {key: [ids]} (int keys)."""
    out = {}
    for ln in Path(path).read_text(encoding="utf-8").splitlines():
        f = ln.split("\t")
        if len(f) >= 2:
            out.setdefault(int(f[1], 16), []).append(f[0])
    return out


def seen_ids(old, dirs):
    k = keys(old)
    ids = set()
    for d in dirs:
        for f in Path(d).rglob("log.txt"):
            for ln in f.read_text(encoding="utf-8", errors="replace").splitlines():
                if ln.startswith("TEXT "):
                    ids.update(k.get(int(ln.split()[1], 16), []))
    return ids


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("old")
    p.add_argument("dirs", nargs="+")
    p.add_argument("--new", default=str(ROOT / "build" / "wataru_en.strings.tsv"))
    p.add_argument("--out", default=str(ROOT / "work" / "qa" / "cover_now"))
    a = p.parse_args()
    ids = seen_ids(a.old, a.dirs)
    new = {i: key for key, its in keys(a.new).items() for i in its}
    lost = sorted(i for i in ids if i not in new)
    assert not lost, f"ids gone from the new build: {lost[:5]}"
    Path(a.out).mkdir(parents=True, exist_ok=True)
    (Path(a.out) / "log.txt").write_text("".join(f"TEXT {new[i]:X}\n" for i in sorted(ids)), encoding="utf-8")
    print(f"{len(ids)} ids shown, {len(new)} strings in the new build -> {a.out}/log.txt")


if __name__ == "__main__":
    main()
