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
| G3 | Title | copyright サンライズ・R・テレビ東京・ASATSU / BANPRESTO 1998 | OUT/TTL.CHG blk 12 | **done** (p8): line 1 re-set "SUNRISE·RED·TV TOKYO·ASATSU" (palette 1); BANPRESTO 1998 kept |
| G4 | Title menu | ニューゲーム / コンティニュー / コンフィグ | OUT/TTL.CHG blk 12 (4bpp, palette 4) | **done** (p8): New Game / Continue / Config; the kana shared ニュー, so TTL.BIN records 0x4FA2/0x4FB0 get own 80-px rects |
| G5 | Prologue / area cards | 創界山のふもと, chapter numerals 一二三四五六七, 0-9, area/menu words (コンビニ, エキストラ, タウン, キャラクター, データ, モンスター, エンディング, ...) | OUT/SBTCHAR.CHG (768,0) 64x256, 4bpp | redraw; find the layout table (SBTTL.BIN?) |
| G6 | Episode title cards | えっ!? ボクは救世主？ etc.: big caption **glyph atlas** (あいうえおか..., 救世主, 弁当, 創界山, 最強, 演歌, 龍神丸, 天翔, 決戦...) | OUT/SUBTTL.CHG 3 blocks, 4bpp | glyph-composed from **sprite lists in PRG/SBTTL.BIN** (base 0x800D0000, 0x3B70-~0x4F60, verified static): 14-byte records `000C, tpage/clut 7DC4/7DC5, u8 u,v, u16 w,h, s16 x,y`, list ends 0xFFFF; animation scripts at 0x4F68+ (`5, ptr`) and pointer tables at 0x761C+ pick them. English: redraw caption strips into the atlas and rewrite the rects |
| G7 | FMV | WATA01-04.STR, OUT/P_SR_00/P_ST_00.STR: any burnt-in text | ? | check each video in the tour |
| G8 | Dialogue box | window frame, page arrow (no text) | - | none |
| G9 | Memory card screen | all save/load messages (セーブ中です, メモリーカードを..., ファイル1-4, はい/いいえ, NODATA, 第 話 最終 プロローグ), save-slot place names (もんじゃ村, コンビニ村, カンボづくし村, ...), party names (炎部ワタル, 剣部アラゴト, 忍部サクヤ, ...), 0-9 digits | PRG/MEM_01.CHG (640,0) 320x256, 4bpp | redraw (largest group) |
| G10 | Prologue scroll | story intro text 「…ワルモンダーの操る魔神の『ワルワル・キュウキョーン』に、…」 as 3 images | FM16/R15_MES.BIN (one upload, 4bpp) | redraw as English paragraphs |
| G11 | Shop | ｶﾞﾝﾎﾞ (currency) 個 合計 (count / total) | FM16/FD_SHP.PX (768,0) 64x256, CLUT (208,481) from the field code | **done** (p8, verified in scene shop): Ganbo / pcs / Total; FDS.BIN records 0x171C6 / 0x171D4 re-cut |
| G12 | IQ battle (hit & blow) | あたり / おしい / あと 回, まけ! / かちっ! | IQ/HIT_MAIN.CHG blk 5, IQ/KIO_MAIN.CHG (まけ/かち) | **drawn** (p8, not yet seen in game): Hit / Blow / Tries [digit], LOSE! / WIN + ! (ST.BIN records 0x3B3FC, 0x3ACAC-0x3ACD8 unchanged) |
| G13 | IQ battle cards | BATTLE (English) | IQ/BUR_MAIN.CHG | none |
| G14 | Eyecatch | logo on CATCH05 | OUT/CATCH05.CHG | keep (logo) |
| G15 | Puzzle images | logo on PUZ_PG05 | IQ/PUZ_PG05.CHG | keep (logo) |
| G16 | Battle command menu | たたかう / 必殺技 / アイテム / にげる / さくせん + party names (ワタル, アラゴト, サクヤ?, ...) | YM/BR_17/OTHER01-06.CHG (6 copies) | **done** (p8): Fight / Special / Item / Run / Tactics, Wataru / Aragoto / Sakuya / Warurine (Spleen 6x12 + outline; CLUT (208,497) = file header 0x9A0; BALLBAT records 0x23EE4, 0x23F00.., 0x250FC.. widened to 48) |
| G17 | Battle speech bubbles | ゴメンネ, バ〜ン | YM/BR_17/OTHER11.CHG | **drawn** (p8, not yet seen in game): Sorry♥ / Bam! |
| G18 | Enemy sprite bubble | 圏外 (with furigana) | YM/BR_01/ENE09.CHG | **drawn** (p8, not yet seen in game): No / Signal |
| G19 | Mashin battle status | mashin names per matchup (龍神丸 / 天翔龍神丸 vs レンジ・チ・チン, いらっしゃい魔神, SFXザウルス, ドウガツクエーン, ライトサーチ, ラクライガー, エレクトロン, イリュージョン, アムラーX・55, ゴールドメダラー, シェイプU2, ジューンブライガー, LLラバーズ, QTコアラッコ, 聖ラブリーフォー, ワルワル・キョジョーン...), labels 攻撃 / 回復 / 気合い / 必殺技 | YM/MR_02/STS_01-18.CHG | **done** (p8, verified ep1 VS card + menu): labels Fight / Heal / Spirit / Special (攻撃/回復 cells stay 32 px: u56+ is the gauge-pip strip 0x173E2 and MP; "Attack" can't fit), VS names per file (gfx_gen STS_NAMES); tpage 0x0E is overwritten by MBEXT_05-07 (832,0) and the menu strips later, so the names show only on the VS card |
| G20 | Mashin attack-name banners | 登龍剣, 幻影招, 天翔, 龍破, 昇龍烈, 火爆裂, 聖剣 | YM/MR_05/MBEXT_08.CHG | redraw. Every kanji is its own 40x40 cell, CLUT (112,510); MACHINE.BIN 0x10D38-0x10F14 = one record per kanji (single-glyph frames), 0x10F30.. = 幻影招龍破 in a row (x -98..61, 40-px pitch), 0x10F84.. = 昇龍烈火爆裂聖剣 in two columns of 4 (y -100..20). Look at the animation in game before choosing per-cell syllables (TO/RYU/KEN, SKY/SOAR) vs a re-cut strip |
| G22 | Town / room scenery | shop signs in the 3D room atlases: 酒 bottle/lantern label + a dark diagonal kanji sign repeated in most rooms (R00-R14 M0), katakana sign …コロン (R02M1), large stylised shop logos (R08M0), plaques and tokens (R08M1), kanji shop signs (R09M0, R10M0/M1, R13M4); ~40 more "maybe" boards/posters/labels | FR0x/RxxMy.BIN (8bpp, CLUT elsewhere) | decide per sign after a coloured look in the field tour: legible ones redraw, illegible few-pixel signs may stay (log each as a waiver). Full list: `gfx-review-fr.md` |
| G23 | Field menu / status screen | 炎部ワタル 剣部アラゴト 忍部サクヤ, ワルリーダ, 回復 攻撃 補助 経験値 他, アイテム そうび もんペット ステータス コンフィグ, 気合 装備 属性 超必殺技 こうか, 第 話 最終, small kana/kanji row set, ランク/レベル, Lv Hp Mp Ep (Latin) | FM16/FD_STS.BIN blk 0 (768,0) 64x256 4bpp (tpage 0x0C) + CLUT (0,498) (portrait only). The tail after 0x8210 is compressed portraits (not text). The atlas is a **glyph sheet**: digits v0-8; 8x16 small kana rows v8/24/40/56/72/88 (15 cells from u0: あ-そ, た-ほ, ま..ろ, わをん+small, が-ど, ば-ぽ), ランクタイプレベル/AtRank v104, icons v120, digits v136, 16x16 words v152-248 (炎部ワタル u0 v168 80 wide, 剣部アラゴト, 忍部サクヤ, ワルリーヌ, 回復攻撃・補助経験値の, 他アイテムそうびもんペット, ステータスコンフィグ気合装備属性, つかせいりペン超必殺技こたカ) | **done** (p8 s4; verified in scenes menu, menu_item, menu_use, menu_equip, menu_status, monpet_detail): `gfx.FM_LABELS` (JP spelling asserted per label) -> one Spleen strip per English word in the freed glyph rows (`gfx.FM_FREE`, `fm_layout`), leftmost record cuts it, the others w = h = 0 (draws nothing in PCSX-Redux); colons moved after the word; spacer records (32,56) blanked; `fm_check` = no other record cuts a freed row (shop records 0x16E00-0x17700 cut FD_SHP). Drawn, not yet seen: item tab buttons 回復/攻撃/攻撃補助/その他, 必殺技/超必殺技 (0x14D30/0x14D4C, screen unknown), 最終話, こうたい, 終了 (0x179CA), Warurine panels. Monpet element value 水/雷/火 is MSG_CG glyphs 0xB0-0xB2 drawn by code: still JP. RE notes: every label is static sprite records `[u16 tpage 0x0C, u16 clut 0x784D/0x784C (208/192,481), u8 u,v, u16 w,h, s16 x,y]` in FPRG/FDS.BIN 0x12530.. (1231 records; e.g. 0x12568 炎部ワタル 80x16; stat names ちから.. one 8x16 record per kana, e.g. 0x14C18 ち, 0x14C0A か near 0x14986-0x14C20), drawn by the EXE record renderer 0x8002392C (pc 0x800244D0 reads x/y/w/h/u/v from the record in s3). Plan: list the records per screen (cluster by address, map cells -> kana), draw English word strips into the kana area (free once every kana record is re-pointed: confirm nothing dynamic draws small kana), point each word's first record at its strip (w = width) and blank the rest (w 0 or a blank cell). `tools/prims.py RAM CLUT_Y` lists the GPU sprite packets of a vdump RAM (FR must be < the warp's DONE frame: emu quits there) |
| G24 | Config screen text | config messages drawn with their own font OUT/CNF_MSG.BIN (771 16x16 glyphs, kana at MSG_CG cells) | font, not images: text.md "Fonts other than MSG_CG" | replace font with the main English font |
| G21 | (maybe) battle backgrounds | possible sign lettering: BR_07/BM_17_0-2, MR_05/MBBG_09, MBBG_12 (unreadable in grey) | YM | check in battle tour |

Not displayed (guess, confirm in battle tour): katakana dev labels beside enemy frames in YM/BR_01/ENE03/04/06/09/10/12
(タイキ, ヤラレ, ハイボク, キンキョリ, ...). Latin only: ENE01 OUCH!, BM_24 banners, STS MP/VS/BATTLESTAR.

No Japanese in: CATCH01-08 (except logo), CNF.CHG backgrounds, LVUP.CHG portraits, MARUPXL (round area maps,
rendered as wrong-depth 4bpp; recheck colour in tour), NIJI, SBTTLBG, IQ enemy sprites, FP HUD.

YM/ battle graphics (971 blocks, 23 packed pages) and FR room atlases (94 blocks, 8 pages) reviewed by `codex exec`
read-only: G16-G22; full tables `gfx-review-ym.md` / `gfx-review-fr.md` with the page maps `gfx-review-*.tsv`
(page, x, y, w, h, file). Regenerate pages: `chg.py --render` (FR with `--grey8`) then `pack.py`.

Still to do in tours (phase 2/8): menus, status, battle (normal / mashin / IQ), game over, ending, credits (STAFF.BIN is
not 16-bit text: credits are probably graphics or a format still unknown), every FK still, every FMV.
