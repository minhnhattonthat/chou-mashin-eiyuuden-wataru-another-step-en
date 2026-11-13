# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 4. Extract in progress (kanji read, room pages located; JSON writer + non-room sources next). Last
  build: build/wataru_en.bin, sha1 c2c044d1... (= original, no edits), smoke ok 2026-11-13.
- **Done:**
  - Phase 4 so far (2026-11-14): every kanji glyph read by eye: `tbl/kanji_rows.txt` (CG + 12 room fonts; M16_R14
    borrows by identical bitmap, 6 cells unread: 1D4 1D5 1F6 226 261 262); `tools/mktbl.py` reads its CG lines.
    `tools/jtext.py` = 16-bit codec + per-font tables (dup glyphs as `[0242:先]`), `jtext.py` lists doubtful
    readings. `tools/rooms.py` finds all 4,601 room pages (grammar in docs/re/text.md), `rooms.font()` incl. the
    R13 ep12/13 split. `tests/test_extract.py`: room pages roundtrip, no code past the font, coverage = waivers
    in `tbl/room_data.txt`. `tools/kanjiocr.py --sheet` renders reading sheets (its template guesses are useless).
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
  1. Settle the 73 `?` readings from context: decode pages, grep each doubtful code, fix `tbl/kanji_rows.txt`
     (suspects: the 爆?/嬢? cell in most rooms, 廿?, 闇?/間?, 案?, 誉?/営?, R00 253 悩? vs 1BB). Map 0x0000 to a
     blank (`　`) in the room codec (now `[0000]`). Read M16_R14's 6 unread cells (`jtext.py sheet`).
  2. `tools/extract.py`: write `script/rooms/Rxx.json` (id `Rxx:OFFSET`, font, header, terminator, ptr slots, jp,
     en ""; never clobber en) from rooms.pages(), then the other sources in docs/re/text.md: EXE (pointer arrays +
     fixed-width name tables), PRG/ST, BALLBAT, MACHINE, TTL (CNF_MSG font: check its kanji cells), LVUP, FDS
     (newline 0x9999, ends 0xFFFF). Each source: roundtrip + coverage test against msgscan --menu runs, data
     waivers listed. Mark non-text as data.
  3. When phase 5 starts editing: give `build.build()` a no-edits switch so test_identity stays green.
  4. Free-RAM: 0x80128800-0x80148000 is free outside battles only (files.md); phase 5 must pick a region that
     survives battles (or reload after them).
  5. Tour checks owed by the graphics survey (FK stills, FMV burnt-in text, credits pages, battle signs) have warps.
     Grow scenes.txt when a report names a place it can't reach (open list in docs/re/debug.md).
- **Open bugs:** none.
- **Waiting on the user:** nothing.
