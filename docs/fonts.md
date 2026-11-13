# Fonts

Every font or glyph sheet the build reads ends up inside the released patch, so its licence must allow that. One row
per file; a font with no known licence doesn't go into a release.

| File | Source (URL, version) | Licence | Redistributable in a patch | Used for | Changes made |
|---|---|---|---|---|---|
| fonts/spleen-8x16.bdf | github.com/fcambus/spleen, tag 2.1.0 (fonts/LICENSE-spleen.txt) | BSD-2-Clause | yes, with the licence text in the release README | two-letter cells of the 16x16 text fonts (tools/digraph.py) | 8th column cleared (T, *); shadow added at render |
