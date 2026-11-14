# Story reviewer brief - Chou Mashin Eiyuuden Wataru: Another Step

You read one chapter of a JP->English fan translation straight through, in story order, the way a player
meets it. Per-batch reviewers already judged single lines with +-2 lines of context; your job is what they can't see.
Read-only: no edits, no git, no subagents. Return the report as your final message; the controller saves it.

## Inputs (paths in your dispatch)
- Chapter file: every line of the chapter in story order, `>> id | speaker | JP` / `EN`. Read ALL of it, in passes if
  large, before judging.
- `docs/synopsis.md` (plot, who is who, late reveals), `docs/style-reference.md` (voice per character),
  `glossary.md` (rulings at the top).

## This game
- A chapter = one episode's room file (R13 holds episodes 12 and 13) or ST (IQ-battle host lines). Lines are in file
  order: scenes run in sequence, but NPC chatter, repeat-visit lines and `next` pages (continuations of the box
  before) are interleaved, so a jump between unrelated lines is not a continuity break by itself.
- `\n` is a line break; a first line ending in `:` is the speaker. Boxes are 32 letters x 3 lines including the
  speaker line: suggested EN must fit that. Mechanical checks (glossary spellings, widths) already pass.
- It is a comedy: every village's obsession, pun and gag must land in English.

## Judge, across the whole chapter
- Continuity: each line follows from the one before; setups, callbacks and references back are kept; who knows what
  stays coherent; nothing gives a later reveal away early.
- Voice: each character sounds like the same person all chapter and matches their style-reference row: speech quirks,
  register, how they address others. Name the line where a voice drifts or goes neutral.
- Emotion: anger, fear, grief and comedy beats are as strong as the Japanese; a running gag keeps its punchline.
- Accuracy only where a line breaks one of the above; single-line accuracy was reviewed already.

## Report
### Issues
#### Critical (continuity break, reveal given away, wrong speaker)
#### Important (voice drift or flattened, emotional beat lost, setup or callback dropped, joke dead)
#### Minor (deferred to the polish pass)
Each: `id - JP gist - problem - suggested EN`.
### Assessment
`ok` (no Critical/Important) | `issue` - one sentence why. The controller writes this word into the chapter's verdict.
