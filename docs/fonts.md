# Fonts

Every font or glyph sheet the build reads ends up inside the released patch, so its licence must allow that. One row
per file; a font with no known licence doesn't go into a release.

| File | Source (URL, version) | Licence | Redistributable in a patch | Used for | Changes made |
|---|---|---|---|---|---|
| fonts/spleen-6x12.bdf | github.com/fcambus/spleen, tag 2.1.0 (fonts/LICENSE-spleen.txt) | BSD-2-Clause | yes, with the licence text in the release README | redrawn small labels: battle commands, party names (tools/gfx_gen.py) | none (outline added at render) |
| fonts/liberation/LiberationSans-{Bold,Regular}.ttf | github.com/liberationfonts/liberation-fonts, release 2.1.5 (fonts/liberation/LICENSE.txt) | SIL OFL 1.1 | yes | redrawn title menu (Bold 14) and copyright line (Regular 15) (tools/gfx_gen.py) | none |
| fonts/spleen-8x16.bdf | github.com/fcambus/spleen, tag 2.1.0 (fonts/LICENSE-spleen.txt) | BSD-2-Clause | yes, with the licence text in the release README | two-letter cells of the 16x16 text fonts (tools/digraph.py) | 8th column cleared (T, *); shadow added at render |
