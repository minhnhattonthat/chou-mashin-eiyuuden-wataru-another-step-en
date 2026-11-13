"""tools/batches.py: split / check / merge rules (box limits, cursor indents, speakers, honorifics) on a temp script."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_batches_selftest():
    r = subprocess.run([sys.executable, "-X", "utf8", str(ROOT / "tools/batches.py"), "--selftest"],
                       capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0 and "selftest ok" in r.stdout, r.stdout[-2000:] + r.stderr[-2000:]


def test_shipped_english_clean():
    """Every merged `en` passes the batch rules (the text lint)."""
    r = subprocess.run([sys.executable, "-X", "utf8", str(ROOT / "tools/batches.py"), "check"],
                       capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, r.stdout[-3000:]
