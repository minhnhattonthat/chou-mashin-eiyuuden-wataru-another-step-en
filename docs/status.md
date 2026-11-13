# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 7. Insert, fit, check: not started. Phase 6 done (2026-11-14): 5,820 entries translated, check clean,
  every batch's latest review has no Critical/Important (work/tl/review_verdicts.tsv, all 42 ok), glossary current.
  First job: the build still withholds English (insert.py: "792 common pairs, MSG_CG has 189 free codes: English
  withheld, marker build"; room fonts likely over too) -> font/pair-code capacity, then work/overflow.tsv (English
  longer than its JP slot) and the phase-7 items listed under Next. Last build: build/wataru_en.bin sha1 6bebf36b...
  (2026-11-14, marker build), smoke ok.
- **Done:**
  - Phase 6, session 2 (2026-11-14): revise round 1 on the last 10 batches; review rounds 2-6 (codex) on every
    revised batch, Critical/Important fixed by codex revise or by hand (work/tl/handN.tsv/.out.tsv = hand-fix
    batches merged with `batches.py merge handN --overwrite`). Kanji misreads fixed in tbl/kanji_rows.txt (re-extract
    keeps en): M16_R02 0x212 襲 (was 救: villagers "attacked", not "rescued"), M16_R02 0x1B9 儲, M16_R07 0x244 灸.
    Room-font codes in EXE key items resolved (0x224 金 / 0x226 銀 / 0x228 介 in M16_R08/R09, 0x221 隊 in M16_R02).
    `batches.py`: honorific-on-common-noun lint ("bride-san", "Father-sama"), set phrases exempt (ゴクローさん,
    トリさん..), 殿 -> -dono, glossary terms matched across line wraps (この世/界 no longer demands "Layer"), BALLBAT
    particle fragments は/を may be " ", pairs take JP from script/. Glossary: Super Funny Cool Squad, Ear-Mouth-King
    Tree, Gold Medal, おじさま = "(my dear) sir" (never Uncle), kin/deity nouns take no honorific. Minors from every
    latest review are in docs/polish.md (110 open; some already fixed by later rounds: tick as fixed in the polish pass).
    Review archives: work/tl/bNNN.rN.review.md.
  - Phase 6, session 1 (2026-11-14): glossary rulings D9 (names: Hepburn, English-pun spellings), D10 (register,
    SFX), D11 (codex translates, prompt-only); `## Speakers` table (exact speaker labels); docs/style-reference.md
    (pilot R00:0CCF4-0D5A8 by the controller + voices), docs/synopsis.md (episodes 0-14), docs/translator-brief.md,
    docs/reviewer-brief.md, docs/polish.md. Tools: `tools/batches.py` (split/check/merge/terms/pairs; limits per
    entry in `box()` from windows.md; speaker, cursor-indent, honorific-after-katakana, [B000] rules; merge fills
    the B000 arg word), `tools/tl_codex.py` (tl / fix / review / revise via `codex exec` prompt-only),
    `tools/names.py` (one English per item/skill/enemy/place across tables, fits the tightest field; writes the
    generated glossary section). `insert.py`: English longer than its JP slot falls back to the marker and is
    listed in work/overflow.tsv (phase 7 grows slots), so builds and tests stay green. 42 batches (work/tl/), wave 0
    = name tables (b001-b006), wave 1 = dialogue.
  - Phase 5, session 5 (2026-11-14), width gate closed: mashin HP found (mashin u16 0x800BE31E/0x800BEBA4, enemy
    0x800BE38A/0x800BEF04, debug.md); retry box measured 7 cells = 14 letters x 2 lines (scene mashin_lose); mashin
    win shows no 経験値 banner (scene mashin_win: explosion -> fade -> mode B story dialogue; the strings are banner
    entries 0x20/0x21, budget 13 cells if ever drawn); もんペット attack names measured on the original: 10 cells
    drawn **squeezed to half width** (8 px per cell), so English = 10 letters, one letter per cell (a 2x-wide
    single-letter glyph: phase-7 item); roster RAM 0x800A8D60 (scene monpet_detail). warp.lua: `late=F:A:V:N`
    one-shot write F frames into a scene. Ending/credits toured on the marker build (work/qa/p5/tour_end): FMV and
    staff roll are graphics (STAFF.BIN, D3 = English: phase 8).
  - Phase 5, session 4 (2026-11-14): battle アイテム list measured (11 letters; inventory RAM + builder found, scene
    battle_item pokes it). Mashin battle: the 斬る/突く, 必殺技 and retry menus are texture strips cut from the MACHINE
    glyph lists by sprite records (box 8 cells = 16 letters; widening = phase-7 engine item, all addresses in
    windows.md). Attack-name banner (MACHINE.json names) measured 13 cells = 26 letters via `tools/lua/mbanner.lua`
    (forces banner actor 0x800BDEE8). exe_mashin_attacks are もんペット moves (read by FDS only), not mashin. New
    probes: `tools/lua/acts.lua` (log actor-action handlers of EXE table 0x8006E840 with the actor), `mbanner.lua`.
    New scenes battle_item, mashin_hit. Mashin MP: party 0x800A8D3C is copied; the battle copy is among
    0x800BE7A6 / 0x800BEBEC / 0x800E0574 (MP 98 shows, yet 登龍剣 (cost 20) still won't fire in ep1: probably not
    learned). Mashin HP not found (0x800BDA86 / 0x800BEF1A candidates poked to 1: no loss).
  - Phase 5, session 3 (2026-11-14): width gate for menus and battle (windows.md, every row now has a shot path):
    battle message box 16 cells (record-sized, centred), IQ box 16 cells x 3 lines, config labels 6 / values 13
    cells, field config rows 7, place box 10, key-item description 2x16, ENE names in messages = slot, header 11
    letters. Found: BALLBAT draws the `[u32 cells, u32 ptr]` record's count, not to the terminator
    (`extract.CELL_RECORDS` -> `len_at`, insert rewrites it; ENE `len_at` is now the exact count byte). Battle header
    name = ENE record ptr8 (`kind: bname`, 8x16 battle font bytes, char[12]); it was drawn for the 16-bit name's cell
    count (half an English name): `insert.CODE` patches BALLBAT 0x800DF340/390/398 to stop at the NUL (verified).
    battle_table 0xEB = `[00EB:・]`. `qa['+ID']` = stress-only spill past the slot. New scenes: menu_key (key items
    poked at 0x800A91F8), battle_menu, mashin_attack, iq_page2.
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
- **Next (phase 7: insert, fit, check, `references/pipeline.md` §Checks):**
  1. Get English into the build: pair-code capacity per font context (792 common pairs vs 189 free MSG_CG codes;
     room fonts too): more glyph slots, fallback single-letter cells, or fewer shared pairs. Then the overflow list
     (work/overflow.tsv) and the items below. Done when the build is green: width/overflow lint clean, control codes
     matched, romdiff shows no writes outside allowed ranges.
  2. Text edits after phase 6: change English through a batch (`batches.py merge NAME --overwrite`, a handN batch for
     hand fixes) so the check runs; after a table name change `tools/names.py --apply` then `batches.py terms`.
  Known draft gaps: BALLBAT messages with inner blank cells (ステータス　　を受けない: an icon or name is drawn
  there?) were translated without the blanks: check in game (phase 7/8). LVUP line 4: the level number prints into
  the JP blank cells (cols 7-8): English "Wataru reached level    !" puts the gap elsewhere: phase 7 must find
  where the digits go. TTL config labels may be 14 letters: phase 7 moves the value column x 112 -> 128.
  Phase-7 items already known (do not block phase 6): text longer than its JP slot (grow banks: bank pointers, NPC
  u32 arrays, text.md; menu pointers; fixed tables); fallback single-letter cells when a font context overflows;
  mashin strip relayout (windows.md); banner/bfont names past their JP cells (relocate via their u32 / record
  tables); monpet attack names as one 2x-wide letter per cell; MACHINE glyph lists 0x1761C/0x17630/0x17648 and FDS
  name-entry grid 0x18468 (data, not in script/ yet); free RAM that survives battles (0x80128800-0x80148000 is free
  outside battles only, files.md). Phase 8: graphics rows (G1-G24, incl. STAFF.BIN credits, FMV, FK stills).
- **Open bugs:** none.
- **Waiting on the user:** nothing.
