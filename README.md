# Chou Mashin Eiyuuden Wataru: Another Step English translation

Unofficial English fan translation of **Chou Mashin Eiyuuden Wataru: Another Step** (超魔神英雄伝ワタル Another Step;
PlayStation, Banpresto / Aspect, 1998, SLPS-01368): the source text and tools that build the patch.

**Just want to play?** Download the patch from [Releases](../../releases) and follow its README. This repository holds
no game data you can play; you need your own dump of the Japanese game.

**Found a bug?** [Report it](../../issues/new/choose): untranslated text, typos, overflow, crashes. Attaching a savestate
helps most.

## Translation status

| Part | Status |
|---|---|
| Dialogue and narration: prologue and all 14 episodes | Translated |
| Menus, items, abilities, monpets, shops, IQ-battle rules, battle text | Translated |
| Title and config screens, episode cards, signs and battle labels drawn as graphics | Translated |
| Monpet name entry | Translated (Latin letters, both cases, digits) |
| Staff roll | Translated (re-laid as Western credits) |
| Voices and songs (audio) | Left in Japanese |

Known issues: none known; see [Issues](../../issues). Every scene was reached with a debug warp and checked on
screenshots, but no one has played it start to end yet. Ball-battle text was checked on screenshots only.

Base disc (Redump, SLPS-01368): `Chou Mashin Eiyuuden Wataru - Another Step (Japan).bin`, 486,099,600 bytes,
CRC32 `B1BFDF2B`, MD5 `74eab1dba095ccfdb3943b2539ca8456`, SHA-1 `c2c044d17f5235ff8a419d554b2dd3ab82db2161`.
Tested in PCSX-Redux (SCPH-5500 BIOS); start from a cold boot, not a savestate made on the Japanese game.

## What's here

| Path | What it is |
|---|---|
| `script/` | Every text block: original Japanese and English. Translation fixes go here. |
| `glossary.md` | Binding names, terms and style rules. |
| `tools/` | Python build chain: extract, insert, lint, release. |
| `tests/` | pytest suite (ROM-dependent tests skip when the ROM is absent). |
| `docs/re/` | Reverse-engineering notes. |
| `docs/decisions.md`, `docs/status.md` | Rulings with their reasons; current progress and open bugs. |
| `docs/fonts.md` | Fonts used and their licences. |
| `AGENTS.md` | Instructions for coding agents (`CLAUDE.md` points to it). |
| `.claude/agents/` | Subagent types (translator, reviewer, visual QA, playtester) with only the tools each needs. |

## Build your own patched ROM

Needs Python 3.12+ and your own dump of the Japanese game.

```sh
git clone https://github.com/minhnhattonthat/chou-mashin-eiyuuden-wataru-another-step-en
cd chou-mashin-eiyuuden-wataru-another-step-en
# copy your dump (.bin + .cue) to: rom/Chou Mashin Eiyuuden Wataru - Another Step (Japan).bin
#   (486099600 bytes, SHA-1 c2c044d17f5235ff8a419d554b2dd3ab82db2161; the build refuses any other dump, see rom.sha1)
# tools: mkpsxiso 2.30 in tools/mkpsxiso/ (see AGENTS.md)
python -X utf8 tools/build.py                          # -> build/wataru_en.bin + .cue
python -X utf8 tools/check.py                          # tests + text lint
```

## Support

If you enjoy this translation, you can support my work on Ko-fi:

[![Support me on Ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/minhnhattonthat)

## Licence

Tools and English translation: MIT. The original Japanese text in `script/` is Banpresto's and is included only so
the translation can be checked against it. Chou Mashin Eiyuuden Wataru: Another Step is (c) 1998 Banpresto / Aspect,
Mashin Eiyuuden Wataru (c) Sunrise; this project is not affiliated with them. Fonts: see `docs/fonts.md`.
Do not share patched ROMs.

The translation was made with extensive AI assistance (Claude by Anthropic). Corrections are very welcome.
