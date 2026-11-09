# Skill gotchas (one line each: reference file, then the fact)

- references/pipeline.md §Recon: `relsearch.py WORD` with no `--width` found nothing on 16-bit LE text (this game: あ=0x0001); `--width 2` found it at once. Try both widths before concluding the encoding is not kana-ordered.
- references/emulator-qa.md §PCSX-Redux: at this game's title, 6-frame Start/circle presses in a route were ignored; 12-frame presses registered.
- references/platform-ps1.md: a game with no Shift-JIS can carry per-room fonts whose kanji codes are allocated per overlay (same code = different kanji per room); tables must be per room, and `jp_left.py --sjis` will see nothing.
