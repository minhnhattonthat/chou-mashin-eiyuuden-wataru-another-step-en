# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 5. Marker build boots and tours; width gate partly measured (docs/re/windows.md).
  Last build: build/wataru_en.bin sha1 d126aaa1... (2026-11-14, marker build: every entry `NNNN` + filler), smoke ok,
  all 35 warps + talk01 reach (work/qa/p5/marker, summary.tsv). Stress build: `tools/stress.py` (build/stress.bin).
- **Done:**
  - Phase 5, session 2 (2026-11-14): `tools/insert.py` = the real insert path from script/: `en` or a marker (number
    in work/markers.tsv, filler letters tell the column), in place, pair codes per font context (room-only pairs ->
    that M16 font 0x1A4+, cap 190; the rest -> MSG_CG kanji slots 0xE6-0x1A3 minus ▼, mirrored into CNF_MSG; overflow
    promotes the most shared pair), bfont names one letter per 8x16 cell (the 8x16 font is MSG_CG 0-0x3B00), ENE
    names + their cell-count byte. Every write logged; `tests/test_insert.py` runs romdiff on every edited file.
    `tbl/not_text.txt` (3 ids). `build.py --qa ID=TEXT`. New text source: battle enemy names YM/BR_02/ENE01-18
    (extract.py `ene/`, text.md). Width gate: dialogue 32 letters x 3 lines, measured; torture line clean.
    Markers seen in: dialogue, CNF config, field config, shop list, equip/status names, place HUD, battle messages,
    LVUP, IQ battle. Japanese left in tour shots = known graphics rows (G4, G9, G11, G16, G19/MR_02 STS, G23).
  - Phase 5, session 1 (2026-11-14): glyph path traced (docs/re/font.md): src = 0x80115300 + code*128, one
    LoadImage per 16x16 glyph into a VRAM window buffer, 124 render sites across EXE/ST/BALLBAT/MACHINE/TTL/LVUP/FDS.
    **D8: two letters per 16x16 cell**, pre-rendered (`tools/digraph.py`, Spleen 8x16 in `fonts/`), codes allocated
    per font context like kanji; no renderer patch. Spike (`tools/insert.py`): R01:0E7CA in English, legible in game
    (work/qa/p5/spike3). `build.build(edits=...)`: `{}` = identity (test_identity), default = `insert.edits()`;
    edited files go to work/disc/en/ via layout_en.xml. Probes: `lua/readpcs.lua`, `callers.lua`, `stackwalk.lua`,
    `vdump.lua` + `tools/vram.py`.
  - Phase 4 done (session 3, 2026-11-14): menu sources structured (docs/re/text.md "Menu-source structure"). A string
    starts at every pointer target (blank cells after one are kept: cursor indents); `[u32 id, u32 ptr]` records
    dropped; BALLBAT battle-font item names (`kind: bfont`, `jtext.battle_table`, 8x16 font at RAM 0x80110000);
    new fixed tables exe_key_item_desc / exe_shop_lines / exe_monpet_lines / fds_places / fds_voices
    (`FIXED` = (source, lo, hi, stride)). Table ranges that decode as text: `tbl/menu_data.txt` (replaces the `data`
    flag). `test_menu_coverage`: no msgscan run in any menu source outside an entry or a data range (inside text
    ranges any run, outside them 6+ words). `tools/refs.py SRC LO HI` lists pointer targets with their refs.
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
- **Next (phase 5: finish the width gate, `references/pipeline.md` §Width gate):**
  1. Measure every "guess" row of docs/re/windows.md with `build.py --qa` / `tools/stress.py` overrides (fill each to
     its slot, read the last drawn column zoomed): battle messages, config, place HUD, key-item descriptions, ENE
     names in messages, bfont item names (see them in a battle item menu), EXE system messages (item get).
  2. Trace the battle header enemy name (thin font, still Japanese in battle_ball): which file/font; add it.
  3. Not yet in place-only insert: text longer than its JP slot. Phase 7: grow banks (bank pointers, NPC u32
     arrays: text.md), menu pointers, fixed tables; fallback single-letter cells when a font context overflows.
  4. MACHINE glyph lists 0x1761C/0x17630/0x17648, FDS name-entry grid 0x18468 (data, not in script/ yet).
  5. Tour the marker build further: ending/credits sheets, mashin-battle messages, item-get messages; any box
     showing Japanese that is not a graphics row = an extractor gap (sweep the disc for its form).
  3b. Fixed fields now hold 2 letters per cell (8-cell name = 16 letters): measure, relocate only what still overflows.
  4. Free-RAM: 0x80128800-0x80148000 is free outside battles only (files.md); pick a region that survives battles.
  5. Marker build (`[id]` per entry), tour with the warps, width gate: measure every box variant in-game.
  6. Phase 6 prep (translator batches): speakers are the first line (`ワタル：`); pages end 2000 (next page) /
     3000 (message end); key-item descriptions use borrowed room-font codes ([01AF] etc., reading depends on episode).
  7. Tour checks owed by the graphics survey (FK stills, FMV burnt-in text, credits pages, battle signs) have warps.
     Grow scenes.txt when a report names a place it can't reach (open list in docs/re/debug.md).
- **Open bugs:** none.
- **Waiting on the user:** nothing.
