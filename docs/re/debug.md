# Game flow, RAM map and the debug warp (phase 2)

Tools: `tools/debug/warp.lua` + `tools/debug/scenes.txt` (scene list), `tools/debug/warp_all.py` (every scene from a
cold boot, states to `work/states/`, summary `work/qa/warp/summary.tsv`). Probes: `tools/lua/ramlog.lua` (log value
changes), `tools/lua/poke.lua` (RAM writes from a state), `tools/lua/fileload.lua` (file-table reads, `--debugger`).
Static helpers: `tools/filetab.py` (file table), `tools/loadcalls.py` (load-by-index calls in a code image).

## Main loop (verified: disassembly + forced-mode runs from `work/states/idle_ep01.sstate`, 2026-11-13)

- 0x8001F114: `jalr table[SysMode]`, table 0x80075D64 (23 entries), then debug printfs "Check SysMode"/"Stage No".
- **SysMode** u8 0x8009C7FC. Writing it from Lua takes effect on the next main-loop pass; every value below was
  reached that way from the field:

| Mode | Handler | What | File loaded (table index) |
|---|---|---|---|
| 0x14 | 0x80058904 | boot: logo, attract FMV, title art (loops until Start) | BP_LOGO |
| 2 | 0x8005AC64 | title menu ニューゲーム/コンティニュー/コンフィグ (TTL.BIN). New Game sets ep = 0xFFFF, plays WATA02 (movie, Start skips), then mode F | 1 TTL |
| 9 | 0x8005AE34 | movie player (index 0x8009C978) | 5 MOVIE |
| F | 0x8005AC28 | area map + episode title card (SBTTL.BIN): ep += 1, then mode C | 2 SBTTL |
| C/D | 0x8005832C | room setup / episode flow (room overlay init 0x800CE198); at ep 15 the ending | room files |
| 3/4 | 0x8002DABC / 0x80033ED8 | enter field after an event / a battle | |
| 5 | 0x8002F8D4 | field main loop (sub-state 0x8009C788, below) | |
| 6 | 0x8005A6C0 | battle (BALLBAT.BIN) | 8 BALLBAT |
| 7 | 0x8005A98C | mashin battle (MACHINE.BIN); stage word 0x8009C618 = table 0x80081DCC[ep] | 7 MACHINE |
| 8 | 0x8005AAC4 | IQ battle (ST.BIN, entry 0x80108328); result u16 0x8009C74C: 1 win -> mode 4, 3 retry, 0/2 -> mode 2 | 0 ST |
| B | 0x8005ACE0 | level-up screen (LVUP.BIN), then mode 4 | 3 LVUP |
| 10/11 | 0x8005AD28 | memory card save (10) / load (11) (MEMORY.BIN) | 6 MEMORY |
| 16 | 0x80058B78 | staff roll | STAFF.BIN |
| 12/13/15 | 0x800595CC / 0x800598D8 / 0x80058738 | not identified yet (15 = field re-entry after Continue, guess) | |

- Script calls that start these: 0x800336D8 save (mode 10), 0x80033734 IQ battle (mode 8), 0x800337DC mashin battle
  (mode 7), 0x80033A2C / 0x80033E5C battle (mode 6).

## Episodes (verified by warp: card text, overlay compare, font compare)

- **Episode index** u16 0x8009C90C: 0 = prologue (創界山のふもと), 1-14 = 第01話-第14話, 15 = ending (set by
  0x800580B0 when ep 14 ends). 0xFFFF on New Game; SBTTL adds 1 before it draws the card, so the warp writes N-1.
- Overlay per index (warp_all ROOMHEAD compare of 0x800CE000 with each file): 0-11 = `FPRG/R00-R11.BIN`, **12 and 13
  both R13.BIN**, 14 = R14.BIN. R15.BIN is a 472-byte stub (ending?). There is no R12.BIN.
