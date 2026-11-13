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
| D12 | 2026-11-14 | Honorifics on kin and deity nouns (agent ruling under D1) | keep (Father-sama, Dragon God-sama); drop | Drop: お父さま "father", 龍神様 "the Dragon God", 神様 "God"/"the gods", お嫁さん "bride". D1 keeps honorifics after names and titles only; on common nouns they read as mistakes. `batches.py` lints "word-san". |
| D13 | 2026-11-14 | 殿 after a name (agent ruling under D1) | -dono; "Lord/Lady"; drop | -dono (Sakuya-dono): same rule as the other kept honorifics. |
| D14 | 2026-11-14 | Sakuya's おじさま to Aragoto (agent ruling under D10) | Uncle; sir / my dear sir | "(my dear) sir", never "Uncle": no kinship, a polite address. Wataru's おじさん = "Old Man Aragoto" (the gag is that he's called old). |
| D15 | 2026-11-14 | 超おもしろカッコいい隊 where the JP shortens it (agent ruling under D4) | follow the JP short form; full name | Full name "Super Funny Cool Squad" everywhere: D4 (full names, no abbreviations). |
| D16 | 2026-11-14 | Item names spelled in kana in battle, kanji in the field (agent ruling under D4) | separate English; one name fitting the 11-letter battle list | One name per item, fitting BALLBAT's 11 letters: Gods' Wrath, Valor Token, Dragon Dew (`names.py` ALIASES). Mismatched names are what players catch first. |
