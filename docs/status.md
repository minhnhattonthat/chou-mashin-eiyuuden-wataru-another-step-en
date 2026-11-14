# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 8. QA in the emulator: in progress (graphics rows done: G3, G4, G5, G6, G9, G11, G12, G16, G19, G20,
  G23, G25 credits; G10 waived (never drawn); drawn, checked offline, not yet seen in game: G17, G18).
  Phase 7 done (2026-11-14): full English build, overflow empty, all warp scenes reach.
- **Done:**
  - Phase 8, session 10 (2026-11-14): **visual-QA tour started**. warp_all on EN + original (work/qa/tour_jp, states
    work/qa/tour_jp_states; 70/71 reach, `endreal` times out on both after its AT at f8301: the emulator stalls in
    the ending FMV, harmless, the roll is covered by staff_roll). New `tools/tour_sheets.py` (full-scale sheets,
    8 frames a page: emu.py's half-scale sheets made codex flag every pixel-font label as garbled, 60 false issues)
    -> work/qa/tour (717 sheets) + work/qa/tour_jp_full; new `tools/vqa_codex.py` (codex exec read-only, EN + JP
    sheet per id, writes work/qa/verdicts/<chunk>.tsv). docs/visual-qa-brief.md got the game's standing non-bugs.
    Round 1 on build 25e4d369: 702 ok, 15 issue; real ones fixed: **ST blank-cell padding** drew past the IQ box's
    16-cell VRAM buffer (704,0) and wiped the hit-and-blow card backs at (768,0) (insert: ST strings now end with
    their terminator after the text; found with new `tools/lua/loadimg.lua`); **staff roll**: the next page's first
    row showed under each 224-px page (staff.py keeps row 0 blank); **Config heading** centred (hand19: "  Config").
    False positives (check after the re-tour, write `ok` overrides in work/qa/verdicts/zz_controller.tsv if the
    sheet is unchanged): credits/sheet_3-6 (forced mode 0x16 shows the map off-grid, not the real roll),
    mashin_fire/sheet_140 + mashin_fire2/sheet_141 (same grid in the JP), mashin_hit/sheet_16 (box mid-fade),
    menu/menu_config/menu_use/monpet_detail sheet_3 "..." page (EN types faster: timing drift). inkbox: save-file
    box File 1-4 centred (26/27 px; JP 5/13); the other menus are left-aligned lists like the JP; title menu has no
    box. **Text coverage started**: `insert.strings()` -> build/wataru_en.strings.tsv (4,599 room pages, key =
    episode << 24 | EN RAM address of the page's first word), `tools/lua/textlog.lua` (logs the event pointer in
    that form), `tools/lua/textview.lua` (dialogue viewer: plays a page list as events; debug.md "Dialogue
    viewer"). First run (ep 1, 234 pages): 67 shown, 66 STUCK (the event never returns to state 0 within 3000
    frames; probably a choice, a scene change or a missing end): not yet usable. Build sha1 e210ee37..., 110 tests,
    smoke ok. A full re-tour on this build was running at hand-off (work/qa/retour.log: warp_all -> tour_sheets ->
    qa_gate init).
  - Phase 8, session 9 (2026-11-14): **G12 done**: Hit / Blow / Tries seen in new scene **hitblow** (ep 7 IQ = card
    hit & blow), WIN! in new scene **iq_win** (KIO lose-card table pointer 0x8010AE9C poked to the win list; WIN /
    ! now meet at the record seam, `put_stone ha=`). G17/G18: battle id = u8 **0x8009C856** (formation, EXE
    0x80033DEC; per-episode random tables at 0x80081D88), id 0x1C = Pitch Girl troop (ENE09) -> new scene
    **pitch_battle**; neither bubble drawn in 15000 mashed frames; offline check clean (work/qa/g18/bub.png).
    docs/visual-qa-brief.md copied for the tour. G20: Phantom Wyrmwave banner cells seen in new scene
    **mashin_fire2** (second special). Build sha1 25e4d369..., 110 tests, smoke ok. warp_all not rerun
    (only IQ pixels changed; hitblow / iq_win states made).
  - Phase 8, session 8 (2026-11-14): **G10 waived**: R15_MES narration is never drawn (the real ending path, traced
    from ep 14 with new scene **endreal** = 0x8009C7B0 0xFFFF + mode D: 0x800580B0 sets ep 15 + loads R15, the next
    C/D loop pass plays movie 3 then the staff roll; the R15 overlay entry never runs; graphics.md G10). **G23 monpet
    element** 水/雷/火 (MSG_CG 0xB0-0xB2, one 16x16 cell drawn by FDS code) -> icons drop / bolt / flame
    (`digraph.ICONS`, insert writes them, D23; drop verified in monpet_detail, roster +0 is not the element so bolt/
    flame only offline). **G12**: LOSE! card seen clean in the ep-2 KIO game; IQ game type per episode listed in
    graphics.md G12. Build sha1 311cab54..., 110 tests. warp_all not rerun (MSG_CG glyphs in place, no LBA shift).
  - Phase 8, session 7 (2026-11-14): **G9 memory card** in English (`gfx.MEM_EN` per MEMORY.BIN sprite list, strips
    via `mem_layout`/`mem_recs`/`mem_check`, はい/いいえ/第 話 -> Yes/No/Ep. in place; `gfx_gen memcard`; test_memcard;
    `tools/memview.py` composes every message offline -> work/g9/preview.png). Verified in new scene **save_slot**
    (save into file 1: Which file / Select / Saving / Save complete / filled slot) and title_continue with its card
    (work/states/card_file1.mcd: Checking / Load slot). New scene save_ep3 (warped ep-3 save shifts the slot row on
    the original too: not ours). **G20 banners** (D22): one carved word per MBEXT_08 kanji cell (`gfx_gen.BANNER`),
    verified TO / RYU / KEN in new scene **mashin_fire** (ep13, Wataru MP max poked 99: his 18 < cost 20). **G10** RE
    (graphics.md: R15.BIN = 8-page scroll state machine; not reached yet, see Next). G7: ending FMV has no burnt-in
    text. Scene `narration` = the ep15 card flow held 15000 frames (card -> FMV -> roll; R15 not in it). Build sha1
    b3fc2a7e..., 110 tests. warp_all not rerun this session (no LBA shift: records/pixels in place).
  - Phase 8, session 6 (2026-11-14): **G25 staff roll** (D3, D21) in English: FVHH/STAFF.BIN is a 120x98 tile map of
    16x16 cells (6x7 pages of 320x224) over a glyph image; `tools/staff.py` lays out `gfx/staff_en.txt` (42 pages,
    two-column credits, Spleen 8x16 two letters per cell, colours = the JP's white/orange/yellow palettes) into the same
    cell list / map / image (gfx.apply, test_gfx test_staff_roll). Verified the whole roll in new scene **staff_roll**
    (ending FMV -> pages row-major -> title; work/qa/p8/roll/sheet*.png). G9 memory-card RE notes in graphics.md (CLUT
    r2310 pal 13, every strip = one MEMORY.BIN record, redraw plan). warp_all 49/49 before G25 (G25 doesn't move
    LBAs). Build sha1 36aacd17..., 109 tests.
  - Phase 8, session 5 (2026-11-14): **G5** area cards (SBTCHAR glyph sheet; card label lists in SBTTL.BIN
    0x3B70-0x4E00, `gfx.SBT_EN`/`sbt_recs`, Spleen 8x16 word strips via `gfx_gen.put_mono`, boxes widened from bar B)
    and **G6** episode captions (16 captions x 2 CLUT lists in SBTTL.BIN 0x5528-0x7274, `gfx.CAP_EN`/`cap_recs`, one
    Liberation Sans Bold 24 strip per line via `gfx_gen.put_line`), verified in ep00-05/13/14 and new scene **ep15**
    (ending card + ending caption). graphics.md G5/G6 rows rewritten (the 0x3B70 lists are G5's, not G6's).
    Build sha1 fe33b696..., 108 tests. warp_all not rerun after these builds (records/pixels changed in place, no
    LBA shift): rerun before the next state-based check.
  - Phase 8, session 4 (2026-11-14): **G23** field menu / status / equip / item / monpet-detail labels in English
    (graphics.md G23, D20: Sp. Attack / Sp. Defense / Ep. are the only short forms). `gfx.FM_LABELS` + `fm_layout`
    + `fm_recs` + `fm_check`, `gfx_gen.py fmenu`, gfx.tsv row FM16/STS_atlas.png, tests/test_gfx.py
    test_fmenu_labels. New scenes menu_use (item list + tab heading), menu_status2 (right = next character, not a
    second page). Build sha1 10dcf222..., 106 tests.
  - Phase 8, session 3 (2026-11-14): **G19** done, verified in scene mashin_attack (VS card + menu): labels Fight /
    Heal / Spirit / Special (one png in all 18 STS files: 攻撃/回復 cells stay 32 px, u56+ is the gauge-pip strip
    MACHINE 0x173E2 and MP, so "Attack" can't fit; Fight matches the ball-battle command), VS-card names per file
    (`gfx_gen.STS_NAMES`, `fit_stone` condenses to the rect; STS_03 player = Super Funny Cool Squad in its 192x24
    record set). tpage 0x0E (names) is overwritten by MBEXT_05-07 at (832,0) and by the menu strips: names only on
    the VS card. **G23 RE**: FD_STS atlas is a glyph sheet and every field-menu/status label is static per-glyph
    sprite records in FDS.BIN 0x12530.. (graphics.md G23 has the layout and the redraw plan). New `tools/prims.py`
    (GPU sprite packets in a RAM dump, by CLUT row); `gfx.py show` takes `rHEX`. Build sha1 f2db47da..., 105 tests.
  - Phase 8, session 2 (2026-11-14): G11 shop (FD_SHP.PX: ｶﾞﾝﾎﾞ/個/合計 -> Ganbo / pcs / Total, FDS.BIN records
    0x171C6/0x171D4 re-cut; verified in scene shop), G12 IQ (HIT_MAIN labels Hit / Blow / Tries [digit]; HIT + KIO
    LOSE! / WIN + !, `put_stone`), G17 OTHER11 bubbles Sorry♥ / Bam!, G18 ENE09 No / Signal (`recolor` wipes the
    text indices, keeps the bubble). gfx_gen: put_bdf `edge=None`, `trim=False` (one baseline), `shadow`, `bold`.
    New `tools/clutfind.py`: CLUT finder from a VRAM dump + screenshot (shop CLUT (208,481) set by code; its 16
    colours are raw in FP00/P00M0.BIN 0x1BE20 -> gfx.tsv `r1BE20`). Sprite records: the struct starts 4 bytes
    before u,v (`[tpage, clut, u, v, w, h, x, y]`). Build sha1 d46c4330..., smoke ok, warps shop/battle_ball/
    battle_iq/iq_page2/battle_win reach, 105 tests.
  - Phase 8, session 1 (2026-11-14): graphics pipeline. `tools/gfx.py` (rows in `gfx/gfx.tsv`: png, target file,
    upload-block offset, bpp, CLUT file + offset (`rHEX` = raw colours in a file header), palette, rect; `export`
    writes gfx/orig/ + gfx/en/ seeds; the build imports gfx/en/ by palette index through insert.put(), unknown
    colours fail; `gfx.RECS` = sprite-record patches (fmt, original asserted, new)). `tools/gfx_gen.py GROUP` draws
    gfx/en/ from gfx/orig/ (label classes: `put_text` TrueType coverage -> palette ramp, `put_bdf` pixel font +
    1-px outline). Fonts: Liberation Sans 2.1.5 (OFL), Spleen 6x12 (docs/fonts.md). tests/test_gfx.py; romdiff spans
    and test_reloc know gfx writes. Done, verified zoomed in a cold-boot warp: **G4** title menu (TTL.BIN records
    0x4FA2/0x4FB0 re-cut: the kana shared ニュー), **G3** copyright line 1, **G16** battle commands + party names in
    all six YM/BR_17/OTHER0n.CHG (CLUT found by VRAM dump: `--script tools/lua/vdump.lua --var FR=<frame before the
    warp's DONE>`; BALLBAT name records widened to 48). Sprite records here: `[u16 tpage, u16 clut, u8 u, u8 v,
    u16 w, u16 h, s16 x, s16 y]`; find them by scanning the overlay for the atlas u/v/w/h (TTL.BIN, BALLBAT).
  - Phase-7 review fixes (2026-11-14, H:\translation\.harness\reviews\...-phase7.md): insert fails the build on any
    fixed-slot overflow (qa builds excepted) and `batches.py` lints every fixed slot (was ST only); romdiff writes
    must sit in allowed spans built from the script layout + named sites (test_insert `allowed_spans`); new
    tests/test_reloc.py (every original u32 / lui+lo reference follows its entry, none left inside a moved one,
    non-entry targets keep their bytes, EXE strings checked from every other code file, roompack.selftest) with
    explicit waivers (actor-record fields, two BALLBAT table bases never read in battle: rdA/rdB watch). It found
    **the EXE zero run is libspu's _spu_zerobuf**: SpuClearReverbWorkArea (0x80062E98) now clears in 64-byte chunks
    from strpack.SPU_ZERO (0x80098BEC, kept zero; never called in 9 sampled scenes, hits.lua). Overlay tails capped
    and trap-tested on the original in every battle scene (BALLBAT -> 0x80104800 ENE base, MACHINE -> 0x800F0000;
    files.md). Save title (MEMORY.BIN SJIS) in English: script/MEMORY.json `kind: sjis`. Stub-last-line lint
    (6 hits rewrapped, hand18). D17 (ST/fixed-block fit), D18 (compose hook), D19 (cut names waived); polish.md
    cut-name lines ticked. Stale states idle_ep01/ep15 deleted. Build sha1 84d3e92e..., 102 tests.
  - Phase 7 (2026-11-14): runtime pair composer (LoadImage hook, tools/compose.py) instead of pre-rendered pairs;
    room text re-laid per bank/NPC unit (tools/roompack.py); EXE/PRG strings relocated (tools/strpack.py: EXE zero
    run ends 0x80098C2C, the last 20 bytes are live: strings there froze the title; TTL re-laid as a pool). **ST is
    not relocatable**: its strings are C local arrays copied into JP-sized stack buffers (moved ones showed garbage
    in the IQ battle), so ST English fits its JP word count (batches.py lint; 127 lines refit by codex fix).
    Mashin menu strips in English (insert.STRIP_ROWS: Slash/Stab, specials, Retry/Quit; scenes mashin_special,
    mashin_lose retimed). もんペット moves use the 8x16 font at code + 14 (insert.FDS_BF, "Bubble Jet" verified).
    Battle-font space is a blank cell (0 ended header names at the first space); ENE06 Combat Doll header starts in
    the ename slack before it. LVUP digits print at the JP blank cells: line 4 laid out "Wataru: Level  NN!"
    (verified Wataru, Sakuya; Aragoto's cell 8-9 assumed from the JP layout). Code-built room blocks (R08 0x163C0,
    R13 0x16780, R14 0x1BCA0) fixed in place: 13 pages tightened (hand14). BALLBAT 21F04 keeps blank cells 5-6.
    TTL labels fit 13 letters (no column move needed). Last build: build/wataru_en.bin sha1 c77e88ea... (2026-11-14),
    smoke ok, warp_all 46/46, states in work/states/.
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
- **Next (phase 8: QA in the emulator, `references/emulator-qa.md`, `references/graphics.md`):**
  0. Finish the visual-QA gate on build e210ee37: if work/qa/retour.log lacks "in manifest", rerun `warp_all.py
     --jobs 4`, `tools/tour_sheets.py`, `qa_gate.py init work/qa/manifest.tsv work/qa/tour --glob "*sheet*.png"
     --build build/wataru_en.bin`; then `qa_gate.py todo work/qa/manifest.tsv work/qa/verdicts --size 4 --out-dir
     work/qa/chunks` (clear old chunk files first) and `tools/vqa_codex.py <chunks> --jobs 5` (~1 min a chunk,
     background). Verify each issue on full-res frames (`sheet.py f.png --compare jp.png --div 1`) before fixing;
     write overrides with the reason. Check the hitblow card backs are blue circles again and the staff roll page
     bottoms are clean. `qa_gate.py check` must exit 0. Text coverage: make textview.lua's STUCK events end (look at
     state/mode when stuck: choices need a Cross/Down press, scene changes need the room reloaded), run per episode
     from work/states/epNN.sstate, then add the menu/battle sources to strings.tsv (their RAM read address) or waive
     them by source with reasons in docs/text_unshown.tsv.
  1. Remaining graphics rows (docs/re/graphics.md), with the gfx.py pipeline, in the main thread (codex's sandbox
     can't run Python, Orca refuses nested workers): G17/G18 in game (graphics.md rows: find the BALLBAT sprite
     list that cuts each bubble rect and the action that plays it; or waive with the offline check),
     G23 leftovers (the drawn-not-seen G23 labels in graphics.md, e.g. 最終話, Warurine in the party),
     G19 leftovers: VS cards of episodes 2-14 assumed to use the ep1 record layout (spot-check one later matchup with
     a poke of the battle id if one is found), G20 other moves (Skysoar / RISE..SWORD chant: ep 14 for Tensho; the
     third+ list entries),
     G22 room signs (decide per sign, waive illegible), FMV + FK stills
     check (ep00 opening FMV: no burnt-in text seen). Battle names col B (u 160) is drawn somewhere not yet seen: check it. See G12 (IQ
     win/lose cards, hit-and-blow labels: the ep1 IQ battle is the KIO memory game), G17, G18 in game (add scenes or
     `late=` pokes to reach them).
     Screenshots are 320x240 even where the game runs wider: zoom (`sheet.py --crop --zoom 3`) before judging.
     Then routes + contact sheets with visual-QA verdicts (`qa_gate.py check`), `inkbox.py`, `textcover.py`.
     Tour plan: rebuild, `warp_all.py` (all scenes; sheets land in work/qa/warp/<scene>/sheet*.png), the same on the
     original cue into work/qa/tour_jp, `qa_gate.py init work/qa/manifest.tsv work/qa/warp --build build/wataru_en.bin`,
     `todo --size 30 --out-dir work/qa/chunks`, then a fresh read-only pass per chunk (codex exec or own) per
     docs/visual-qa-brief.md writing work/qa/verdicts/<chunk>.tsv. textcover has no infra yet: needs build/strings.tsv
     (string id -> RAM address it is read from; room text shares overlay RAM per room, so log room + address) and a
     `TEXT <addr>` log from a text hook (the 16x16 glyph path in docs/re/font.md). Note: sheet.py doesn't create the
     --out directory.
  2. Carried from phase 7 (QA must confirm or fix): FDS monpet name-entry grid 0x18468 is still kana (no scene
     reaches it yet; find how 0x77C78 なまえを入れてください is reached, then put Latin letters in the grid as
     single-letter pair codes, and check where entered names are drawn: 16x16 font = pair codes, 8x16 = code+14);
     BALLBAT 21F04 "Immune to [blank cells] !" (what the game draws in cells 5-6); Aragoto's LVUP digit cells;
     TTL label "Mashin Battle" (13 letters) against the value column (extra config page, not in a scene yet);
     the English save title (script/MEMORY.json) in a saved card (`tools/debug/blank.mcd` after scene save: header
     title at block offset 0x04) and wherever the game lists saves; a battle that uses もんペット (BALLBAT table
     bases 0x800F1C1C / 0x800F52E8 waived in test_reloc: watch them there too).
  3. Text edits: always through a batch (`batches.py merge NAME --overwrite`, handN for hand fixes; next: hand20).
     ST lines can't grow past their JP word count; polish.md minors on ST must keep that limit.
  4. docs/polish.md: 6 "cut" name lines (header 11 letters / strip 16 are display limits: put the full name where
     the field allows it or waive) + the minors, before phase 9.
- **Open bugs:** none.
- **Waiting on the user:** nothing.
