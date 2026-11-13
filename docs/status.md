# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 3. Identity build next (phase 2 debug tool done 2026-11-13). Last build: none.
- **Done:**
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
- **Next (phase 3: identity build, `references/pipeline.md` §Identity):**
  1. `tools/build.py` that unpacks (dumpsxiso) and repacks (mkpsxiso) with no edits, checks rom.sha1 first; a test
     that the rebuilt .bin is byte-identical (work/disc already proved it by hand).
  2. Free-RAM trap sweep done (files.md): 0x80128800-0x80148000 is free outside battles only; every battle mode
     overwrites all of it. Phase 5 must pick a region that survives battles (or reload after them).
  3. Later phases: kanji OCR for common 0xDA-0x1A2 and every room font (phase 4); split R13.BIN text by episode
     12/13 for the table; tour checks owed by the graphics survey (FK stills, FMV burnt-in text, credits pages,
     battle signs) now have warps (ending, credits, battle_*).
  4. Grow scenes.txt when a report names a place it can't reach (open list in docs/re/debug.md).
- **Open bugs:** none.
- **Waiting on the user:** nothing.
