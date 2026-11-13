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
| text.md | 16-bit encoding, fonts, room banks + NPC-talk pointer arrays, PRG/FDS/EXE pointer formats, fixed-width EXE name tables | encoding, banks, ST/LVUP/EXE refs verified static; room fonts for R01/R03/R05 and fixed-table readers guessed |
| font.md | 16x16 glyph path (0x80115300 + code*128 -> LoadImage per glyph), the 124 render sites, the digraph-cell decision (D8) | room-dialogue path verified by read/exec traces + in-game spike; other sites by pattern only |
| files.md | disc layout, identity rebuild, formats, RAM map / free space | identity verified; free space trap-tested in title + R00 field only |
| debug.md | main loop / SysMode table, episode index, field sub-states, party stats, file table, the warp tool | modes and episode map verified by forced-mode warps; shop variants, battle selection, modes 12/13/15 open |
| windows.md | width gate: budget per box variant, measured or guess | dialogue measured; menus/battle partly |
| graphics.md | graphics-text survey G1-G24 | static sweep done; tours still owe FK stills, FMV, credits, battle/menu checks |

Recon helpers in `tools/`: `sjisscan.py`, `msgscan.py`, `peek.py`, `fontview.py`, `mktbl.py`, `re.py` (lui/addiu constants, string refs), `lua/ptrlog.lua`, `lua/trapwatch.lua` (free-space trap), `filetab.py` (EXE file table), `loadcalls.py` (load-by-index calls),
`lua/ramlog.lua` (value changes), `lua/poke.lua` (RAM writes), `lua/fileload.lua` (file loads, `--debugger`),
`lua/readpcs.lua` (who reads/writes a RAM range), `lua/callers.lua` (callers of an address), `lua/stackwalk.lua`,
`lua/vdump.lua` + `vram.py` (VRAM/RAM dump at a frame, render 4bpp or 15-bit), `digraph.py` (English cells).
