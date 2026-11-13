# Translator brief - Chou Mashin Eiyuuden Wataru: Another Step (PS1, 1998)

You translate part of the Japanese script of Chou Mashin Eiyuuden Wataru: Another Step into English for a fan
patch. A kids' comedy RPG from the Wataru anime: 10-year-old Wataru Homurabe is summoned to Sokaizan to beat the
demon Warumonder, who forces one single value on each village; every village's obsession is a running gag.

`tools/tl_codex.py` sends this brief, the glossary rulings, the style reference, the synopsis, the batch's terms
and the batch itself in one prompt (codex has no file access here). An agent with file access reads them instead:
`docs/style-reference.md`, `build/terms_<batch>.txt`, `docs/synopsis.md`, `work/tl/<batch>.tsv`.

## Input
`id<TAB>speaker<TAB>form<TAB>limit<TAB>Japanese`.
- form: dlg (dialogue box), choice (a box with cursor lines), menu, name (a fixed field: item, enemy, place, skill).
- limit `WxN`: at most W letters per line and N lines. This is a HARD limit (the game has no wrap and no VWF; every
  16x16 cell holds two letters). Spaces and punctuation count as letters.
- `\n` in the Japanese is a line break. The speaker column is a hint for pages without a speaker line.
- Lines are in story order; a page without a speaker line continues the previous page's speaker.

## Output
`id<TAB>English`, every input id exactly once, same order, nothing else. Plain ASCII (straight quotes, `...`).
Write line breaks as the two characters `\n`. Never a real tab inside the English.

## Rules the check enforces (`python -X utf8 tools/batches.py check <batch>`)
- Each line <= W letters, at most N lines. Break lines yourself at natural points; use all 3 lines of a box when
  needed. Never cut meaning to fit: re-break first, then rephrase tighter.
- A page whose Japanese starts with `Name：\n` starts with the speaker line `Name:` exactly as in the terms list
  (`speaker` rows), then the text on lines 2-3. For speakers not listed, translate the label and end it with `:`.
- Choice boxes: same number of lines as the JP; a line that starts with N blank cells (`　`) starts with 2N spaces.
- `[B000]` is a control code: copy it once per occurrence, in the same place (start or end of its line).
- Glossary: a JP term in the line needs its English form; never use an Avoid spelling.
- Honorifics after a name or title stay: くん -kun, さん -san, さま/様 -sama, ちゃん -chan (Wataru-kun, Savior-sama).
  Generic おじさん/おねえさん are not honorifics ("mister", "miss", or just drop them). Nor are お嫁さん, お嬢さん, お姉ちゃん,
  お父さま, 村長さん, お客さん, ゴクローさん: "bride", "young lady", "big sis", "father", "chief", never "bride-san"
  (the check flags a lowercase word + honorific). Sakuya's おじさま to Aragoto = "(my dear) sir", never "Uncle".

## Style
- Faithful: keep the information and order of ideas; adapt idiom, not meaning. Don't add or skip.
- Every pun, gag and parody must land in English (invent an English pun when the JP one can't survive; no notes).
  Item and skill names are punny katakana coinages (ウレピアス = ureshii + piercing): make a punny English name in
  the limit, not a romanisation, unless it is a person or place name.
- Voices are in the style reference: Obaba's crone talk, Sakuya's refined princess speech, Aragoto's pompous
  samurai bluster, Wataru's breezy kid talk. A line any character could have said is a mistake.
- Punctuation: 「」 -> "...", 『』 -> '...', 【】 -> nothing, ・・・ -> ..., ！？ -> ?!, ！！ -> !!. US spelling.
- SFX: English onomatopoeia, no asterisks.
- Names in Western order; joke names joined with ・ keep their order.

## Notes from earlier batches
- (none yet)

## Report
Agents with file access reply with: entry count, then `NEW TERM: jp -> en`, `UNSURE: id - note` lines.
