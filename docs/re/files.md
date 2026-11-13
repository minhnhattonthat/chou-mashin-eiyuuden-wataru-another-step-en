# Disc layout and free space

- Unpack: `tools/mkpsxiso/mkpsxiso-2.30-win64/dumpsxiso.exe -x tree -s layout.xml <cue>` (run in `work/disc/`); 1,013
  files, plain ISO9660 + XA STR. **verified:** `mkpsxiso -y -o ident.bin layout.xml` gives SHA-1
  c2c044d17f5235ff8a419d554b2dd3ab82db2161, identical to the original (2026-11-09). No disc-level compression.
- Directories: `PRG/` (title, battle, menus, FMV WATA01-04.STR), `FPRG/` room overlays R00-R14 + FDS.BIN, `FM16/` fonts
  (MSG_CG common, M16_Rxx per room, FD_STS, R15_MES), `FP00/FP01/FR00-FR03/FK00-FK05` map data per room, `IQ/` IQ-battle
  minigame graphics, `OUT/` title/catch graphics (CHG) + STR, `YM/` battle graphics, `VC00-02` voice STR, `FSEQ/FVBB/FVHH`
  music and sound.
- Formats seen: `.CHG` graphics with a type word: 0xC0000023 (OUT/TTL.CHG, CATCH*: tile map + tiles, "8080 1010"),
  0xC0000322 (PRG/MEM_01.CHG: sprite list), raw 15-bit colour (YM/*). Few TIM headers (15 files). Decoders still to
  write for the graphics sweep.

## RAM map (room scripts, guess unless noted)

- EXE 0x80018000-0x8009C800 (+BSS). Room overlay at 0x800CE000 (verified); largest R14 ends at 0x800F6B3C.
- Zero runs during R00 dialogue (`work/qa/d1/ram.bin`): 0x800E23AB-0x800F0000, 0x800F1A00-0x800F7000, 0x80128072-
  0x80148000 (128 KB), 0x801ECD10-0x801FFAFC. Zero is a candidate, not free: trap-fill and tour before use.
- **FDS.BIN loads at 0x800F7000** (findbase + jal range, 2026-11-13) and runs to 0x8010F5B0: the gap after the largest
  room (0x800F6B3C-0x800F7000, 1.2 KB) is all there is between rooms and FDS. So R00's zero run 0x800F1A00-0x800F7000
  is room space for bigger rooms, not free. PRG overlays (ST, BALLBAT, MACHINE, TTL, LVUP, SBTTL, MEMORY) load at
  0x800D0000, i.e. over the room overlay area: different game modes swap them.
- Best free-RAM candidate: 0x80128072-0x80148000 (128 KB, zero during R00 dialogue). Not yet trap-filled: fill with a
  trap pattern from a Lua hook and tour field, shop, battle, IQ battle, save before relying on it (phase 5).
- Free space inside each overlay: the old bank area once banks move; plan in phase 3/5 (append banks past the overlay end
  if the RAM after the largest room is free, else reuse the old area plus a second region).
