# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 2. Debug tool next (phase 1 recon done 2026-11-13). Last build: none.
- **Done:**
  - Step 0: PCSX-Redux + SCPH-5500 + mkpsxiso in tools/, smoke boots the original, input + Lua verified, pre-commit gates on tools/check.py, guard hook active, rom.sha1 pinned.
  - Disc unpack/rebuild with mkpsxiso is byte-identical (work/disc/, not yet a test: phase 3).
  - Phase 1 (docs/re/): encoding (16-bit LE, MSG_CG common font, per-room M16 kanji), text sources, pointer formats for
    every source (room banks + NPC-talk u32 arrays, ST/LVUP lui/addiu blocks, TTL/MACHINE/BALLBAT/FDS u32 tables, EXE
    u32 arrays + fixed-width name tables), free RAM 0x80128800-0x80148000 (trap-tested title + R00 field), graphics
    survey G1-G24 (static sweep complete; FD_STS menu labels and CNF_MSG config font added).
- **Next (phase 2: debug tool, `references/emulator-qa.md` §Debug tool):**
  1. Room switch: room id halfword 0x8009C90C (< 15), script pointer 0x8009C998 (text.md). Find the room-load
     routine and story-flag area; build `tools/debug/warp.lua` + `tools/debug/scenes.txt` (field rooms R00-R14, shop,
     menu/status, save screen, normal / mashin / IQ battles, level-up, each episode title card, game over, ending, credits).
  2. While warping: RAM-read the loaded room font for R01/R03/R05 (text.md "Fonts other than MSG_CG"); log reads of the
     EXE fixed-width tables (equipment, attacks, enemies) to confirm their bases; dump VRAM on the status screen (FD_STS
     tail format) and config screen (CNF_MSG use).
  3. Re-run `tools/lua/trapwatch.lua` over every warp scene before phase 5 uses 0x80128800+.
  4. Tour checks owed by the graphics survey: FK stills, FMV burnt-in text, credits, battle signs (graphics.md end).
  5. Kanji OCR for common 0xDA-0x1A2 and room fonts: phase 4.
- **Open bugs:** none.
- **Waiting on the user:** nothing.
