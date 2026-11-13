# Decisions

The user's rulings on scope, style and trade-offs, newest last. Read before asking the user anything; if a later
decision replaces one, mark the old one "replaced by D<n>" instead of deleting it. Binding term spellings live in
`glossary.md`; this file holds the why.

All D1-D7 came pre-answered in the owner's one-shot brief (Orca dispatch, 2026-11-09); the whole project is pre-approved.

| # | Date | Question | Options offered | Decision and reason |
|---|---|---|---|---|
| D1 | 2026-11-09 | Honorifics and name order | keep (-san), drop; JP or Western order | Keep honorifics; Western order (given name first). Owner default. |
| D2 | 2026-11-09 | Romanization source for names | official art, earlier patch, Hepburn | Official English names where they exist, else an earlier fan patch, else Hepburn without macrons. |
| D3 | 2026-11-09 | Credits | stay Japanese, translate | English. |
| D4 | 2026-11-09 | Abbreviations | engine work first (default), abbreviate | Engine work first (skill default; full names and terms). |
| D5 | 2026-11-09 | Graphics text left in Japanese | none (default), list | Translate all (titles, menus, banners, cards); keep the original Japanese logo only if it has no official English version. |
| D6 | 2026-11-09 | Specs and plans | need approval, pre-approved | Pre-approved: keep going through checkpoints, report at the end. |
| D7 | 2026-11-09 | Existing saves / memory cards | use them, none | None provided; build the debug tool as usual. |
| D8 | 2026-11-14 | English font for the 16x16 text (agent ruling under D6) | half-width (patch ~124 render sites), runtime VWF/compose hook, pre-rendered two-letter cells | Two letters per 16x16 cell, pre-rendered per font context by the build (Spleen 8x16, BSD-2). No renderer change, every fixed field doubles its letters, proven in game. Costs: printed numbers stay one digit per cell, odd-length runtime joins leave a half-cell gap. docs/re/font.md. |
| D9 | 2026-11-14 | Names with no official English (agent ruling under D2/D6) | strict Hepburn (Warumonda, Waruririsu, Sandaru); English-pun spelling where the katakana spells an English word or Western name | Hepburn, except names that pun on an English word or Western name take that spelling: Warumonder, Warulilith, Warurine, Watt, Thundar, Carl/Bill Jobs. Strict Hepburn hides the joke the Japanese reader gets. Speaker labels fixed in glossary.md `## Speakers`. |
| D10 | 2026-11-14 | Register and sound effects (agent ruling under D6) | neutral; playful kids' comedy; SFX as *Slam!*, caps, or plain | Playful, natural kids' comedy English with light JP flavour (honorifics), every pun replaced by an English pun, item/skill coinages get punny English names. SFX plain English onomatopoeia, no asterisks (the two-letter cells make * cost a half cell each). US spelling. |
| D11 | 2026-11-14 | Who translates (Orca refuses nested workers) | controller alone; `codex exec` | Pilot + style reference by the controller, batches by `codex exec` prompt-only (`tools/tl_codex.py`; its Windows sandbox cannot start processes, so files go in the prompt), checked by `tools/batches.py check`, reviewed by a fresh codex pass with docs/reviewer-brief.md. |
