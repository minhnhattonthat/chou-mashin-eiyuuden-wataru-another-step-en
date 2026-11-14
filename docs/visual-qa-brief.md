# Visual-QA reviewer brief - Chou Mashin Eiyuuden Wataru: Another Step (PS1)

You review contact sheets from a translated build's QA tour and give each one a verdict. Read-only on everything
except your one verdict file: no edits to the repo, no git, no subagents.

## Inputs (in your dispatch)
- A chunk file: one `id<TAB>path` line per sheet. Read every sheet in it; none may be skipped.
- Your verdict file: `work/qa/verdicts/<chunk>.tsv`.
- Optional: the original ROM's sheets (`work/qa/tour_jp/`, same ids) and `glossary.md`.

## How to look
- Read each sheet whole first. Where text is small, zoom into it with
  `python -X utf8 $SKILL/scripts/sheet.py SHEET.png --crop x,y,w,h --zoom 3 --out <scratch>.png` and read that.
- When something looks wrong, open the same id from `tour_jp/` (`sheet.py EN.png --compare JP.png`). If the
  original shows the same thing, it is the game's own behaviour: `ok`, with a note.
- Zoom into every Yes/No prompt, selection box, menu row and speech bubble: a few pixels of misalignment don't show
  at sheet scale. To measure one: `python -X utf8 $SKILL/scripts/inkbox.py SHOT.png x,y,w,h`.

## Judge
An `issue` is any of:
- Japanese still visible;
- text overflowing a box, clipped by a frame, or running off screen;
- text off-centre where the original centres it: an option in its selection box or cursor brackets, a label, a bubble;
- garbage tiles, wrong or missing glyphs, a strike or stray pixels across letters;
- broken line breaks: a word split mid-line, a page ending mid-sentence, a one-word last line;
- an empty box where text belongs;
- a name that differs from `glossary.md`.

Standing non-bugs, `ok` (the controller adds the game's own below):
- text still typing out, a box mid-fade or mid-scroll, a cursor caught mid-blink;
- a map or scene still loading after a warp;
- anything identical in the original's sheet.
- English is drawn two letters per 16x16 cell (D8/D18): letters sit in fixed cell pairs, so a half-cell gap
  between words or before a number is by design, as are numbers drawn one digit per 16-px cell.
- Kept Japanese/stylised art by ruling: the title logo 超魔神英雄伝ワタル ANOTHER STEP, logos in eyecatch and
  puzzle images, signs and lettering in 3D room scenery and battle backgrounds (G21/G22: not yet ruled, flag only
  if a large, legible sign).
- Dialogue types out a letter pair at a time: a box that is empty, holds only a speaker name, or ends mid-word is
  still typing. Judge line breaks and one-word last lines only on a page that is complete (the ▼ page arrow at the
  box's bottom right is shown).
- Monpet element shows a drop / bolt / flame icon instead of 水/雷/火 (D23).
- Short forms by ruling: "Sp. Attack", "Sp. Defense", "Ep." (D20), and the cut names in D19 (Steel Jane, Jar
  Sanpun, Mo Ippun, Veggiepurr, Maiko Jodan, Holy Wyrminferno).
- Mashin special-move banners flash one English word per kanji cell (TO / RYU / KEN, PHAN / TOM / WYRM / WAVE): D22.
- A black or fading frame at a warp's start, an FMV frame, a loading screen, the BANPRESTO / SUNRISE company
  logos and "PUSH START" are not text issues.

## Verdicts
Write your verdict file once you have read every sheet, one line per id in the chunk:
`id<TAB>ok|issue<TAB>what and where` (for an issue: which tile, which text, what is wrong).
Then return a short summary: counts, and the issues one per line.
