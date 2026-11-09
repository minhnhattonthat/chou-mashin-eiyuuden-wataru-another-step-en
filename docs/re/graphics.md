# Graphics text survey

Tour so far: cold boot to the first room dialogue (work/qa/r1, r2, r3). Static sweep of CHG files not done yet (formats in
`files.md`). Rows are tile- or image-drawn Japanese; "?" = source not yet found.

| # | Screen | Element | Seen in | Source guess |
|---|---|---|---|---|
| G1 | Title | logo 超魔神英雄伝ワタル ANOTHER STEP | r2 f60 | OUT/TTL.CHG (keep logo unless an official English logo exists, D5) |
| G2 | Title | PUSH START (already English) | r1 | OUT/TTL.CHG |
| G3 | Title | copyright line サンライズ・R・テレビ東京・ASATSU / BANPRESTO 1998 | r1 | OUT/TTL.CHG |
| G4 | Title menu | ニューゲーム / コンティニュー / コンフィグ | r2 f180 | OUT/TTL.CHG or PRG/TTL.BIN sprites |
| G5 | Prologue | location banner 創界山のふもと | r3 f3150 | ? (PRG/MEM_*.CHG or OUT/CATCH*) |
| G6 | Prologue | caption えっ!? ボクは救世主？ over a still | r3 f3450 | OUT/CATCH*.CHG |
| G7 | FMV | WATA01-04.STR, OUT/*.STR: any burnt-in text | r3 | check each video; subtitles if voiced |
| G8 | Dialogue box | window frame, page arrow (no text) | r3 | - |

To do (phase 1 remainder): decode CHG types 0xC0000023 / 0xC0000322 and the YM raw images into sheets, sweep all of them
for Japanese, then tour menus, shop, status, battle (normal / mashin / IQ battle), game over, save screen, ending and
credits with the debug tool (phase 2) and add rows.
