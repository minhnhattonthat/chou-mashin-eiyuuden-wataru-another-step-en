"""cover_ids.py: the string ids a coverage log shows, by source (TEXT keys -> ids via build/wataru_en.strings.tsv).

    python -X utf8 tools/cover_ids.py work/qa/ncover/items_all [--strings build/wataru_en.strings.tsv]
"""
import argparse
import collections
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("logdir")
    p.add_argument("--strings", default=str(ROOT / "build" / "wataru_en.strings.tsv"))
    a = p.parse_args()
    keys = set()
    for f in Path(a.logdir).rglob("log.txt"):
        for ln in f.read_text(encoding="utf-8", errors="replace").splitlines():
            if ln.startswith("TEXT "):
                keys.add(int(ln.split()[1], 16))
    by = collections.defaultdict(list)
    for ln in Path(a.strings).read_text(encoding="utf-8").splitlines():
        pid, key = ln.split("\t")[:2]
        if int(key, 16) in keys:
            by[pid.split(":")[0]].append(pid.split(":")[1])
    for src, ids in sorted(by.items()):
        print(f"{src} {len(ids)}: {' '.join(ids)}")


if __name__ == "__main__":
    main()
