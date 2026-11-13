"""Identity build: unpack + repack with no edits must give the original disc byte for byte."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import build  # noqa: E402

pytestmark = pytest.mark.skipif(not build.CUE.exists() or not (build.MKPSX / "mkpsxiso.exe").exists(),
                                reason="no ROM or mkpsxiso")


def test_unpacked_repack_is_identical(tmp_path):
    b, c = build.build(tmp_path, "ident", edits={})
    assert build.sha1(b) == build.rom_sha1()
    assert c.read_text().startswith('FILE "ident.bin" BINARY')
