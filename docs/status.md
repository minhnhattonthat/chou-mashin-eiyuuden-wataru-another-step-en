# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 1. Research and recon in progress (text side mostly done; graphics static sweep and a few pointer formats left). Last build: none.
- **Done:**
  - Step 0: PCSX-Redux + SCPH-5500 + mkpsxiso in tools/, smoke boots the original, input + Lua verified, pre-commit gates on tools/check.py, guard hook active, rom.sha1 pinned.
  - Disc unpack/rebuild with mkpsxiso is byte-identical (work/disc/, not yet a test: phase 3).
  - Encoding found and verified: 16-bit LE codes, common font MSG_CG (code+0xA6), per-room kanji fonts M16_Rxx (code-0x1A4), 0x1000 newline, 0x2000 page end. Kana/punct/latin table: tbl/jp_common.tbl (tools/mktbl.py).
  - Room scripts FPRG/R00-R14 (overlay at 0x800CE000): message banks reached only via per-room bank pointer tables (R00 file 0xE5D8), messages found by id walk: banks relocatable. Details docs/re/text.md.
  - Text sources listed: EXE 0x6AA10-0x7CA9A, PRG/ST, BALLBAT, MACHINE, TTL, LVUP, FPRG/FDS, FM16/R15_MES.
  - Prologue route: work/qa/r3 states (s003600 = before new-game FMV end, s009000 = first-room dialogue). Title needs 12-frame presses.
- **Next (phase 1 remainder):**
  1. Graphics static sweep: decode CHG type 0xC0000023 (OUT/TTL, CATCH*: 20x15 map of 16x16 tiles, tile data ~450 B/tile, likely compressed), 0xC0000322 (PRG/MEM_*), YM raw 15-bit images; render sheets; list Japanese in docs/re/graphics.md (rows G1-G8 so far).
  2. Map pointer formats for EXE/ST/BALLBAT/MACHINE/TTL/LVUP/FDS strings, and the second text area per room (R00 0x10D28+, other switch branch 0x800326DC).
  3. Which room font is resident for rooms 01/03/05/11/13 (no M16 file by that name): RAM probe on the font buffer.
  4. Free space: what lives after the overlay end (0x800E04E0 for R00; largest room ends 0x800F6B3C); trap-fill test.
  5. Kanji OCR for common 0xDA-0x1A2 and room fonts (~2,400 cells): template-match + reviewer pass (can move to phase 4).
- **Open bugs:** none.
- **Waiting on the user:** nothing.
