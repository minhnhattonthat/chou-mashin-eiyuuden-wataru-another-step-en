# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 4. Extract next (phase 3 identity build done 2026-11-13). Last build: build/wataru_en.bin, sha1
  c2c044d1... (= original, no edits), smoke ok 2026-11-13.
- **Done:**
  - Phase 3: `tools/build.py` (check_rom -> dumpsxiso once into work/disc -> mkpsxiso) + `tests/test_identity.py`
    (no-edit build byte-identical, runs in the pre-commit check, ~2 s).
  - Step 0: PCSX-Redux + SCPH-5500 + mkpsxiso in tools/, smoke boots the original, input + Lua verified, pre-commit gates on tools/check.py, guard hook active, rom.sha1 pinned.
  - Disc unpack/rebuild with mkpsxiso is byte-identical (work/disc/, not yet a test: phase 3).
  - Phase 1 (docs/re/): encoding, text sources, pointer formats, free RAM candidate, graphics survey G1-G24.
  - Phase 2 (docs/re/debug.md): `tools/debug/warp.lua` + `scenes.txt` + `warp_all.py`. All 35 scenes reach their
    screen from a cold boot on a blank card (work/qa/warp/summary.tsv, final.png per scene, states in work/states/):
    title menu / Continue / Config, ep00-ep14 (every area map + episode card + opening dialogue), field, field menu +
    5 submenus, shop, save, ball / mashin / IQ battles, battle won, battle lost, level-up, ending (FMV + staff roll),
    credits. GOD covers the field party and the battle's own HP copy.
  - Phase-2 RE: SysMode table (0x8009C7FC), episode index 0x8009C90C (0-14; 12 and 13 share R13.BIN; 15 = ending),
    room font per episode index verified (text.md: the kanji table is per episode index, R13.BIN needs two),
    field sub-state 0x8009C788, party stats, file table 0x80077240 (`tools/filetab.py`).
- **Next (phase 4: extract, `references/pipeline.md` §Extract):**
  1. Kanji OCR for common 0xDA-0x1A2 (`tbl/kanji_common.txt`) and every room font (per-episode tables; R13.BIN
     needs two, split its text by episode 12/13).
  2. Extractor to `script/` JSON for every source in docs/re/text.md (room message banks, NPC-talk arrays, EXE,
     ST/BALLBAT/MACHINE/LVUP...), unknown codes as `[XXXX]`; roundtrip test + coverage test on the original; mark
     non-text as data.
  3. When phase 5 starts editing: give `build.build()` a no-edits switch so test_identity stays green.
  4. Free-RAM: 0x80128800-0x80148000 is free outside battles only (files.md); phase 5 must pick a region that
     survives battles (or reload after them).
  5. Tour checks owed by the graphics survey (FK stills, FMV burnt-in text, credits pages, battle signs) have warps.
     Grow scenes.txt when a report names a place it can't reach (open list in docs/re/debug.md).
- **Open bugs:** none.
- **Waiting on the user:** nothing.
