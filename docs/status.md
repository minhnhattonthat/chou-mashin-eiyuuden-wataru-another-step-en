# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 4. Extract in progress (script/ dumped and roundtrip-tested; menu-source structure + coverage next).
  Last build: build/wataru_en.bin, sha1 c2c044d1... (= original, no edits), smoke ok 2026-11-13.
- **Done:**
  - Phase 4, session 2 (2026-11-14): all 73 `?` readings settled (`jtext.py ctx [R04:1E1 ..]` prints uses in context).
    Pixel-font lookalikes fixed everywhere: 女 (read 廿/甘), 嬢 (爆), 簡 (闇), CG 0x131 聞 (was 闇), plus 遠 逞 輩 救 漢
    姿 接 誉. R13 0x16780-0x172EA (ワルジョ panel trap) is ep 12 -> M16_R12 (`rooms.font`). 0x0000 decodes as `　`.
    `tools/extract.py` writes script/rooms/Rxx.json (4,601 pages), script/{EXE,ST,BALLBAT,MACHINE,TTL,LVUP,FDS}.json
    and script/exe_<table>.json (7 fixed-width EXE name tables); keeps en/status/notes by id, refuses to drop English.
    `rooms.pages(data, base)` also parses the EXE dialogue (save lady, shops, inn, item/system messages).
    `test_script_roundtrip`: every script entry re-encodes to the original bytes.
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
  1. Menu sources (tools/extract.py STREAMS; ranges narrowed 2026-11-14 from msgscan clusters) need structure:
     - BALLBAT 0x21500-0x22A70: strings end 0x0000 (names `ワタル` etc.), not 0xFFFF; some entries are glued
       (`ブリザードタックル！ウォーターウォール！..`, `がいる！の攻撃！は`) and some are noise (`き`, `お`,
       `とんどんらのエなャパガめち` 0x2285C): split by the u32 tables at 0x2E8-0x7B4, mark noise `data`
       (tbl/menu_data.txt, read by extract.load_data_marks).
     - FDS 0x120D8: place names are fixed 10-cell fields (`もんじゃ村　　　　　龍神池`): split by stride; 0x125FA+
       entries are noise. 0x1840C-0x18596 is a kana grid (name entry?), EXE 0x7099C-0x70B34 and 0x77CC8 too:
       decide text vs data. MACHINE 0x1056C/0x10920 noise; 0x17616 is a kanji list (天翔登龍剣幻影招龍破.., a glyph
       set for drawn attack names? check before phase 5). ST 0x3ACC noise. TTL: check the CNF_MSG font cells.
     - EXE menu strings 0x77B8A+ end 0x0000 (`よろしいですか` / `はい` / `いいえ`); `segments()` cuts at pointer
       targets only, so check each against the lui/addiu refs. EXE 0x0224 in key item `[0224]メダル` = 金 in the
       R08/R09 font (menus borrow the loaded room font): note it for translators.
     Then a coverage test per source: every msgscan --menu run in the file is inside an entry or a listed data range.
  2. Translator view: speakers (`ワタル：` first line), message grouping of pages (0x2000 next page, 0x3000 end).
  3. When phase 5 starts editing: give `build.build()` a no-edits switch so test_identity stays green.
  4. Free-RAM: 0x80128800-0x80148000 is free outside battles only (files.md); phase 5 must pick a region that
     survives battles (or reload after them).
  5. Tour checks owed by the graphics survey (FK stills, FMV burnt-in text, credits pages, battle signs) have warps.
     Grow scenes.txt when a report names a place it can't reach (open list in docs/re/debug.md).
- **Open bugs:** none.
- **Waiting on the user:** nothing.
