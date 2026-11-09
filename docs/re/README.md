# Reverse-engineering notes

One file per subsystem (text engine, pointers, compression, font, graphics). Mark every finding with how far it is
proven, so a later session doesn't build on a guess:

- **verified** - and how: a decoded known string, a corrupt-and-boot test, a breakpoint hit on the drawing path, a
  passing roundtrip test. Name the test or savestate.
- **guess** - and why it seems likely (byte pattern, another game, an earlier patch's notes). Promote it to verified
  before code depends on it.

Addresses are for the dump in `rom.sha1` unless a note says otherwise.

| File | Covers | State |
|---|---|---|
| text.md | 16-bit encoding, fonts, room message banks + bank pointer tables, other text files | encoding + R00 banks verified; other pointer formats open |
| files.md | disc layout, identity rebuild, formats, RAM map / free-space candidates | identity verified; free space guessed |
| graphics.md | graphics-text survey | partial (tour to first dialogue; static CHG sweep to do) |

Recon helpers in `tools/`: `sjisscan.py`, `msgscan.py`, `peek.py`, `fontview.py`, `mktbl.py`, `lua/ptrlog.lua`.
