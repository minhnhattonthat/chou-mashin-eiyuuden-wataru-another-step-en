import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import digraph  # noqa: E402


def test_font_and_cells():
    digraph.selftest()
    assert digraph.pairs("Sakuya:") == ["Sa", "ku", "ya", ":"]
    assert digraph.cell("A")[:64] == digraph.cell("A ")[:64]
