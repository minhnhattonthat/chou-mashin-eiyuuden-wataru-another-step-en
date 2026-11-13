# Disc layout and free space

- Unpack: `tools/mkpsxiso/mkpsxiso-2.30-win64/dumpsxiso.exe -x tree -s layout.xml <cue>` (run in `work/disc/`); 1,013
  files, plain ISO9660 + XA STR. **verified:** `mkpsxiso -y -o ident.bin layout.xml` gives SHA-1
  c2c044d17f5235ff8a419d554b2dd3ab82db2161, identical to the original (2026-11-09). No disc-level compression.
  `tools/build.py` does both (unpack once, stamped by `work/disc/unpacked.sha1`; repack ~2 s);
  `tests/test_identity.py` asserts the no-edit build is byte-identical. LBAs in the EXE file table are filled at boot
  (CdSearchFile-style), so files can move; the table's size word still needs checking before a file grows.
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
- Best free-RAM candidate: **0x80128800-0x80148000** (126 KB). Trap test `tools/lua/trapwatch.lua` (fill 0xA5, log
  dirty sub-ranges every 600 frames), 2026-11-13: cold boot + intro FMV + title (work/qa/trap0) dirtied only
  0x80128072-0x80128800; R00 field, dialogue, walking out into the village, 36,000 frames from r3/s009000
  (work/qa/trap1) dirtied nothing, and the game ran on with the trap bytes in place. Still untoured: menus, shop,
  battle (normal / mashin / IQ), save screen, FMV mid-game: re-run the probe over the phase-2 warp list before phase 5
  puts anything there.
  - **Warp sweep, 2026-11-13** (`warp_all.py --script tools/lua/trapwatch.lua --var LO=0x80128800 --var HI=0x80148000
    --var FILL=1300`, work/qa/trapwarp; FILL must be after boot: at f10 the EXE load wipes the fill): title, Continue,
    Config, all 15 episode openings, field, field menu + submenus, shop, save, ending, credits leave it untouched;
    **every battle (ball, mashin, IQ, won, lost, level-up) overwrites the whole 0x80128800-0x80148000**. So it is
    free only outside battles: field text/VWF code there must be reloaded after a battle, or live elsewhere.
- **PRG overlay tails (strpack free space)**, trap-tested on the original disc:
  - BALLBAT 0x80101794 (file end) - **0x80104800** (ENE01-18 load there while BALLBAT is resident: the cap).
    2026-11-14, `warp_all.py --rom rom/... --only battle_ball,battle_menu,battle_item,battle_win,battle_lose,levelup
    --script tools/lua/trapwatch.lua --var LO=0x80101794 --var HI=0x80104800 --var FILL=7300` (work/qa/p7/trapB2):
    all 6 reached, nothing dirty. An earlier fill to 0x80109800 (trapB) ran over the ENE data and hung the battle.
  - MACHINE 0x800EA164 - **0x800F0000**: work/qa/p7/trapM (fill to 0x800F206C, mashin_hit) found the game writing
    0x800F0000-0x800F1E54, so the cap is 0x800F0000; trapM2 (fill 0x800EA164-0x800F0000 at f7300, battle_mashin,
    mashin_attack, mashin_hit, mashin_special, mashin_lose, mashin_win; 2026-11-14): all 6 reached, nothing dirty.
  - TTL has no tail (re-laid in its own string pool).
- Free space inside each overlay: the old bank area once banks move; plan in phase 3/5 (append banks past the overlay end
  if the RAM after the largest room is free, else reuse the old area plus a second region).
