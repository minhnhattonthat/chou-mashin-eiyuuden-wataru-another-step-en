"""check.py: the one-command check (tests + text lint). The pre-commit hook runs this; exit code gates the commit."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# The text lint (batches.py check) runs as tests/test_batches.py; romdiff + allowed spans in test_insert.py,
# relocation in test_reloc.py.
sys.exit(subprocess.call([sys.executable, "-X", "utf8", "-m", "pytest", "-q", "-p", "no:cacheprovider", str(ROOT / "tests")], cwd=ROOT))