- Room font per index: switch 0x800272F8 on 0x8009C90C (jump table 0x8001D848), verified by comparing RAM
  0x80122500 with the font files in the ep01/03/05/12/13/14 states: 0-1 M16_R00, 2-3 M16_R02, 4-5 M16_R04,
  6 M16_R06, 7 M16_R07, 8 M16_R08, 9 M16_R09, 10 M16_R0A, 11 M16_R11, 12 M16_R12, 13 M16_R13, 14 M16_R0E.
  So R01/R03/R05 share their font with R00/R02/R04, and R13.BIN's text is drawn with M16_R12 in episode 12 and
  M16_R13 in episode 13: **the kanji table is per episode index, not per R file** (phase 4).
- Episode end: 0x8009C7B0 == 0xFFFF -> next card (mode F), or the ending when ep is 14. Otherwise 0x80032144(id)
  starts event `id` of the room (sets field state 3).

## Field (verified by ramlog + button tests from idle_ep01)

- Field sub-state u16 **0x8009C788**, handler table 0x800819DC: 0 free walk, 3 event, 4/5 message window,
  **9 field menu** (Triangle; アイテム/そうび/もんペット/ステータス/コンフィグ + party panel; loads FDS.BIN + FD_STS),
  **0xA shop** (loads FD_SHP.PX; writing 0xA with step counter 0x8009C85A = 0 opens the item shop list), 0x10 after a
  save. 0x80 bit set by 0x800581E8 (guess: pause).
- Party stats 0x800A8D38, 8 bytes per member: hp, hp max, mp, mp max (u16). ワタル 114/114 18/18, アラゴト 144/144,
  サクヤ 90/90 20/20 at the start of ep 1. `GOD=1` (or scene key god=1) pins hp/mp to max.
- Battle (mode 6) keeps its own party units at **0x800BF924**, 0x6C each: hp, hp max (u16) (verified: RAM search in
  the battle_ball state); GOD pins those too while mode is 6. Without it the forced ep-1 battle (ファックスメン + 12)
  is lost: lose message, black, then the title (mode 2): no separate game-over screen seen (scene battle_lose).
