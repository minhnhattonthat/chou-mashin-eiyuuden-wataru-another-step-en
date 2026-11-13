# Graphics text survey

## Formats (verified by rendering, `tools/chg.py`)

- Graphics files are a chain of **VRAM uploads**: `u16 x, y, w, h` (VRAM halfwords) + `w*h*2` bytes, **uncompressed**,
  optionally after typed header chunks (`0xC0000023` tile map: `u8 W,H,tw,th` + map words; `0xC0000322` sprite list:
  `u16 count, u8 W,H` + 8-byte entries `u,v | clut | tpage | ?`). `chg.py` finds the longest chain ending at EOF.
  - A CLUT is an upload with h <= 16 and w 16/256; the images after it use it (CATCH01: CLUT (0,505) 256x1 at 0x1078,
    8bpp image (896,0) 128x256 at 0x1280). Depth is not stored per block: sprite-list tpage bits or the CLUT width
    tell it, and some 256-wide CLUT rows really hold 16 4bpp palettes (SBTCHAR, TTL_12 render wrong at 8bpp).
  - SUBTTL.CHG starts with a CLUT block (0,506) 16x16 that runs past VRAM row 511 (wraps): chg.py drops it.
  - `FR*/RxxMy.BIN` (393,232 B): room object atlases, 2 uploads (384,0) 256x512 + (640,0) 128x512, 8bpp, CLUT
    elsewhere (render with `--grey8`). `FR*/RxxMy_A..` and `BR_04/BMO_*`: sprite lists only.
  - `FP*/PxxMy.BIN`: one 4bpp upload (768,256) 64x256 (HUD bars, no text) + map data.
  - `FK*/KxxIyy.BIN` (event stills, by name): 256-colour palette then pixel data that does not line up at any
    stride: **compressed (guess)**. Not decoded; check every story still in the phase-2/8 tours with a VRAM dump.
  - `YM/*/SND*`, `MEM_02.CHG`, `MINI_01`, `MBEVH_*`: VAB/SEQ sound ("pBAV", "pQES"); `MBPRG_*`: battle code overlays.
- Sweep renders: `work/gfx/sweep/<dir>/` + `index.tsv` (file, offset, VRAM rect, depth); sheets in
  `work/gfx/sweep/sheets/` (`tools/pack.py` for mixed sizes).

## Rows (tile- or image-drawn Japanese)

| # | Screen | Element | Source (verified by render unless "?") | Plan |
|---|---|---|---|---|
| G1 | Title | logo 超魔神英雄伝ワタル ANOTHER STEP | OUT/TTL.CHG blk 12 (640,256) + logo parts | keep (D5) unless an official English logo exists |
| G2 | Title | PUSH START (English) | OUT/TTL.CHG blk 12 | none |
| G3 | Title | copyright サンライズ・R・テレビ東京・ASATSU / BANPRESTO 1998 | OUT/TTL.CHG blk 12 | redraw in Latin (names) |
| G4 | Title menu | ニューゲーム / コンティニュー / コンフィグ | OUT/TTL.CHG blk 12 (4bpp) | redraw |
| G5 | Prologue / area cards | 創界山のふもと, chapter numerals 一二三四五六七, 0-9, area/menu words (コンビニ, エキストラ, タウン, キャラクター, データ, モンスター, エンディング, ...) | OUT/SBTCHAR.CHG (768,0) 64x256, 4bpp | redraw; find the layout table (SBTTL.BIN?) |
| G6 | Episode title cards | えっ!? ボクは救世主？ etc.: big caption **glyph atlas** (あいうえおか..., 救世主, 弁当, 創界山, 最強, 演歌, 龍神丸, 天翔, 決戦...) | OUT/SUBTTL.CHG 3 blocks, 4bpp | glyph-composed: strings of atlas indices, probably in PRG/SBTTL.BIN (guess); English needs a Latin atlas + re-encoded strings, or whole-title strips |
| G7 | FMV | WATA01-04.STR, OUT/P_SR_00/P_ST_00.STR: any burnt-in text | ? | check each video in the tour |
| G8 | Dialogue box | window frame, page arrow (no text) | - | none |
| G9 | Memory card screen | all save/load messages (セーブ中です, メモリーカードを..., ファイル1-4, はい/いいえ, NODATA, 第 話 最終 プロローグ), save-slot place names (もんじゃ村, コンビニ村, カンボづくし村, ...), party names (炎部ワタル, 剣部アラゴト, 忍部サクヤ, ...), 0-9 digits | PRG/MEM_01.CHG (640,0) 320x256, 4bpp | redraw (largest group) |
| G10 | Prologue scroll | story intro text 「…ワルモンダーの操る魔神の『ワルワル・キュウキョーン』に、…」 as 3 images | FM16/R15_MES.BIN (one upload, 4bpp) | redraw as English paragraphs |
| G11 | Shop | 個 合計 (count / total) | FM16/FD_SHP.PX (768,0) 64x256 | redraw |
| G12 | IQ battle (hit & blow) | あたり / おしい / あと 回, まけ! / かちっ! | IQ/HIT_MAIN.CHG blk 5, IQ/KIO_MAIN.CHG (まけ/かち) | redraw |
| G13 | IQ battle cards | BATTLE (English) | IQ/BUR_MAIN.CHG | none |
| G14 | Eyecatch | logo on CATCH05 | OUT/CATCH05.CHG | keep (logo) |
| G15 | Puzzle images | logo on PUZ_PG05 | IQ/PUZ_PG05.CHG | keep (logo) |

No Japanese in: CATCH01-08 (except logo), CNF.CHG backgrounds, LVUP.CHG portraits, MARUPXL (round area maps,
rendered as wrong-depth 4bpp; recheck colour in tour), NIJI, SBTTLBG, IQ enemy sprites, FP HUD.

Pending (codex review in progress, merge here): YM/ battle graphics (971 blocks, `work/gfx/sweep/ym_review.md`),
FR room atlases (94 blocks, `work/gfx/sweep/fr_review.md`; atlases show Latin signs SHOP, 24, NO SOY? already).

Still to do in tours (phase 2/8): menus, status, battle (normal / mashin / IQ), game over, ending, credits (STAFF.BIN is
not 16-bit text: credits are probably graphics or a format still unknown), every FK still, every FMV.
