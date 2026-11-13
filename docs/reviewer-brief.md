# Translation reviewer brief - Chou Mashin Eiyuuden Wataru: Another Step

You review one batch of a JP->English fan translation. Read-only: no edits, no git, no subagents.
Mechanical validity (ids, the [B000] control code, ASCII, 32-letter lines, 3-line boxes, speaker lines, cursor
indents, glossary spellings) is already enforced by `tools/batches.py check` - judge translation quality.
Return the report as your final message; the controller saves it (`tools/tl_codex.py review` sends everything below
in one prompt).

## Inputs
- Pairs file: every entry of the batch as `>> id | speaker | JP` / `EN` in story order (`\n` = line break).
  Read ALL of it.
- `glossary.md` (rulings at the top), `docs/style-reference.md` (voices), `docs/synopsis.md` (reveals).

## Judge
- Accuracy: mistranslation, omission, addition, wrong speaker or addressee, reversed meaning. Quote the JP and say
  what it means.
- Consistency: glossary names/terms exactly; honorifics (くん/さん/さま kept as -kun/-san/-sama) stable; voice
  matches the style reference.
- Things players caught that reviewers missed: jokes/wordplay losing their punch (this game is a comedy: every
  village's obsession, every punny item or attack name must stay funny); abbreviated names or terms; stock phrases
  that read awkwardly ("... GET!"); a reveal given away early (Warurine is Warumonder's daughter).
- Voice: Obaba's じゃ/のぉ crone talk, Sakuya's refined ですわ/おほほ, Aragoto's pompous ではないか, Wataru's breezy
  kid talk, old men's じゃ/わし, rough ぜ/ねぇ, feminine かしら/わよ/のね, dialects. Register flattened into
  neutral prose is Important, not Minor.
- Naturalness: would a fan-translation reader stumble?
- Not your job: line length and line breaks (checked by tool), unless a break splits a word or a name.

## Report
### Issues
#### Critical (meaning reversed, wrong speaker)
#### Important (clear mistranslation, glossary inconsistency, abbreviation, a voice flattened, joke dead)
#### Minor (style - deferred to one polish pass)
Each: `id - JP gist - problem - suggested EN` (suggested EN must respect 32 letters per line, `\n` for breaks).
### Assessment
Approved | Needs fixes - one sentence why.
