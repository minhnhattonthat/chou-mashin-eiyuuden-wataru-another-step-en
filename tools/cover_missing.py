"""cover_missing.py: the NEVER SHOWN ids of a textcover report, with their script file and English.

    python -X utf8 tools/cover_missing.py work/qa/cover_now_report.txt [--src EXE]
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def index():
    out = {}
    for f in sorted((ROOT / "script").rglob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        for e in d.get("entries", []):
            out.setdefault(e["id"], (f.stem, e))
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("report")
    p.add_argument("--src", help="only ids of this source (EXE, ST, ...)")
    a = p.parse_args()
    idx = index()
    for ln in Path(a.report).read_text(encoding="utf-8").splitlines():
        if not ln.startswith("NEVER SHOWN"):
            continue
        pid = ln.split()[2]
        if a.src and not pid.startswith(a.src + ":"):
            continue
        stem, e = idx.get(pid, ("?", {}))
        en = (e.get("en") or "").replace("\n", " / ")
        print(f"{pid}\t{stem}\t{e.get('kind', '')}\t{en[:70]}")


if __name__ == "__main__":
    main()
