"""sjisscan.py: count Shift-JIS runs (>= N chars, at least one kana) per file under a tree. Recon helper.

usage: python -X utf8 tools/sjisscan.py DIR|FILE [min_chars=4] [--show K]   (--show prints the first K runs per file)
"""
import re
import sys
from pathlib import Path

# 2-byte SJIS: lead 81-9F/E0-EF, trail 40-7E/80-FC
RUN = re.compile(rb"(?:[\x81-\x9f\xe0-\xef][\x40-\x7e\x80-\xfc])+")
KANA = re.compile("[ぁ-ヿ]")


def runs(data, n):
    for m in RUN.finditer(data):
        b = m.group()
        if len(b) // 2 < n:
            continue
        try:
            s = b.decode("cp932")
        except UnicodeDecodeError:
            continue
        if len(KANA.findall(s)) >= 2:
            yield m.start(), s


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    show = int(sys.argv[sys.argv.index("--show") + 1]) if "--show" in sys.argv else 0
    if show:
        args.remove(str(show))
    root = Path(args[0])
    n = int(args[1]) if len(args) > 1 else 4
    files = [root] if root.is_file() else sorted(p for p in root.rglob("*") if p.is_file())
    for p in files:
        if p.suffix.upper() in (".STR", ".VB", ".XA"):
            continue
        hits = list(runs(p.read_bytes(), n))
        if hits:
            print(f"{len(hits):6d} {sum(len(s) for _, s in hits):7d}  {p}")
            for off, s in hits[:show]:
                print(f"         {off:08X} {s[:60]}")


if __name__ == "__main__":
    main()
