Chou Mashin Eiyuuden Wataru: Another Step (PlayStation) - English fan translation, v{version}

Unofficial. Not affiliated with Banpresto, Aspect or Sunrise. This zip holds a patch only, no game data: you need
your own dump of the Japanese disc. Do not share patched discs.

WHAT YOU NEED
  Chou Mashin Eiyuuden Wataru - Another Step (Japan).bin, the Redump dump (SLPS-01368,
  http://redump.org/discs/quicksearch/{base_sha1_lower}/). Check it against the hashes below; no other dump will
  patch correctly.

HOW TO PATCH
  Windows: Delta Patcher (or any xdelta3 GUI): pick the .bin as the original file, {patch} as the patch.
  Command line:
    xdelta3 -d -s "Chou Mashin Eiyuuden Wataru - Another Step (Japan).bin" {patch} wataru_en.bin
  The patched .bin needs a .cue with the same name beside it (wataru_en.cue), holding:
    FILE "wataru_en.bin" BINARY
      TRACK 01 MODE2/2352
        INDEX 01 00:00:00

  Tested in PCSX-Redux (nightly 30651.20261109.3, SCPH-5500 BIOS). Start from a cold boot: savestates made on the
  Japanese game keep the old font and text. Memory-card saves from the Japanese version were not tested (monpet
  names typed in kana there are not expected to show).

CONTROLS
  As in the Japanese game: circle confirms, cross cancels.

WHAT IS TRANSLATED
  All dialogue and narration in every episode, menus, items, abilities, monpets, shops, IQ-battle rules and hosts,
  ball-battle and mashin-battle text, episode cards, title and config screens, graphics with text (signs, cards,
  battle labels), the monpet name entry (Latin letters, both cases, digits), the memory-card save title, and the
  staff roll (re-laid as Western credits).
  Left in Japanese: spoken voices and songs (audio).

KNOWN LIMITS
  No one has played it start to end yet: every scene was reached with a debug warp and checked on screenshots.
  Ball-battle text was checked on screenshots only (the text logger can't run in ball battles). Some speech
  bubbles in ball battles and one lantern sign were checked as English in video memory, not seen on screen.
  Reports welcome: https://github.com/minhnhattonthat/chou-mashin-eiyuuden-wataru-another-step-en/issues

BASE DISC
  size {base_size}  CRC32 {base_crc}  MD5 {base_md5}  SHA-1 {base_sha1}

PATCHED DISC
  size {patched_size}  CRC32 {patched_crc}  SHA-1 {patched_sha1}

CREDITS
  Original game (c) 1998 Banpresto / Aspect; Mashin Eiyuuden Wataru (c) Sunrise.
  Translation and tools by minhnhattonthat. Made with extensive AI assistance (Claude by Anthropic, reviews by OpenAI
  Codex), so corrections are very welcome. No official English names exist for this game; romanisations and the
  reasons for them are in docs/decisions.md in the source repository.
  Fonts drawn into the game: Spleen 6x12 and 8x16 (BSD-2-Clause, licence below), Liberation Sans (SIL OFL 1.1).

SPLEEN LICENCE
  Copyright (c) 2018-2024, Frederic Cambus
  All rights reserved.

  Redistribution and use in source and binary forms, with or without modification, are permitted provided that the
  following conditions are met:

    * Redistributions of source code must retain the above copyright notice, this list of conditions and the
      following disclaimer.

    * Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the
      following disclaimer in the documentation and/or other materials provided with the distribution.

  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
  INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
  DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
  SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
  SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
  WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
  USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
