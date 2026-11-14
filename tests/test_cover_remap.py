import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import cover_remap  # noqa: E402


def test_remap_follows_ids(tmp_path):
    old = tmp_path / "old.tsv"
    new = tmp_path / "new.tsv"
    old.write_text("R00:1\tDA000\tevent\nR00:2\tDA010\tnext\nEXE:3\t26094C10\tmenu\t01020304\n", encoding="utf-8")
    new.write_text("R00:1\tDA004\tevent\nR00:2\tDA020\tnext\nEXE:3\t26094C10\tmenu\t01020304\n", encoding="utf-8")
    run = tmp_path / "logs" / "a"
    run.mkdir(parents=True)
    (run / "log.txt").write_text("WARP x\nTEXT DA010 f5\nTEXT 26094C10\nTEXT DEAD\n", encoding="utf-8")
    assert cover_remap.seen_ids(old, [tmp_path / "logs"]) == {"R00:2", "EXE:3"}
    sys.argv = ["cover_remap.py", str(old), str(tmp_path / "logs"), "--new", str(new), "--out", str(tmp_path / "now")]
    cover_remap.main()
    assert (tmp_path / "now" / "log.txt").read_text(encoding="utf-8") == "TEXT 26094C10\nTEXT DA020\n"
