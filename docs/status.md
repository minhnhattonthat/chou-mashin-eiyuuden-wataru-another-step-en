# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 1. Research and recon in progress (graphics static sweep done for OUT/PRG/IQ/FM16; YM + room atlases reviewed by codex; text pointer formats mapped for TTL/MACHINE/BALLBAT/FDS; ST/LVUP/EXE pointers, room fonts and free-space trap test left). Last build: none.
- **Done:**
  - Step 0: PCSX-Redux + SCPH-5500 + mkpsxiso in tools/, smoke boots the original, input + Lua verified, pre-commit gates on tools/check.py, guard hook active, rom.sha1 pinned.
  - Disc unpack/rebuild with mkpsxiso is byte-identical (work/disc/, not yet a test: phase 3).
  - Encoding: 16-bit LE codes, common font MSG_CG (code+0xA6), per-room kanji fonts M16_Rxx (code-0x1A4), 0x1000 newline, 0x2000 page end. tbl/jp_common.tbl. Room message banks relocatable (docs/re/text.md).
  - Text sources final: FPRG/R00-R14 (no R12), FDS, EXE, PRG/ST, BALLBAT, MACHINE, TTL, LVUP. Everything else decodes to noise (text.md).
  - Overlay bases: PRG overlays 0x800D0000, FDS 0x800F7000 (tools/findbase.py). u32 string tables found for TTL, MACHINE, BALLBAT, FDS.
  - Graphics: CHG = chain of uncompressed VRAM uploads (tools/chg.py, tests/test_chg.py); sweep renders in work/gfx/sweep/ (regenerate: see graphics.md). Rows G1-G15 in docs/re/graphics.md: big ones are MEM_01 (memory-card screen), SUBTTL (episode-title glyph atlas), SBTCHAR (area cards), R15_MES (prologue scroll), TTL menu, IQ win/lose.
- **Next (phase 1 remainder):**
  1. Merge codex reviews `work/gfx/sweep/ym_review.md` (YM battle graphics) and `fr_review.md` (room atlases) into graphics.md rows (if missing, rerun: commands in git log of this commit / graphics.md "Pending").
  2. Pointers for ST.BIN, LVUP.BIN, EXE strings: no u32 pointer hits; log reads with tools/lua/ptrlog.lua on the battle menu / level-up (or disassemble lui/addiu refs). Second text area per room (R00 0x10D28+, branch 0x800326DC).
  3. Which room font is resident for rooms 01/03/05/11/13 (no M16 file by that name): RAM probe on the font buffer.
  4. Free space: trap-fill 0x80128072-0x80148000 and tour (files.md).
  5. SUBTTL caption strings: find the atlas-index strings (SBTTL.BIN guess); FK*/K*.BIN event stills look compressed: check stills in VRAM during tours.
  6. Kanji OCR for common 0xDA-0x1A2 and room fonts: can move to phase 4.
- **Open bugs:** none.
- **Waiting on the user:** nothing.
