# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 9. Release: done (2026-11-15). `tools/release.py` passed every gate on build **02e1b54d** and wrote
  `release/Wataru-Another-Step_EN_v1.0.zip` (xdelta + README.txt; zip sha1 d38ab729..., patched CRC32 064D3105,
  re-applied identical). Publishing (tag, `gh release create`) is the owner's call: not done.
  **That zip is now stale**: FMV subtitles (below) changed the disc; build **c5b3aa44** needs the release gate rerun
  (qa_gate will say STALE: re-tour or waive the scenes, then `tools/release.py`).
- **Done:**
  - Session 25 (2026-11-15): **FMV subtitles** (D26), all 4 movies PRG/WATA01-04 (OUT/*.STR are audio only).
    Lines in `script/fmv.tsv` (faster-whisper large-v3 transcripts in work/fmv/*.asr.tsv, checked by ear-free
    context: WATA01 opening song "STEP" lyrics, 02 prologue, 03 summon shouts, 04 ending dialogue; the lyric lines
    and the WATA03 shouts いっくぞー/登龍剣 are best-guess hearings, a native listen is in docs/polish.md).
    `tools/fmv.py` (build.py calls it, cached by hash): libass in the black-matrix-00 style (user: same style, no
    background), jPSXdec partial-replace on the text rect, measures every frame against jPSXdec's decode and
    re-encodes starved ones whole; worst error 7.4 (limit 12). Scenes movie0-3 (movie index 0x8009C978 = WATA01-04) show every movie's lines in game
    (work/qa/warp/movie*/subs). Check 115 passed, smoke ok on c5b3aa44.
  - Phase 9, session 24 (2026-11-15): **story pass** (new `tools/story.py`: chapters R00-R14 + ST from script/,
    `codex exec` per chapter with docs/story-reviewer-brief.md; reports work/qa/story/reports, earlier rounds in
    reports/r1, r2): 15/15 ok after 3 rounds. Fixed hand26-28: R06 Himiko's やれ echo ("give it a rest" / "Give it to
    him!"), R13 剣 clue -> "swordsman", R13 quiz 漢 vs 男 -> "Capital-M Man" / "Man" (R13 kanji OCR shows 漢 as 満 in
    script/, display only) + 14 Minors; all in docs/polish.md (ticked). Rebuild -> re-warped 17 scenes, 4 changed
    sheets judged ok (codex), gate 1071/1071 on 02e1b54d; coverage logs remapped (old build's strings.tsv rebuilt in
    work/old_build -> work/qa/cover/strings_a0774c53.tsv; old merge kept as work/qa/cover_now_a0774c53),
    textcover exit 0. **jp_left**: every disc file scanned (rewritten files vs original, min 4; untouched min 6):
    149 runs, all data noise (map/graphics/audio/STR/tables), listed in docs/jp_known.tsv; release.py fails on any
    new run. New `tools/release.py` (build, tests, smoke, jp_left, qa_gate on every work/qa/**/manifest.tsv,
    textcover, polish, README placeholders, xdelta -B 1 GiB, re-apply compare, zip), `docs/release-readme.txt`,
    README filled (status table, base hashes). Superseded manifest work/qa/old moved to work/qa_old_manifest.
  - Phase 8, session 23 (2026-11-15): **monpet names in letter codes** (D25): c = ASCII - 0x20, one letter per cell,
    in exe_enemies (insert.py `enemies` table -> FDS_BF path), the name grid (both cases on one page, rows A-Z
    .-!?, a-z, 0-9; case key cells 85-86 = 0, labels code 0) and so in every roster name; the roster card draws them
    unchanged (8x16, glyph c + 14). 16x16 draws patched to 8x16 (insert.NAME_DRAW): shop list 0x801043F4, cart list
    0x801052F0 (not reached in a scene: static check only), name box 0x80107C5C, and the box's green next-letter
    frame (0x80108AB0, x = 16 + len * 8). A wrapper in the dead case-offset block 0x801078B8 also uploads a blank
    cell 80 px right of each glyph (8x16 cells left the strip's right half stale: old dialogue showed in the shop
    list). Grid cells use MSG_CG 16x16 slots 1-0x5F (letter centred, `insert.name_cell`). Names cut to 10 letters
    under D19: Megadragonfly -> **Megafly**, King Croakpuff -> **King Croak** (hand25, glossary). Scenes re-warped
    and re-judged (codex, chunks23: 6 ok); roster_name now pokes "Ab z". EXE 7B050 "Got 1500 Ganbo!" moved with the
    shorter line: re-logged (exe_log_keep.txt). debug.md: name task 0x800C0E28, length 0x800C0E7E.
  - Phase 8, session 22 (2026-11-15): **monpet name entry reached and English**: field state 0xB + 0x8009C85A 0
    starts FDS task 0x250 (debug.md "Monpet name entry"); scenes name_entry / name_saved. Grid (FDS 0x18470) now A-Z,
    digits, `.-!?` and a working case key "A/a" (insert.NAME_GRID: single-letter pair codes at fixed codes at the end
    of the compose table, lower = upper + offset patched over the 0x55 at 3 sites, label in blank MSG_CG slots
    0x55/0x8E). Verified typing "ABfz", Exit, Yes. **Bug found: the roster card draws names with the 8x16 font**
    (FDS 0x80102A64: src 0x80110380 + code * 64 = glyph code + 14, 10 cells) -> EN species names (pair codes, from
    the chest/shop copy) and entered names draw nothing there; JP shows the name (codex verdict, name_saved/sheet_4,
    work/qa/tour_jp/name_saved/final.png). Not fixed: Next 0. **Missed string**: EXE 0x77808 もどれませぬぞ (map
    edge, EXE 0x800434E8) showed Japanese: new FIXED table `exe_no_way_back` ("No going back!", hand24; 0x77818 has
    no reference: waived); sweep of every stream for uncovered runs ending in a page terminator found no other.
    batches.py counts a raw `[XXXX]` word as one cell. Scene no_way_back.
  - Phase 8, session 21 (2026-11-15): **coverage 6 -> 0**: shop builders traced (debug.md "Shop messages"): new
    scenes shop_nomoney / shop_carry (cart + money pokes, actor 0x800C0DBC step 0), shop_leave (EXE 0x8004A844's
    writes), item_order2 (3 picks -> title box). 77C00 "You already have it." waived (dead branch). **Bug: "Customer!
    Just a moment." showed Japanese** in the real flow: the EN line outgrew its 26-byte slot and was moved, but the
    code (`lui/addiu` 0x8004A8D4) still started the old JP copy; coverage hadn't caught it (hijack used the EN address)
    -> hand22 shortens it to fit in place; sweep of every moved string found no other unreferenced move. **Item-order
    title "Confirm" off-centre 9 px** (8-px letters can't centre 7) -> hand23 "Done" (inkbox 116/117; batches.py
    CENTRED exempts it from the cursor-indent rule). G17/G18/G22 SAKE: English art found in game VRAM dumps
    (work/qa/g18v/bubbles_vram.png, work/qa/g22s/sake_vram.png). Re-tour of the 4 new scenes (EN + JP) judged ok.
  - Phase 8, session 20 (2026-11-14): **re-tour on d7ca3b3b**: EN + JP warps of shop, shop_confirm/monpet, chest_*,
    items_c/d, keys_b, abil_all/b -> 139 new sheets judged by codex (chunks20), 15 issues all false positives,
    overridden in zz_controller.tsv (chest_mon* empty second box = the original's own, work/qa/p8x/chestB.png;
    "..." drift; Ep.01 box cosmetic) -> `qa_gate.py check` 1041/1041. **Coverage 75 -> 6 left**: all 36 ST IQ
    branch lines via new `tools/lua/iqstep.lua` (jumps an IQ game actor's step/sub-step: debug.md "IQ battle
    steps"; runs work/qa/iqs/<run>, logs merged as cover_now/ncover/iqs_*), 4 monpet naming lines via new scene
    **act250** (shop/naming actor action 0x250 spawned in slot 12, iqstep `OBJ=0x800BDC60 SETTOP=4|6`), rooms 29
    via textcover_run `--chunk 1 --timeout 150` (run8, then cover_remap). EXE 0x800315CC starts action 0x250 at
    0x800C0E28 when u16 0x8009C85A == 0; FDS actions 0x22A-0x22C (scenes act22a-c) read nothing. Build unchanged.
  - Phase 8, session 19 (2026-11-14): coverage 107 -> 75 left, 2 real bugs fixed, build d7ca3b3b (smoke ok, 111
    tests). **Bug: junk glyphs after "Opened the treasure chest!"**: EXE 0x80055EE0 uploads exactly 16 glyph words
    of the chest lines (7A4DC empty / 7A500 opened / 7A524 bottle) with no end check; the JP fills them with blank
    cells, the moved EN didn't -> insert.py pads moved EXE strings whose JP ends in blank cells to the JP length
    (strings.tsv unchanged, so coverage logs stay valid). **Bug: shop "Is this OK? Yes No"** cursor covered "Yes"
    (Yes at cell 8, JP はい at cell 10): hand21 respaces to cells 10 / 13 (matches JP, work/qa/warp/shop_confirm).
    s18's "monpet naming flow" was the **treasure chest** (debug.md "Treasure chest", corrected): scenes
    chest_open/empty/bottle/monpet + chest_mon1-4 (warp.lua `chest=A-B`, kind 5 = monpet) -> all 30 species names
    read. Shop kinds (u16 0x8009C914 0-3): scenes shop_confirm (kind 1: Yes/No box) and shop_monpet (kind 2). The
    exe_monpet_lines (77C58..77CB8) are drawn by FDS 0x80107AEC (16 glyphs, line = arg; callers 0x801072F4,
    0x80107694, 0x801078A0, 0x8010794C, 0x801079F8): the naming screen is FDS code, not yet reached; monpet buy via
    0x80042228 (needs money u32 0x8009C8B4 + an Other-tab item 4 bottle), but Circle in a poked shop never buys.
    New scenes not toured yet (EN warp exists in work/qa/warp, JP only for chest_monpet/shop_confirm): chest_*,
    shop_confirm, shop_monpet + the 5 from s18.
  - Phase 8, session 18 (2026-11-14): coverage 177 -> 107 left (no rebuild, build 48f7e75a). New scenes (logs in
    work/qa/ncover/<scene>, merged into work/qa/cover_now/ncover/): **items_c / items_d** (4th Use tab "Other" =
    inventory 0x800A3568: items_b never switched to it; the list reads only 8 rows: consumables 44-58 + effects
    all shown), **keys_b** (key-item list is 2 columns: right column = even items, all 16 descs shown),
    **abil_all / abil_b** (abilities: FDS 0x80101740 per character u16[10] at 0x800A96D0; only slots 1-7 read).
    Tried, nothing new (scenes removed): practice IQ games held 30k frames (iql0-3), story IQ ep 4/8/10 mashed 30k
    frames, ep 10 refusing the rules (No): none reached the ST win/lose/retry lines. Monpet naming flow traced
    statically to task type 0x210/0x211 started by EXE 0x8004EC74 (debug.md "Monpet naming flow"); caller unknown.
    Not toured yet: the 5 new scenes (EN + JP warp, sheets, qa_gate init/todo, vqa_codex) - menus only, no build change.
  - Phase 8, session 17 (2026-11-14): **tour extended** to the coverage scenes (title_extra/values, iqp/iqn 0-3,
    items_all/b, keys_all, gear_all, places0-5, mcover02-14, monpets1-2, item_order; EN in work/qa/warp, JP in
    work/qa/tour_jp, sheets work/qa/tour + tour_jp_full): 188 new/changed sheets judged by codex (vqa_codex.py),
    1 real issue: **cake-game まけ! stone card still Japanese** (IQ/BUR_MAIN.CHG; PUZ_MAIN.CHG has the same cards):
    gfx.tsv BUR_/PUZ_ rows + gfx_gen.iq -> LOSE! verified in iqp2 (f6600). Gate 902/902 on 48f7e75a (items_all /
    items_b report "False" in warp_all but reach the menu, exit 0, final yes; same on the JP). **Coverage**: monpet
    special moves all shown (scenes monpets1-2: roster species poke, debug.md "Monpet roster"), item-order line
    (scene item_order). Probes that found nothing (removed): shop buy route (no confirm/money line read), shop id
    0x8009C85A 1-8 (no reads at all), IQ Start -> Retry / Give Up from practice (game index differs) and ep1 story
    (that battle forbids giving up). Species names (exe_enemies) are copied only at monpet acquisition (debug.md).
    Build 48f7e75a: smoke ok, 111 tests.
  - Phase 8, session 16 (2026-11-14): coverage 440 -> 192 left. **Clear flag u8 0x8009C681** unlocks title Config
    rows IQ Battle / Mashin Battle (debug.md); scenes title_extra, title_values (every Config value: TTL all but
    056DC, waived: no pointer), iqp0-3 / iqn0-3 (IQ practice of each game, mash Circle / `mashkey=down/circle` =
    take No at choices; warp.lua `mashkey`). **Bug fixed**: "Mashin Battle" touched its value ("Choose an enemy
    mashin") -> value column x 115 -> 123 (insert.CODE TTL 0x360C `lui v1,0x7B`; verified work/qa/p8x/tv_zoom.png).
    MACHINE 34/34 via `tools/lua/mbanall.lua` (forces each banner name from work/states/mashin_attack.sstate; reads
    = glyph uploads, banner not drawn in the menu state). Gear: list 0x800A9758 poked ids 1-88, scene gear_all (all
    88 names). Places: scenes places0-5 poke ep + place index and open the menu (all 48; 9 per scene: debugger runs stall
    ~f9600). New tools/cover_missing.py
    (report -> id, script file, English), tools/lua/sprx.lua (who sets a sprite's x). warp_all: debugger wall
    timeout frames/8. Build 0051ad42: smoke ok, 111 tests.
  - Phase 8, session 15 (2026-11-14): **room coverage** rounds 6-7 (`textcover_run.py --base work/qa/cover_e210
    --jobs 5 --chunk 5`, then `--chunk 2 --timeout 75`): rooms 458 -> 29 left. **Menu viewers** (readlog.lua,
    --debugger, logs in work/qa/ncover/): new scenes items_all + items_b (every consumable in Use tabs 1-3 + effect
    lines; inventories 0x800A3510 x16 = ids 1-16, 3530 x8 = 18-25, 3548 x16 = 27-42), keys_all (key items 1-16 +
    descriptions), mcover02-14 (each episode's mashin battle, no banner logged yet). warp.lua: press step
    `FRAMES:BTN/GAPxN` repeats; GOD pins mashin HP in mode 7. New tools/cover_ids.py. **BALLBAT/ENE waived as
    unloggable** (326, docs/text_unshown.tsv: debugger freezes ball battles even from a mid-battle state; no
    pollable pointer/buffer). Coverage 4,512 -> 5,039 shown + 326 waived. Build unchanged (90f876dc), 111 tests.
  - Phase 8, session 14 (2026-11-14): **room coverage** run4 killed (hung chunks idle to the 900 s timeout: the emulator
    freezes after ~30 s of real work), run5 (`--jobs 6 --timeout 90`) took rooms 3,507 -> 4,141/4,599 before Claude
    Code reaped it for low system memory (other repos' Mesen); not restarted this session per that notice.
    `textcover_run.py --base DIR` runs on a frozen copy (**work/qa/cover_e210** = build e210ee37 + its ep states +
    FPRG, same subpaths) so the repo can rebuild meanwhile; default timeout 90. **EXE dialogue pages** (item get, shop,
    save lady, inn: 230 EXE.json entries of kind next/ptr/code) all shown: `textcover_run.py --exe --only 38 --out
    <ABSOLUTE dir>` (pass-2 hijack of ep01's host event; textlog.lua `EXETAG` logs EXE-range pointers as menu keys
    0x26xxxxxx) -> work/qa/cover_exe. **Rebuilt** (polish hand20 + G22 signs): smoke ok, 111 tests, warp_all 58/59
    (endreal = known FMV stall). **G22 INN** board legible in game (work/qa/g22/inn_zoom.png, field state walked
    left+up); the 飯 column stays blank (INN = 3 of the 4 board columns). SAKE lantern not on that route. Re-tour:
    81 changed sheets judged by codex, 1 issue: shop "Ganbo" last o under the window border -> label drawn 1 px left
    (gfx_gen.shop; 5 Spleen letters need 29 of the 30 visible px, so G now sits tight to the digits). **Build
    90f876dc**: smoke ok, 111 tests, `qa_gate.py check` 717/717 (shop/sheet_3 "..." drift override in zz_controller).
    Coverage merged for this build: `cover_remap.py work/qa/cover/strings_e210.tsv work/qa/cover work/qa/rcover --out
    work/qa/cover_now` + work/qa/cover_now/exe/log.txt (cover_exe TEXT lines) -> report work/qa/cover_now_report.txt:
    **4,512/5,805**; missing: rooms 458 (361 next, 67 ptr, 30 event), EXE 307 (name/menu tables), BALLBAT 206, ENE 120,
    ST 90, FDS 50, MACHINE 32, TTL 30.
  - Phase 8, session 13 (2026-11-14): **G22 room signs** (D24): FR room atlases are 4bpp (the sweep misread them as
    8bpp); 酒 lantern -> SAKE (15 rooms), 一宿一飯 board -> INN (18 copies, 9 pngs; R07M0/R10M0 boards cut in two
    pieces) via gfx.tsv rows with CLUT "-" (`gfx.GREY` index palette, `gfx.row_lut`) and `gfx_gen.signs`; offline
    sheets work/g22/cmp4.png. Not in a build yet (coverage run reads build/). Rest of G22 left as illegible set dressing.
    **Room coverage run3 added nothing** (machine shared with other repos' emulators: ~13 fps, chunks timed out at
    150 s, some died with no output); **run4** = `textcover_run.py --jobs 3 --chunk 10 --timeout 900` (log
    work/qa/cover/run4.log, buffered) was running at hand-off: 3,492/4,599 after its first chunks.
  - Phase 8, session 12 (2026-11-14): **polish pass done** (docs/polish.md 0 unticked): work/tl/hand20 (96 entries,
    merged; ST/10-cell-field lines that can't fit waived with reasons; G25 readings waived per D21). Script changed,
    **build NOT rebuilt** (still e210ee37: coverage runs were using it); 111 tests pass on the new script.
    **Room coverage**: run2 = 3,407/4,599 pages (work/qa/cover/report.txt; ep01 234/234; 64 chunks timed out);
    run3 (`textcover_run.py --jobs 4`, resumes) was started detached at hand-off -> work/qa/cover/run3.log.
    The old build's strings.tsv (rooms + menu lines) is saved as work/qa/cover/strings_e210.tsv: after a rebuild,
    `tools/cover_remap.py work/qa/cover/strings_e210.tsv work/qa/cover work/qa/rcover --out work/qa/cover_now`
    carries every shown id to its new key (page ids survive text edits; tests/test_cover_remap.py).
    **Menu/battle coverage**: `insert.strings()` now also lists every EXE/overlay/ENE string (kind `menu`, key =
    (0x20 + source index) << 24 | RAM address, col 4 = first 4 bytes); new `tools/lua/readlog.lua` (read
    breakpoints over spans of string first words, bytes checked since ST/BALLBAT/MACHINE/TTL/LVUP share 0x800D0000;
    needs --debugger; DEBUG/DLO/DHI vars). warp_all over all scenes with it (work/qa/rcover, report
    work/qa/rcover_report.txt): **140/1,206 shown** (field menus, shop, title, ST, MACHINE, FDS). **Battles hang
    under --debugger** (the interpreter: battle bg loads, UI never appears, cold boot or from the stalled state;
    levelup/battle_win warp timeouts), and from a dynarec battle state nothing is read (BALLBAT builds its lists/
    names once at setup, e.g. item list buffer 0x80101478). G22 note: a legible 飯 sign shows on a field building
    (scene field) -> room-sign redraws are real work.
  - Phase 8, session 11 (2026-11-14): **visual-QA gate passes** on build e210ee37 (`qa_gate.py check` 717/717:
    re-tour 58/59 scenes (endreal: known FMV stall), 43 changed sheets re-judged by codex, all ok incl. hitblow card
    backs, staff-roll page bottoms, Config heading; false positives overridden with reasons in
    work/qa/verdicts/zz_controller.tsv). vqa_codex.py verdict files are now dated (qa_gate's chunk_NNN names
    overwrote 44 round-1 verdicts; re-judged). **Text coverage works for room text**: the s10 viewer only ever
    replayed the bank start (state 3 reads the event start u32 0x8009C9A4, not 0x8009C998; 7-word header; debug.md
    "Dialogue viewer" correction). New textview.lua: pass 1 starts each 'event' page at its header, pass 2 redirects
    a HOST event's pointer to every page still unseen (NPC talk), free-walk snapshot reloaded per event.
    strings.tsv col 3 = page header kind (insert.strings()). New `tools/textcover_run.py` (per episode, chunks of 30
    pages, resumable). ep01: 230/234. A full run (twice, all episodes) was started at hand-off: logs
    work/qa/cover/run1.log, run2.log, report in work/qa/cover/report.txt. Build unchanged (e210ee37), 110 tests.
  - Phase 8, session 10 (2026-11-14): **visual-QA tour started**. warp_all on EN + original (work/qa/tour_jp, states
    work/qa/tour_jp_states; 70/71 reach, `endreal` times out on both after its AT at f8301: the emulator stalls in
    the ending FMV, harmless, the roll is covered by staff_roll). New `tools/tour_sheets.py` (full-scale sheets,
    8 frames a page: emu.py's half-scale sheets made codex flag every pixel-font label as garbled, 60 false issues)
    -> work/qa/tour (717 sheets) + work/qa/tour_jp_full; new `tools/vqa_codex.py` (codex exec read-only, EN + JP
    sheet per id, writes work/qa/verdicts/<chunk>.tsv). docs/visual-qa-brief.md got the game's standing non-bugs.
    Round 1 on build 25e4d369: 702 ok, 15 issue; real ones fixed: **ST blank-cell padding** drew past the IQ box's
    16-cell VRAM buffer (704,0) and wiped the hit-and-blow card backs at (768,0) (insert: ST strings now end with
    their terminator after the text; found with new `tools/lua/loadwin.lua`); **staff roll**: the next page's first
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
- **Next:** release v1.0 is built and verified; publishing waits on the owner (never `gh release create` or a
  visibility change without them). Player bug reports -> GitHub issues (AGENTS.md). For any later fix: edit through a
  batch (next: hand29), rebuild, re-warp the scenes that show it + sheets + `qa_gate init/todo` + `vqa_codex.py`,
  remap coverage (save the old build's strings.tsv first: `build.py --out` on the old script), changed chapters
  through `story.py chapters` + qa_gate init + `story.py review CH`, then `release.py --version 1.x`.
- **Phase-8 reference (QA recipes; gates pass on a0774c53):**
  00. Visual-QA gate: passes on a0774c53 (1071 sheets). After any rebuild: rerun the scenes that show the change
     (warp_all --only, EN), `sheet.py work/qa/warp/<s> --div 1 --max 8 --cols 4 --out work/qa/tour/<s>/sheet.png`
     (or tour_sheets.py for all, ~15 min), `qa_gate.py init work/qa/manifest.tsv work/qa/tour --build
     build/wataru_en.bin`, `todo --out-dir`, `vqa_codex.py <chunks> --jp work/qa/tour_jp_full`. A new scene also
     needs its JP warp (`--rom <orig cue> --out work/qa/tour_jp --states work/qa/tour_jp_states`) + JP sheet.
  0. Text coverage: exit 0 on 02e1b54d (s24: the per-scene ncover logs are a0774c53 keys, kept in
     work/qa/cover_now_a0774c53/ncover and remapped into cover_now/ncover_a0774c53 with strings_a0774c53.tsv; the
     recipe below now remaps them too). Battle draw of monpet names not checked (ball battles unloggable; a 16x16
     draw of a name would show centred letters from MSG_CG slots 1-0x5F).
     **Merge recipe** (after any new run): `tools/cover_remap.py work/qa/cover/strings_e210.tsv work/qa/cover
     work/qa/rcover --out work/qa/cover_now`; `cp work/qa/exe_log_keep.txt work/qa/cover_now/exe/log.txt` (EXE
     dialogue pages); copy each `work/qa/ncover/<run>/log.txt` (current-build keys, not remapped) to
     `work/qa/cover_now/ncover/<run>/`; then `textcover.py work/qa/cover_now build/wataru_en.strings.tsv --waive
     docs/text_unshown.tsv`. `tools/cover_ids.py DIR` lists the ids a log dir shows.
     BALLBAT/ENE (326) are **waived as unloggable** (docs/text_unshown.tsv, reason in each line; gotcha in
     docs/skill-gotchas.md): --debugger freezes ball battles even from a dynarec mid-battle state, and RAM dumps
     through battle_win found no pointer slot or message buffer to poll. Visual-QA gate: passes on 90f876dc; any
     rebuild needs a re-tour (pixel-only changes: rerun just the scenes that show them, as the shop in session 14) (`warp_all.py`, `tour_sheets.py`, `qa_gate.py init/todo`, `vqa_codex.py`).
  Older phase-8 notes (non-gating, kept for reference):
  1. Remaining graphics rows (docs/re/graphics.md), with the gfx.py pipeline, in the main thread (codex's sandbox
     can't run Python, Orca refuses nested workers): G17/G18 in game (graphics.md rows: find the BALLBAT sprite
     list that cuts each bubble rect and the action that plays it; or waive with the offline check),
     G23 leftovers (the drawn-not-seen G23 labels in graphics.md, e.g. 最終話, Warurine in the party),
     G19 leftovers: VS cards of episodes 2-14 assumed to use the ep1 record layout (spot-check one later matchup with
     a poke of the battle id if one is found), G20 other moves (Skysoar / RISE..SWORD chant: ep 14 for Tensho; the
     third+ list entries),
     G22 SAKE lantern in game (find a room that shows it: gfx.tsv sign rows list the 15 FR files), FMV + FK stills
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
  2. Carried from phase 7 (name-entry grid done s22-23, letter codes): BALLBAT 21F04 "Immune to [blank cells] !" (what the game draws in cells 5-6); Aragoto's LVUP digit cells;
     TTL label "Mashin Battle" (13 letters) against the value column (extra config page, not in a scene yet);
     the English save title (script/MEMORY.json) in a saved card (`tools/debug/blank.mcd` after scene save: header
     title at block offset 0x04) and wherever the game lists saves; a battle that uses もんペット (BALLBAT table
     bases 0x800F1C1C / 0x800F52E8 waived in test_reloc: watch them there too).
  3. Text edits: always through a batch (`batches.py merge NAME --overwrite`, handN for hand fixes; next: hand26).
     ST lines can't grow past their JP word count; polish.md minors on ST must keep that limit.
  4. docs/polish.md: done (session 12).
- **Open bugs:** none.
- **Waiting on the user:** (non-blocking) G17/G18 ball-battle bubbles and the G22 SAKE lantern are checked as English
  art loaded in game VRAM, not on screen (the enemy actions / camera spot were never reached); default: accept.
  (non-blocking) 326 ball-battle strings (BALLBAT, ENE) are waived in docs/text_unshown.tsv
  as *unloggable*, not unreachable: the read probe can't run in ball battles (emulator debugger freezes them). The
  skill's gate wants waivers only for unreachable text; the alternative is a QA-only logger patched into the
  BALLBAT renderer. Default: keep the waiver, battle text judged on the tour sheets.
