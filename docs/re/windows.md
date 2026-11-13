# Window budgets (phase 5 width gate)

Every 16x16 cell holds two letters (D8), so a budget is cells x 2 letters. "measured" = read off a marker or stress
shot (path given); "guess" = JP slot size only, measure before translators rely on it.

| Variant | Source | Budget | Status |
|---|---|---|---|
| Dialogue box (room pages, EXE save lady / shop / inn / system messages) | rooms/*.json, EXE.json pages | 16 cells = **32 letters per line, 3 lines** (speaker line counts as one); cell 17 is not drawn; 4+ lines write outside the 3-line VRAM window buffer and garble every later page (hard cap); the ▼ prompt sits under the frame and does not cover a full line 3 | measured 2026-11-14, `tools/stress.py`, work/qa/p5/stress/talk01 f4800-f5900 |
| Glyph torture line (all printable ASCII + double spaces) | stress R01:0E7CA / 0E820 | every glyph distinct and clean, double spaces kept | measured, same run |
| Shop list item names | exe_consumables | 8 cells = 16 letters, then the price column | measured, marker_a.png (shop) |
| Equipment names (equip screen, status 装備) | exe_equipment | 8 cells = 16 letters | measured, marker_a.png (menu_equip, menu_status) |
| Config screen options (CNF_MSG font) | TTL.json | JP up to 12 cells; marker shows 14-16 letters per item cleanly | guess for the max |
| Field config list | TTL.json / EXE | 5 items, up to 7 cells shown | guess |
| Battle message box (BALLBAT) | BALLBAT.json | box sizes to the text; 14 cells (28 letters) shown clean; JP up to 16 | guess for the max |
| Level-up box (LVUP) | LVUP.json | 4 lines, 15 cells; the level number prints one digit per cell into the blank cells | measured, marker_b.png (levelup) |
| Place name (field HUD) | fds_places | 10 cells = 20 letters | guess |
| Enemy name, battle header | ? | not from ENE*.BIN (still Japanese with ENE markers in, thin font): source untraced | open |
| Enemy name in messages | ene/ENExx.json | explicit cell count in the record (`len_at`); in place up to the JP cells | guess |
| Key-item description | exe_key_item_desc | 2 lines x 16 cells | guess |
| Battle-font item names (8x16) | BALLBAT bfont | one letter per cell, JP cell count (list `[u32 cells, u32 ptr]`) | guess |
