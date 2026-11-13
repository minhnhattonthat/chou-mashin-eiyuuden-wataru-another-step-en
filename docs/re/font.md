# Text renderer and the English font (phase 5 engine spike)

## How 16x16 text reaches the screen (verified 2026-11-14, ep01 dialogue)

- Fonts live in RAM as one array: MSG_CG.BIN at 0x80110000, the room font (M16_Rxx) right after it at 0x80122500.
  Glyph source = **0x80115300 + code * 128** (0x5300 = 0xA6 * 128), so codes 0x1A4+ land in the room font.
- Room dialogue per-char step: EXE 0x80053560-0x80053700 (unoptimised, `$fp` frame). Control words first (0xB000 n,
  0xF000 ..), then `src = 0x80115300 + code<<7` (0x8005364C) and `jal 0x800704B8(src, mode 0, 0, x, y, w 16, h 16)`
  with x/y = u16 0x8009C7B2 / 0x8009C7B4 (VRAM halfwords / lines); then x += 4 (0x800536E0). Text pointer u32
  0x8009C998.
- 0x800704B8 = LoadImage(rect{x, y, w/4, h}, src) + GetTPage: each glyph is DMA'd (128 B) into an off-screen 4bpp
  window buffer in VRAM (x 768+, y 256+ in the ep01 dump: `tools/vram.py`), which the box then draws. 0x80113B00
  (6,144 B, glyphs below code 0) is uploaded when a box opens (frame / clear, guess). The font RAM is never written
  while text runs (`tools/lua/readpcs.lua MODE=Write`).
- The same `lui 0x8011 / ori 0x5300` glyph formula appears at 124 sites: EXE 2, ST 24, BALLBAT 26, MACHINE 4, TTL 24,
  LVUP 9, FDS 35. Each has its own width/advance code, so any change to the cell width is ~124 patches.
- BALLBAT item names use the separate 8x16 battle font (`jtext.battle_table`): its cells are already 8 px wide.

## Decision: pre-rendered digraph cells, no renderer change (D8)

- Every 16x16 cell holds **two 8x16 letters** (`tools/digraph.py`: Spleen 8x16, BSD-2-Clause, body colour 1, shadow
  E one pixel right and down; T and * lose their 8th column). One 16-bit code = two characters, so all 124 render
  sites, every box and every fixed-width table keep their cell counts and gain double the characters: an 8-cell EXE
  name field holds 16 letters, a 16-cell line 32.
- The build assigns codes to the letter pairs a text actually uses, per font context, exactly as the Japanese game
  allocates kanji: common pairs into MSG_CG's slots (codes 0x01-0x1A3 except digits/icons the code prints), room-only
  pairs into that room's M16 font (codes 0x1A4+, up to ~190; FDS / menu text drawn in a room borrows them, like the
  key-item descriptions do now). A string whose pairs don't fit falls back to single-letter cells ("a" + blank).
- Spike: ep01 page R01:0E7CA in place (`tools/insert.py`), cells over MSG_CG kanji slots 0xE6+: renders clean and
  legible in game (work/qa/p5/spike3/f000100.png): 29 + 27 chars on a JP 15/14-cell page.
- Known costs, for later phases: numbers the code prints (digit codes 0xB4-0xBD) stay one digit per 16-px cell unless
  their printers are patched; runtime-joined pieces (names + `を手に入れた！`) of odd length leave a half-cell gap: give
  the encoder a pad or keep joined pieces even; the 8x16 battle font and CNF_MSG (config screen, its own file at
  0x80110000) need their own Latin glyphs.
- Rejected: half-width by patching width and advance at all 124 sites (more code, fixed tables still overflow); a
  runtime-composing hook in 0x800704B8 (LoadImage is queued, so composed cells need a ring buffer in resident RAM,
  and there is little: EXE zero run 0x8009882C-0x80098C3F (1 KB) saw no writes in field/battle/menu states, 0x80099184+
  is live); a true VWF (per-glyph LoadImage at 4-px granularity, would need a RAM line compositor).
