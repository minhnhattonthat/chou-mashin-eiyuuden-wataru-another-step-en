# Skill gotchas (one line each: reference file, then the fact)

- references/pipeline.md §Recon: `relsearch.py WORD` with no `--width` found nothing on 16-bit LE text (this game: あ=0x0001); `--width 2` found it at once. Try both widths before concluding the encoding is not kana-ordered.
- references/emulator-qa.md §PCSX-Redux: at this game's title, 6-frame Start/circle presses in a route were ignored; 12-frame presses registered.
- references/platform-ps1.md: a game with no Shift-JIS can carry per-room fonts whose kanji codes are allocated per overlay (same code = different kanji per room); tables must be per room, and `jp_left.py --sjis` will see nothing.
- references/graphics.md §Survey: PS1 games that store graphics as raw VRAM-upload chains (u16 x,y,w,h + data) can be swept with no format knowledge: find the longest chain of plausible headers ending at EOF (prefer the chain with most blocks; a lone big block from inside a tile map can chain to EOF by chance). CLUT rows may start at y=506 with h=16 and wrap past 511.
- references/graphics.md §Survey: sheet.py sizes every tile to the largest image, so mixed-size texture dumps (8x48 frames next to 256x256 atlases) give dozens of near-empty pages; a shelf packer (tools/pack.py here) fit 971 blocks into 23 pages. codex exec -s read-only -i page.png... worked as the independent read-only reviewer for those pages.