- Field menu (Triangle) needs ~150 frames before it takes the next press; presses 40 frames apart then register.
- Key-item list: 50 bytes at **0x800A91F8** (item ids, 0 = empty; FDS.BIN 0x800F8E20 compacts it, 0x800FC79C reads
  the cursor's item for its description). Scene menu_key pokes ids 1-4. The battle item inventory is elsewhere and
  still unknown (not read from 0x800A8E00-0x800AA000 in battle; scene battle_menu reaches the command cursor only).
- Mode 0x16 forced from the field shows static staff-roll pages; the real staff roll plays inside the ending
  (scene `ending`: ep 15 + mode C loads R15.BIN, FMV, then the credits text).
- Forcing mode B (level-up) from the field leaves a black screen forever (LVUP loads ~10 files, guess: it needs
  the post-battle state). After a battle the mode-6 handler goes to mode 4, or to mode B when u8 **0x8009C758** is
  set (0x8005A7E0); writing the flag every frame does not stick (cleared just before the test), so scene `levelup`
  wins the ep-1 battle (GOD + Circle) with a debug-only RAM code patch: nop the `beqz` at 0x8005A7EC. The screen
  shows ワタルはレベルアップ！ … レベル０２になった！ ~350 frames after mode B, then returns to the field.
- Battle win: ~10,900 frames of 12-frame Circle presses for the forced ep-1 battle (scene `battle_win`).
- Mashin battle (mode 7) HP, u16, each with a copy: mashin **0x800BE31E / 0x800BEBA4**, enemy **0x800BE38A /
  0x800BEF04** (RAM search 2026-11-14; the bars redraw only on the next hit). Set after the intro (~1,700 frames
  into mode 7), so scenes write them with `late=`. Mashin at 1 + one enemy hit = explosion, then the retry box
  (scene mashin_lose); enemy at 1 + 斬る = explosion, fade, mode B with the story dialogue (scene mashin_win).
  Cold boot: the command menu drops presses until ~2,100 frames into mode 7; then circles 90 frames apart register.
- Monpet roster: 8 x 34 bytes at **0x800A8D60** (u16 +0 nonzero = owned; 1 = a 水 rank-A one), swap list 8 x 6 at
  0x800A9148. Per-episode monpet table u32 0x8008F88C[ep] (6-byte entries: attack-name index into the 10-cell table
  0x80097AEC = exe_mashin_attacks). Scene monpet_detail. (p8 s23: the FDS shop list 0x801043F4 and cart list
  0x801052F0 index 0x80097AEC + 20 * species = exe_enemies, 1-based; cart rows at 0x800A9148, cart list not reached: cart pokes in a poked monpet shop draw nothing, JP too.)
- Clear flag u8 **0x8009C681** (p8 s16): nonzero unlocks the title Config rows IQ Battle / Mashin Battle (TTL
  0x800D0BE8 skips rows 3-4 while 0). Config: circle = edit a row, up/down = value, circle on IQ Battle starts that
  IQ game as practice (scenes title_extra, title_values, iqp0-3 / iqn0-3). Value column x = actor +0x28 set by
  `lui v1,0x73` at TTL 0x800D360C (patched to 0x7B in insert.CODE: "Mashin Battle" touched its value).
- Field-menu place box: FDS 0x800F9468 draws `u32 table 0x801094AC[ep u16 0x8009C90C] + 20 * place u16 0x8009C902`
  (scenes places0-5 poke both, open the menu, restore ep 1).
- Gear inventory: u16 list **0x800A9758** (100 slots, `icon << 8 | id`, id 1-88 = exe_equipment, name table
  0x8009546C + 16 * id); equipped gear per character u16 pair at 0x800A9110 + 4 * (u16 0x8009C750[char]); list cursor
  u16 0x800C1680. Scene gear_all. Mashin banner names: `tools/lua/mbanall.lua` forces all 34 from a mashin state.
- Monpet shop table u32 0x8008F88C[ep] = 6-byte entries [u16 species 1-15, u16 price, u16 rank]; the 30 names in
  exe_enemies are 15 species x 2 (growth?) - not yet mapped to roster fields.
- Monpet roster (p8 s17): u16 species at 0x800A8D60 + 0x22 * slot (8 slots, 2x4 grid: Monpet -> Status; Circle =
  detail, Cross = back). Valid species 1-15; detail "Special" = exe_mashin_attacks[species - 1] (0x80094 +
  0x14 * k; scenes monpet_detail + monpets1-2 show all 15). The detail page has no name. Species names
  (exe_enemies, table 0x80097AEC + 20 * id) are only read by two EXE copy loops, 0x80042564 (in 0x80042228, called
  from 0x80041FBC/0x80042134) and 0x80056FB8 (in 0x80056080, called from 0x80055D60): they copy the name into the
  roster at acquisition (shop / naming screen, exe_monpet_lines), never run in the monpet menus (hits.lua).
- **Treasure chest** (p8 s19; s18 took it for monpet naming): tasks dispatch through u32 table **0x80076840**[u16
  task +0] (current task ptr u32 0x8009C7AC); field actors live at 0x800BD750 + 0x6C * n. Chest actor = type 0x21D
  (0x8004EA60, states table 0x80091654); talking to it (0x800416B0, actor index u16 0x8009C84A) sets its state 1 -> 2
  = 0x8004EC74, which (if chest flag 0x800B2E38[+0x50] & 0x7F is clear) starts slots 12/13 (0x800BDC60 = 0x211,
  0x800BDCCC = 0x210, handler 0x80055AB0, states table 0x80094600) and copies +0x52/+0x54/+0x56 to slot 12 +0x58/
  +0x5C/+0x5E (item id / kind / species). Slot 12 +0x5A picks the line (0x80091D48: 0 empty, 1 opened, 2 monpet
  bottle); **0x80055EE0 uploads exactly 16 glyph words of it** (no end check: EN pads them with blank cells, insert.py).
  0x80056080 gives the item by kind (+0x5C, jump table 0x8001E2F8, 0-6); kind 5 = monpet: species +0x5E goes into the
  first free roster slot with its name copied (0x80056FB8). Scenes chest_open/empty/bottle/monpet, chest_mon1-4
  (warp.lua `chest=A-B`: every species name read).
- **Monpet name entry** (p8 s22): field sub-state **0xB** with u16 0x8009C85A = 0 makes handler 0x80031578 start
  FDS task **0x250** (0x80107184, states table 0x8010F44C): 0-1 open, 2 "Please choose a Monpet" (roster; Circle on
  an owned slot whose +4 is 0 -> state 4; in field state 0xF the same pick releases the monpet, state 8), 4-5 slide,
  6 the grid (0x80107788: cursor col u16 0x800C0EE4 0-9, row 0x800C0EE6 0-8; name u16[10] at 0x800B3670, length
  task +0x56, case flag +0x54), 7 "Is this name OK?". Grid draw 0x80107D5C. The task is at 0x800C0E28 (length
  0x800C0E7E); the name box 0x80107C5C draws 10 cells; its green next-letter frame is the actor at 0x800C0F04, x set
  at 0x80108AB0 (16 + length * 16). English names are letter codes: insert.NAME_GRID / NAME_DRAW. Scenes name_entry / name_saved (poke
  slot 1 species, state 0xB, Circle). English grid: insert.NAME_GRID. Under field state 0xB the D-pad also walks
  Wataru with no collision, so ~8 Downs walk him off the map: map-exit check EXE 0x800434E8 (y u16 0x8009C892 >=
  0x700, no exit) shows EXE 77808 "No going back!" (scene no_way_back; a field page, missed by extract until s22).
- **IQ battle steps** (p8 s20): each IQ game is a field actor (0x800BD750 + 0x6C * n; practice 15-puzzle at n 16,
  0x800BDE10) whose action u16 +0 picks an ST handler from EXE table 0x8006E840: 0x103 = KIO / 15-puzzle (ST
  0x800EEE84), 0x112 = hit & blow (0x800FA2D4), 0x120 = 0x800FF958 game. Top state u16 +2 indexes the game's step
  table (0x103: 0x8010AEB8; 0x112: 0x8010B884; 0x120: 0x8010C954); some top states run a sub-step at another field
  through their own table (0x103 top 3 -> +0x56 table 0x8010AF34: host talk, 4/6/8 opponent taunts, 16/18/20 lose
  lines, 27 "Start all over again?", 29 "any time!", 47 "weren't listening?!"; top 19 -> +0x5A table 0x8010B180:
  2/4/6 win lines; 0x112 top 5 -> +0x56 0x8010B910, top 6 -> 0x8010B940; 0x120 top 5 -> +0x68 0x8010CA90). The ST
  message functions copy their JP-sized string to the stack, so readlog sees them even when the box isn't drawn.
  `tools/lua/iqstep.lua` logs the steps and jumps one (`TOP`/`ATF`, `SETTOP`, `FIELD`, `TO`); runs in work/qa/iqs/.
  The ep-2 story KIO game doesn't run as one of these actors (only 0x11E/0x11F appear, at its card).
- Abilities (p8 s18): FDS 0x80101740(char) uploads the glyphs of u16[10] at **0x800A96D0 + 20 * char** (ability ids,
  name = 0x8009703C + 14 * id, exe_abilities) when Status opens a page; scene abil_all pokes ids 1-26.
- Use menu tabs (p8 s18): 4 tabs Heal / Attack / Support / Other = inventories 0x800A3510 / 3530 / 3548 / 3568; the
  list reads only its first 8 rows under --debugger (items_c + items_d cover Other ids 1-8 / 9-15).
- Key items list is 2 columns: even items are in the right column (scene keys_b presses right first).
- File table 0x80077240: 1,037 records of 0x20 bytes {name ptr, load address, LBA (filled at boot), size, ...};
  loader 0x8002505C(index). `tools/filetab.py` lists it.

## Dialogue viewer (p8 s10, for text coverage)

- From free walk (work/states/field.sstate, ep 1), writing u32 0x8009C998 = a message record's start and field
  state u16 0x8009C788 = 3 plays that message as an event: state goes 4 (window), the pointer walks the text a word
  per frame, Circle pages on, and the event ends at the record's end (`tools/lua/textview.lua`, PTR defaults to the
  bank start u32 0x8009C9A4: R01 bank 0x800DC96A played Wataru's "A village!" then "So..." and ended at f329).
  **Correction (p8 s11):** state 3 ignores 0x8009C998: EXE 0x8003275C copies the event start u32 0x8009C9A4 into
  it, then 0x80032810 parses a **7-word header** (w1 music/sound id or FFFF -> 0x800282F0, w2/w3 actor + arg bytes,
  w4 face (0x7FFF none; high nibble << 6 = portrait), w5-w7 portrait cmd 0x0100 + args, or 0x7FFF) and walks the
  text. So the viewer writes both pointers = page - 14. The s10 "plays its record" result only ever replayed the bank
  start. An event started on the frame its predecessor ended returns at once: wait ~40 frames of state 0. State 5 =
  a post-text command (actor walk) running; an event can sit in it 240+ frames, or forever with absent actors.
  `A000 n FFFF` <text> pages have text before them, not a header: starting there passed a text code as music id and
  hung the emulator (textview header() check). NPC talk / pages after a stall: start any good event (HOST) and, once
  it is in state 4 inside its text, point 0x8009C998 at the page: the walker draws it to its 0x3000.
  `tools/textcover_run.py` runs this per episode in chunks of 30 pages (one hang costs a chunk), resumable; log =
  textlog.lua's TEXT lines, key = episode << 24 | EN address (build/wataru_en.strings.tsv col 2; col 3 = header kind).

## Scene list (tools/debug/scenes.txt) and its proof

Title (menu, Continue -> card screen, Config), ep00-ep14 (area map + title card + opening dialogue of every
episode), field, field menu and its five submenus, shop, save, battle (ball / mashin / IQ), battle won, battle
lost, level-up, ending (FMV + staff roll), credits (mode 0x16); phase 5 added battle_menu/battle_item, mashin
attack/hit/lose/win, iq_page2, menu_key, monpet_detail. `warp_all.py` writes `work/qa/warp/<scene>/`
(final.png, sheet) and `work/states/<scene>.sstate`; summary.tsv has the arrival frame and the overlay check.

## Open (grow the list when a bug report names a place it can't reach)

- Mid-episode scenes (events by id: 0x80032144(id) / 0x8009C7B0), other shops (shop id 0x8009C900 / 0x8009C90A
  read by the shop setup; guess), battle enemy and IQ-puzzle selection, mashin battles per stage (0x8009C618),
  and modes 12/13/15.

## Shop messages (p8 s21)

- Item-shop actor 0x800C0DBC (action 0x228, +2 = 5 item shop; other values = monpet shop), step u16 +0x54 (handler
  FDS 0x80104028: step 0 runs the confirm builder once, nonzero result -> step 1, else 2). Builders: item shop FDS
  0x80106ABC, monpet shop 0x80107004. Message index: 1 when the cart total (sum of u32 0x800B3828[8]) > money u32
  0x8009C8B4 -> EXE 77BC0 "Not enough money!!"; 2 (item shop only) when a cart row (6 bytes at 0x800A9148: qty, type
  0-5, id) plus the held count (inventories 0x800A3510/3530/3548.., u16 id << 8 | count) reaches 100 -> 77BE0 carry
  limit; 0 -> 77BA0 "Is this OK?". The monpet builder never sets 2, so 77C00 "You already have it." is dead (waived).
  Scenes shop_nomoney / shop_carry poke the cart and money, then step 0.
- Leaving with an unpaid cart: EXE 0x8004A060 (talk/exit check) loops the 8 cart rows and calls 0x8004A844, which
  starts the 77C20 page (u32 0x8009C998 = 0x8008F420, actor 15 +2 = 0xD, actor 11 action 0x20C): "Customer! Just a
  moment." + choice "1. Go back / 2. Leave". Scene shop_leave replays those writes from free walk.
- Item order: FDS 0x800FBF58(a0) draws the title box, a0 = 0 "Please choose the item order." (124F0), 1 "Confirm"
  (12510) after the third pick (the fourth fills itself). Scene item_order2.
