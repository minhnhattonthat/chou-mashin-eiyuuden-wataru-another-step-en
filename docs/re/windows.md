# Window budgets (phase 5 width gate)

Every 16x16 cell holds two letters (D8), so a budget is cells x 2 letters. "measured" = read off a marker or stress
shot (path given); "guess" = JP slot size only, measure before translators rely on it.

| Variant | Source | Budget | Status |
|---|---|---|---|
| Dialogue box (room pages, EXE save lady / shop / inn / system messages) | rooms/*.json, EXE.json pages | 16 cells = **32 letters per line, 3 lines** (speaker line counts as one); cell 17 is not drawn; 4+ lines write outside the 3-line VRAM window buffer and garble every later page (hard cap); the ▼ prompt sits under the frame and does not cover a full line 3 | measured 2026-11-14, `tools/stress.py`, work/qa/p5/stress/talk01 f4800-f5900 |
| Glyph torture line (all printable ASCII + double spaces) | stress R01:0E7CA / 0E820 | every glyph distinct and clean, double spaces kept | measured, same run |
| Shop list item names | exe_consumables | 8 cells = 16 letters, then the price column | measured, marker_a.png (shop) |
| Equipment names (equip screen, status 装備) | exe_equipment | 8 cells = 16 letters | measured, marker_a.png (menu_equip, menu_status) |
| Config screen labels (CNF_MSG font, left column: ボイス, Ｒ１ボタン ..) | TTL.json | label x=8, value column x=112: **6 cells = 12 letters** (a 10-cell label runs into the value) | measured 2026-11-14, `stress.py --ui`, work/qa/p5/stress_ui/title_config |
| Config screen values (ステレオ, なんでやねん ..) | TTL.json | x=112 to the screen edge: **13 cells = 26 letters** drawn (cell 14 off screen); keep 12 for a margin | measured, same run |
| Field config voice list (field menu コンフィグ) | fds_voices (FDS:18550, also TTL copy) | fixed rows: each row draws exactly **7 cells = 14 letters** (no terminator; the box fits 7) | measured, stress_ui/menu_config |
| Battle message box (BALLBAT) | BALLBAT.json (+ ENE names glued in front) | box = cells x 16 + 32 px, centred, sized to the **record's cell count** (`len_at`, insert rewrites it), not the terminator: **16 cells = 32 letters per message** incl. a glued name; an 18-cell test drew 16 and broke the frame, 22 ran off both edges | measured 2026-11-14, stress_ui (22), stress_ui3 (18) battle_ball |
| IQ battle box (ST, top of screen) | ST.json | **16 cells = 32 letters per line, 3 lines** (a 19-cell line drew 16); choice lines keep their 3 blank cells: the hand cursor sits there. Never spill ST:00140 (a jump table at 0x150 follows: the game hung) | measured 2026-11-14, stress_ui7/iq_page2 (ST:00174/001A8) |
| Mashin battle attack sub-menu (斬る / 突く) | MACHINE 0x17630 glyph list (data, not in script/) | Japanese in the marker build: drawn from the glyph lists (status Next 4) | **open** |
| Mashin battle attack names / messages | MACHINE.json, exe_mashin_attacks (10-cell slots) | not seen yet: the mashin_attack scene stops at the 斬る/突く list | **open** |
| Level-up box (LVUP) | LVUP.json | 4 lines, 15 cells; the level number prints one digit per cell into the blank cells | measured, marker_b.png (levelup) |
| Place name (field menu, bottom-right box) | fds_places | **10 cells = 20 letters**, fills the box exactly | measured, stress_ui/menu |
| Enemy name, battle header (top right) | ene/ENExx.json `kind: bname` (ENE record +4: bytes in the 8x16 battle font, NUL-terminated, char[12]) | **11 letters** (slot - 1; one letter per 8x16 cell), ends at the flame icon. The game drew the 16-bit name's cell count of letters (English: half the name): insert.CODE patches BALLBAT 0x800DF340/390/398 to stop at the NUL | measured after the patch, stress_ui4/battle_ball |
| Enemy name in messages | ene/ENExx.json `kind: ename` | slot = JP cells (7-10), count byte `len_at` rewritten; drawn in full at 7 cells, then the message text follows | measured, stress_ui/battle_ball f7800 |
| Key-item description (field menu アイテム, イベント tab) | exe_key_item_desc | **2 lines x 16 cells = 32 letters**, all drawn inside the box | measured, stress_ui/menu_key (key items poked: scenes.txt menu_key) |
| Key-item names (same screen, 2 columns) | exe_key_items | 8-cell slot; columns 10 cells apart, so the slot is the limit | measured, stress_ui/menu_key |
| Battle-font item names (8x16, battle アイテム list) | BALLBAT bfont | one letter per 8x16 cell, in place up to the JP cells (4-8 letters!); drawn count = record `len_at` (rewritten). The list was never reached: with no battle items circle on アイテム opens nothing, and the battle inventory RAM is not found (not 0x800A91F8 = key items, not read in battle; watch probes over 0x800A8E00-0x800AA000 found nothing) | **open** |
