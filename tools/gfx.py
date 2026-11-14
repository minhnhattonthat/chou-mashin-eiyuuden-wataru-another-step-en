"""gfx.py: graphics-text redraws. Export a rect of an upload block (docs/re/graphics.md) as RGB PNG under its CLUT,
and write edited PNGs back into the disc files through insert.put() (build) by palette index.

gfx/gfx.tsv rows (tab-separated, # comments):
  png  target file  block offset  bpp  clut file  clut offset  palette  rect x,y,w,h (block pixels)
`png` is relative to gfx/en/ (the English); the original rect goes to gfx/orig/ (export). A png may be listed for
several targets (the same image in several files). Colour 0x0000 (transparent) shows as magenta (255,0,255).
Import keeps a pixel's original index when its colour didn't change, else takes the first palette index with that
colour (index 0 only for magenta); any colour outside the palette fails the build.

usage: python -X utf8 tools/gfx.py export [ROW-PNG..]      write gfx/orig/<png> (+ gfx/en/<png> if missing)
       python -X utf8 tools/gfx.py show FILE OFF BPP CLUTFILE CLUTOFF PAL OUT.png   whole block, one palette
"""
import struct
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
TREE = ROOT / "work" / "disc" / "tree"
GFX = ROOT / "gfx"
MAGENTA = (255, 0, 255)


# Sprite records that cut the redrawn text out of its atlas: (path, offset, struct fmt, original, new, why).
# TTL.BIN title menu: [u16 tpage, u16 clut, u8 u, u8 v, u16 w, u16 h, s16 x, s16 y] (docs/re/graphics.md G4).
REC = "<HHBBHHhh"
RECS = [
    ("PRG/TTL.BIN", 0x4FA2, REC, (0x1A, 0x7E44, 0, 112, 112, 16, -56, -40), (0x1A, 0x7E44, 80, 112, 80, 16, -40, -40),
     "title Continue"),
    ("PRG/TTL.BIN", 0x4FB0, REC, (0x1A, 0x7E44, 64, 112, 96, 16, -48, -56), (0x1A, 0x7E44, 0, 112, 80, 16, -40, -56),
     "title New Game"),
]
# BALLBAT party-panel names (col u=112, rows v 144-192): w 32/40 -> 48, left edge kept (HP digits sit far right)
RECS += [("PRG/BALLBAT.BIN", off + 6, "<H", (w,), (48,), "battle name w") for off, w in
         ((0x250FC, 32), (0x2510A, 40), (0x25118, 32), (0x25144, 32), (0x25160, 32), (0x2518C, 32), (0x2519A, 40))]
# FDS shop total line (FD_SHP.PX, G11): 個 -> "pcs" 18 px, 合計 -> "Total" moved 2 px right in the atlas
RECS += [
    ("FPRG/FDS.BIN", 0x171C6, REC, (0x0C, 0x784D, 144, 0, 32, 16, -32, 8), (0x0C, 0x784D, 146, 0, 30, 16, -32, 8),
     "shop Total"),
    ("FPRG/FDS.BIN", 0x171D4, REC, (0x0C, 0x784D, 128, 0, 16, 16, -56, 8), (0x0C, 0x784D, 128, 0, 18, 16, -56, 8),
     "shop pcs"),
]


# G23 field menu / status labels (FM16/FD_STS.BIN glyph sheet, tpage 0x0C, docs/re/graphics.md G23): each label is a
# run of FDS.BIN sprite records, one per JP glyph or word. The English goes into one strip of the freed glyph rows
# (FM_FREE, laid out by fm_layout), the label's leftmost record cuts the strip and the rest get w = h = 0.
FDS = "FPRG/FDS.BIN"
FM_FREE = [(0, 8, 120), (0, 24, 120), (0, 40, 120), (0, 56, 120), (0, 72, 120), (0, 88, 80), (0, 104, 72),
           (176, 152, 64), (0, 168, 256), (0, 184, 256), (0, 200, 208), (0, 216, 256), (0, 232, 224)]  # u, v, w; 16 tall
FM_K8 = {8: "あいうえおかきくけこさしすせそ", 24: "たちつてとなにぬねのはひふへほ", 40: "まみむめもやMゆPよらりるれろ",
         56: "わをんゃ_ゅ_ょぁぃぅぇぉっー", 72: "がぎぐげござじずぜぞだぢづでど", 88: "ばびぶべぼぱぴぷぺぽ", 104: "ランクタイプレベル"}
FM_K16 = {152: "...........第話最終：", 168: "炎部ワタル剣部アラゴト忍部サクヤ", 184: "ワルリーヌ回復攻撃・補助経験値の",
          200: "他アイテムそうびもんペット$$", 216: "ステータスコンフィグ気合装備属性", 232: "つかせいりペン超必殺技こたカ□",
          120: "....了"}
# (JP the records spell in (y, x) order, English, record offsets, x of the English: None = leftmost record's x,
#  "c" = centred on 0 (button titles), or an int; colon record moved to the English's right end, or None)
_NAMES = [("炎部ワタル", "Wataru", 0x12568, 0x142A6, 0x1506C), ("剣部アラゴト", "Aragoto", 0x126C8, 0x143CE, 0x151BC),
          ("忍部サクヤ", "Sakuya", 0x12828, 0x144F6, 0x1530C), ("ワルリーヌ", "Warurine", 0x12988, 0x1461E, 0x1545C)]
FM_LABELS = [(jp, en, [o], None, None) for jp, en, *offs in _NAMES for o in offs]
_MENU = [("アイテム", "Item", 0x12B04, 0x12D9C), ("そうび", "Equip", 0x12AF6, 0x12DF0),
         ("もんペット", "Monpet", 0x12AE8, 0x12E44), ("ステータス", "Status", 0x12ADA, 0x12E98),
         ("コンフィグ", "Config", 0x12ACC, 0x12EEC)]
FM_LABELS += [(jp, en, [lst], None, None) for jp, en, lst, _ in _MENU]  # field menu list
FM_LABELS += [(jp, en, [btn], "c", None) for jp, en, _, btn in _MENU]  # window title buttons
FM_LABELS += [
    ("第話", "Ep.", [0x12BA0, 0x12B92], -27, None),  # 第 [episode digits] 話: the frame is a fixed 64 px
    ("最終話", "Final", [0x12BE6, 0x12BD8], "c", None),
    ("つかう", "Use", [0x12F4E, 0x12F40], "c", None),
    ("せいり", "Sort", [0x12F88], "c", None),
    ("イペント", "Key Items", [0x12FDC, 0x12FCE, 0x12FC0], "c", None),
    ("回復", "Heal", [0x1303E, 0x13030], "c", None),  # item tabs
    ("攻撃", "Attack", [0x1306A, 0x1305C], "c", None),
    ("攻撃補助", "Support", [0x13096, 0x13088], "c", None),
    ("その他", "Other", [0x130D0, 0x130C2, 0x130B4], "c", None),
    ("回復", "Heal", [0x140B8, 0x140AA], None, None),  # item list headings
    ("攻撃", "Attack", [0x14138, 0x1412A], None, None),
    ("攻撃・補助", "Support", [0x141E2, 0x141D4, 0x141C6, 0x141B8, 0x141AA], None, None),
    ("その他", "Other", [0x1426E, 0x14260, 0x14252], None, None),
    ("ちから", "Strength", [0x14C18, 0x14C0A, 0x14BFC], None, None),  # status / equip stat column
    ("かしこさ", "Wisdom", [0x14BEE, 0x14BE0, 0x14BD2, 0x14BC4], None, None),
    ("がんじょうさ", "Toughness", [0x14BB6, 0x14BA8, 0x14B9A, 0x14B8C, 0x14B7E, 0x14B70], None, None),
    ("がまんづよさ", "Endurance", [0x14B62, 0x14B54, 0x14B46, 0x14B38, 0x14B2A, 0x14B1C], None, None),
    ("すばやさ", "Speed", [0x14B0E, 0x14B00, 0x14AF2, 0x14AE4], None, None),
    ("こうげき", "Attack", [0x14AD6, 0x14AC8, 0x14ABA, 0x14AAC], None, None),
    ("ぼうぎょ", "Defense", [0x14A9E, 0x14A90, 0x14A82, 0x14A74], None, None),
    ("とくしゅこうげき", "Sp. Attack", [0x14A66, 0x14A58, 0x14A4A, 0x14A3C, 0x14A2E, 0x14A20, 0x14A12, 0x14A04],
     None, None),  # 72 px to the value column (D20)
    ("とくしゅぼうぎょ", "Sp. Defense", [0x149F6, 0x149E8, 0x149DA, 0x149CC, 0x149BE, 0x149B0, 0x149A2, 0x14994],
     None, None),
    ("かいひ", "Evasion", [0x14986, 0x14978, 0x1496A], None, None),
    ("ゆうき", "Valor", [0x1495C, 0x1494E, 0x14940], None, None),
    ("気合い", "Spirit", [0x14932, 0x148FA], None, None),
    ("必殺技", "Special", [0x14D30], None, None),
    ("超必殺技", "Super Special", [0x14D4C], None, None),
    ("げんざいのレベル", "Level", [0x14F54, 0x14F46, 0x14F38, 0x14F2A, 0x14F1C, 0x14F0E], None, None),
    ("経験値", "Experience", [0x14EAC, 0x14E9E, 0x14E90], None, None),
    ("つぎのレベルまで", "Next Level", [0x14F00, 0x14EF2, 0x14EE4, 0x14ED6, 0x14EC8, 0x14EBA], None, None),
] + [("装備：", "Equipment", [o], None, o - 14) for o in (0x15088, 0x151D8, 0x15328, 0x15478)] + [
    ("属性：", "Element", [0x1619A], -107, 0x1618C),  # monpet detail; the element value starts 2 px after the colon
    ("げんざいのランク：", "Current Rank", [0x1612A, 0x16138, 0x16146, 0x16154, 0x16162, 0x16170], -1, 0x1617E),
    ("攻撃カ", "Power", [0x1635A, 0x1634C], None, None),
    ("しょうひMP", "MP Cost", [0x1633E, 0x16330, 0x16322, 0x16314, 0x16306, 0x162F8], None, None),
    ("必殺技", "Special", [0x162EA], None, None),
    ("必殺技タイプ", "Special Type", [0x162DC, 0x162CE], None, None),
    ("こうたい", "Swap", [0x1649E, 0x16490, 0x16482, 0x16474], "c", None),
    ("終了", "Exit", [0x179CA, 0x179BC], None, None),
]
FM_GANBO = (208, 200, 32)  # ｹﾞﾝﾎﾞ money unit (record 0x12C2E): redrawn in place
FM_BLANK = [0x13188, 0x13196, 0x131A4, 0x131B2]  # spacers cutting the empty cell (32, 56): w = h = 0
FM_SHOP = (0x16E00, 0x17700)  # shop records: they cut FD_SHP.PX, swapped into the same VRAM (G11)


def fm_char(u, v, w, h):
    """JP the FD_STS cell rect (u, v, w, h) shows, None outside the glyph rows."""
    for k, s, cw in [(k, s, 8) for k, s in FM_K8.items()] + [(k, s, 16) for k, s in FM_K16.items()]:
        if v == k and h == 16 and (cw == 16 or u < 120):
            return "".join(s[c] if c < len(s) else "?" for c in range(u // cw, (u + w + cw - 1) // cw))
    return None


def fm_layout():
    """{English: (u, v, w)}: first fit, longest first, into FM_FREE (widths from gfx_gen's outlined Spleen 6x12)."""
    import gfx_gen
    free = [list(f) for f in FM_FREE]
    out = {}
    for en in sorted({lab[1] for lab in FM_LABELS}, key=lambda t: (-gfx_gen.bdf_width(t), t)):
        w = gfx_gen.bdf_width(en)
        f = next(f for f in free if f[2] >= w)  # StopIteration = atlas full
        out[en] = (f[0], f[1], w)
        f[0] += w
        f[2] -= w
    return out


def fm_recs(d):
    """gfx.RECS-style entries for the G23 labels, checked against the original FDS.BIN bytes `d`."""
    lay = fm_layout()
    out = []
    for jp, en, offs, xpos, colon in FM_LABELS:
        recs = {o: struct.unpack_from(REC, d, o) for o in offs}
        assert all(r[0] == 0x0C and r[1] in (0x784D, 0x784C) for r in recs.values()), (en, "not an FD_STS record")
        spelt = "".join(fm_char(*r[2:6]) or "?" for r in sorted(recs.values(), key=lambda r: (r[7], r[6])))
        assert spelt + ("：" if colon else "") == jp, (en, spelt, jp)
        u, v, w = lay[en]
        lead = min(recs, key=lambda o: (recs[o][6], recs[o][7]))
        tp, cl, _, _, _, _, x, y = recs[lead]
        x = -(w // 2) if xpos == "c" else x if xpos is None else xpos
        for o, r in recs.items():
            new = (tp, cl, u, v, w, 16, x, y) if o == lead else r[:4] + (0, 0) + r[6:]
            out.append((FDS, o, REC, r, new, "fmenu " + en))
        if colon:
            r = struct.unpack_from(REC, d, colon)
            assert fm_char(*r[2:6]) == "：", (en, "colon")
            out.append((FDS, colon, REC, r, r[:6] + (x + w - 1, r[7]), "fmenu colon " + en))
    for o in FM_BLANK:
        r = struct.unpack_from(REC, d, o)
        assert fm_char(*r[2:6]) == "_", hex(o)
        out.append((FDS, o, REC, r, r[:4] + (0, 0) + r[6:], "fmenu blank"))
    return out


def fm_check(d):
    """Every FD_STS record in FDS.BIN that cuts a freed glyph row is one fm_recs rewrites (else it would show
    English pieces): returns the offsets of the strays."""
    done = {o for lab in FM_LABELS for o in lab[2]} | set(FM_BLANK)
    stray = []
    for o in range(0, len(d) - 14, 2):
        tp, cl, u, v, w, h, x, y = struct.unpack_from(REC, d, o)
        if tp != 0x0C or cl not in (0x784D, 0x784C) or not (0 < w <= 256 and 0 < h <= 64) or o in done or \
                FM_SHOP[0] <= o < FM_SHOP[1]:
            continue
        if any(u < fu + fw and fu < u + w and v < fv + 16 and fv < v + h for fu, fv, fw in FM_FREE):
            stray.append(o)
    return stray


# G5 area cards (OUT/SBTCHAR.CHG glyph sheet, tpage 0x0C, docs/re/graphics.md G5): PRG/SBTTL.BIN 0x3B70-0x4E00
# holds one sprite list per card label (REC records, list ends 0xFFFF): text records (CLUT 0x7DC4, palette 4) cut
# 16x16 glyph runs, box records (0x7DC5, palette 5) cut the 80x32 bar at (0,176); the list after each text list is
# its box alone (same pieces). English = Spleen 8x16 strips (8 px per letter), one per word, in the freed rows; the
# label's text records take the words in x order, the rest get w = h = 0. A box that must grow keeps its anchored
# edge (left when it starts at x 0, else right): left piece from the bar (u0, <= 76), right piece from bar B, a
# 176-px copy of the bar's middle + right edge at (80,176) (where the digits and 創界山のふもと were).
SBT = "PRG/SBTTL.BIN"
SBT_LISTS = (0x3B70, 0x4E00)
SBT_ROWS = {48: "...............イ", 64: ".........もんじゃガンボ", 80: ".........コンビニづくし",
            96: "エキストラタウンキャラクターシテ", 112: "ケイコービリアイドリアンサウンド",
            128: "エアスリートアスレチック花嫁サビ", 144: "レーワルモンダー城村第話界層プロ",
            160: "ローグエンディング一二三四五六七", 176: ".....0123456789.", 192: ".....創界山のふもと"}
# (keys as the records spell them: シティ is drawn シテ + a full-size イ)
SBT_FREE = [(0, 96, 256), (0, 112, 256), (0, 128, 256), (0, 144, 256), (0, 160, 256), (0, 208, 256), (0, 224, 256),
            (0, 240, 256), (144, 64, 112), (144, 80, 112), (240, 48, 16)]  # u, v, w; 16 tall
SBT_BAR = (80, 176, 176, 32)  # bar B
_KAN = "一二三四五六七"
SBT_EN = {"創界山のふもと": "Foot of Sokaizan", "プロローグ": "Prologue", "エンディング": "Ending",
          "もんじゃ村": "Monja Village", "コンビニ村": "Konbini Village", "ガンボづくし村": "Ganbozukushi Village",
          "エキストラタウン": "Extra Town", "キャラクターシテイ": "Character City", "ケイコータウン": "Keiko Town",
          "ビリビリタウン": "Biribiri Town", "アイドリアンシテイ": "Idorian City", "サウンドエコー村": "Sound Echo Village",
          "アスリート村": "Athlete Village", "アスレチック村": "Athletic Village", "花嫁村": "Bride Village",
          "サビレータウン": "Sabire Town", "ワルモンダー城": "Warumonder Castle"}
SBT_EN.update({f"第{k}界層": f"Layer {i + 1}" for i, k in enumerate(_KAN)})
SBT_EN.update({f"第{n:02d}話": f"Episode {n}" for n in range(1, 15)})


def sbt_char(u, v, w, h):
    r = SBT_ROWS.get(v)
    if r is None or h != 16:
        return None
    return "".join(r[c] if c < len(r) else "?" for c in range(u // 16, (u + w + 15) // 16))


def sbt_lists(d):
    """[(offset, [(record offset, REC tuple)..])] for every sprite list in SBT_LISTS."""
    out, o, cur, start = [], SBT_LISTS[0], [], SBT_LISTS[0]
    while o < SBT_LISTS[1]:
        a = struct.unpack_from("<H", d, o)[0]
        if a == 0xFFFF:
            out.append((start, cur))
            cur, o = [], o + 2
            while o < SBT_LISTS[1] and struct.unpack_from("<H", d, o)[0] != 0x0C:  # gap: list headers / anim data
                o += 2
            start = o
        elif a == 0x0C:
            cur.append((o, struct.unpack_from(REC, d, o)))
            o += 14
        else:
            o += 2
    return out


def _words(en, n):
    """Strip texts for a label with n text records: one per word, the leading words merged when n is short."""
    w = en.split(" ")
    while len(w) > n:
        w[:2] = [w[0] + " " + w[1]]
    return w


def _sbt_labels(d):
    """[(list index, text records in x order, box records in x order, JP, English)] for every text list."""
    out = []
    for k, (start, recs) in enumerate(sbt_lists(d)):
        text = sorted([(o, r) for o, r in recs if r[1] == 0x7DC4], key=lambda t: t[1][6])
        box = sorted([(o, r) for o, r in recs if r[1] == 0x7DC5], key=lambda t: t[1][6])
        if text:
            jp = "".join(sbt_char(*r[2:6]) or "?" for _, r in text)
            out.append((k, text, box, jp, SBT_EN[jp]))  # KeyError = a label with no English
    return out


def sbt_layout(d):
    """{strip text: (u, v)}: first fit, longest first, into SBT_FREE (8 px per letter + the 1-px outline)."""
    free = [list(f) for f in SBT_FREE]
    out = {}
    for t in sorted({w for _, text, _, _, en in _sbt_labels(d) for w in _words(en, len(text))},
                    key=lambda t: (-len(t), t)):
        w = 8 * len(t) + 2
        f = next(f for f in free if f[2] >= w)  # StopIteration = atlas full
        out[t] = (f[0], f[1])
        f[0] += w
        f[2] -= w
    return out


def sbt_recs(d):
    """gfx.RECS-style entries for the G5 card labels and their box twins, checked against the original SBTTL.BIN."""
    lay = sbt_layout(d)
    lists = sbt_lists(d)
    out, seen = [], set()
    for k, text, box, jp, en in _sbt_labels(d):
        seen.add(jp)
        bl, br = min(r[6] for _, r in box), max(r[6] + r[4] for _, r in box)
        T = 8 * len(en)
        W = max(br - bl, -(-(T + 16) // 8) * 8)
        left = bl if bl == 0 else br - W
        x0 = left + (W - T) // 2
        pos, words = 0, _words(en, len(text))
        for i, (o, r) in enumerate(text):
            if i < len(words):
                pos = en.index(words[i], pos)
                u, v = lay[words[i]]
                new = r[:2] + (u, v, 8 * len(words[i]) + 2, 16, x0 + 8 * pos - 1, r[7])
                pos += len(words[i])
            else:
                new = r[:4] + (0, 0) + r[6:]
            out.append((SBT, o, REC, r, new, "card " + en))
        if W == br - bl:
            continue
        twin = lists[k + 1][1]
        assert sorted(r for _, r in twin) == sorted(r for _, r in box), (en, "box twin")
        assert len(box) >= 2, (en, "one-piece box can't grow")
        lw = min(76, W - 8)  # u76-79 is the bar's right edge
        for bx in (box, sorted(twin, key=lambda t: t[1][6])):
            for i, (o, r) in enumerate(bx):
                new = r[:2] + ((256 - (W - lw), 176, W - lw, 32, left + lw) if i == len(bx) - 1 else
                               (0, 176, lw, 32, left)) + r[7:]
                out.append((SBT, o, REC, r, new, "card box " + en))
    assert seen == set(SBT_EN), set(SBT_EN) - seen
    return out


# G6 episode captions (OUT/SUBTTL.CHG: 3 glyph blocks = tpages 0x0C/0x0D/0x1C; CLUT (0,506) palette 0 = the fade-in
# ramp, 1 = all white): PRG/SBTTL.BIN CAP_LISTS holds 32 sprite lists = 16 captions (episode index 0-15, 15 = the
# ending) x 2 CLUTs (0x7E80 / 0x7E81), 40-px glyph records + 8x8 furigana, one caption per list, lines 40 px tall.
# English: one Liberation Sans Bold strip per line (CAP_H tall) packed into the freed blocks; the line's leftmost
# glyph record cuts it (first line at the JP line's left x, later lines end at the JP line's right x, as staggered as
# the JP; never past CAP_RIGHT), the other records get w = h = 0.
CAP_LISTS = (0x5528, 0x7274)
CAP_BLK = {0x0C: 0x208, 0x0D: 0x8210, 0x1C: 0x10218}  # tpage -> SUBTTL.CHG upload block
CAP_H, CAP_SIZE, CAP_RIGHT = 26, 24, 180  # strip height, font px, max right x (screen x = list x + ~132)
CAP_EN = [  # per caption: (JP, English lines); JP lines are the list's own (asserted by count)
    ("えっ!? / ボクは救世主？", ["Huh?!", "I'm the Savior?"]),
    ("お弁当に、/ なりたーい", ["I wanna be", "a bento!"]),
    ("お金があれば、/ しーあわせ♥", ["With money,", "I'm ha~ppy!"]),
    ("行くぞ! / 超おもしろ / カッコいい隊!", ["Let's go!", "Super Funny", "Cool Squad!"]),
    ("“コミック創界山” / って、なあに?", ['"Comic Sokaizan"', "...what's that?"]),
    ("救世主がふたり!?", ["Two Saviors?!"]),
    ("最強タッグ! / ワタルとワタル!!", ["Ultimate tag team!", "Wataru & Wataru!!"]),
    ("V.I.に、/ もうメロメロ", ["V.I. has me", "head over heels"]),
    ("演歌は / 人の心です!", ["Enka is", "the people's heart!"]),
    ("金メダルって、/ そんなに大事?", ["Is a gold medal", "that big a deal?"]),
    ("体を鍛えて / 温泉へ!", ["Work out, then", "hit the hot spring!"]),
    ("花嫁さんは… / サクヤ!?", ["The bride is...", "Sakuya?!"]),
    ("龍神丸、倒れる!", ["Ryujinmaru falls!"]),
    ("新生! / 天翔龍神丸!!", ["Reborn!", "Tensho Ryujinmaru!!"]),
    ("決戦! / ワルモンダー!", ["Showdown!", "Warumonder!"]),
    ("戦いが終わって、/ そして…", ["The battle's over,", "and then..."]),
]


def cap_lists(d):
    """[(offset, [(record offset, REC tuple)..])] for the caption lists (after each 0xFFFF: a 10-12 byte gap)."""
    out, o = [], CAP_LISTS[0]
    while o < CAP_LISTS[1]:
        start, cur = o, []
        while struct.unpack_from("<H", d, o)[0] != 0xFFFF:
            cur.append((o, struct.unpack_from(REC, d, o)))
            assert cur[-1][1][0] in CAP_BLK and cur[-1][1][1] in (0x7E80, 0x7E81), hex(o)
            o += 14
        out.append((start, cur))
        o += 2
        while o < CAP_LISTS[1] and not (struct.unpack_from("<H", d, o)[0] in CAP_BLK and
                                        struct.unpack_from("<H", d, o + 2)[0] in (0x7E80, 0x7E81)):
            o += 2
    return out


def cap_lines(recs):
    """The list's glyph records (h >= 30) grouped into lines by y, top line first."""
    lines = []
    for o, r in sorted([t for t in recs if t[1][5] >= 30], key=lambda t: t[1][7]):
        if lines and r[7] - lines[-1][0][1][7] <= 20:
            lines[-1].append((o, r))
        else:
            lines.append([(o, r)])
    return lines


def cap_layout():
    """{line text: (tpage, u, v, w)}: first fit, widest first, into CAP_H rows of the three blocks."""
    import gfx_gen
    free = [[tp, 0, v, 256] for tp in CAP_BLK for v in range(0, 256 - CAP_H + 1, CAP_H)]
    out = {}
    for t in sorted({t for _, en in CAP_EN for t in en}, key=lambda t: (-gfx_gen.line_width(t, CAP_SIZE), t)):
        w = gfx_gen.line_width(t, CAP_SIZE)
        f = next(f for f in free if f[3] >= w)  # StopIteration = atlas full
        out[t] = (f[0], f[1], f[2], w)
        f[1] += w
        f[3] -= w
    return out


def cap_recs(d):
    """gfx.RECS-style entries for the G6 captions, checked against the original SBTTL.BIN bytes `d`."""
    lay = cap_layout()
    lists = cap_lists(d)
    assert len(lists) == 2 * len(CAP_EN), len(lists)
    out = []
    for k, (start, recs) in enumerate(lists):
        jp, en = CAP_EN[k // 2]
        lines = cap_lines(recs)
        assert len(lines) == len(en), (jp, len(lines))
        lead = {}
        for i, (line, t) in enumerate(zip(lines, en)):
            o, r = min(line, key=lambda q: q[1][6])
            tp, u, v, w = lay[t]
            right = max(q[1][6] + q[1][4] for q in line)
            x = min(r[6], CAP_RIGHT - w) if i == 0 else min(right, CAP_RIGHT) - w  # later lines: JP right edge
            lead[o] = (tp, r[1], u, v, w, CAP_H, x, min(q[1][7] for q in line) + (40 - CAP_H) // 2)
        for o, r in recs:
            out.append((SBT, o, REC, r, lead.get(o, r[:4] + (0, 0) + r[6:]), "caption " + en[0]))
    return out


# G9 memory-card screen (PRG/MEM_01.CHG image block 0x2510 = tpages 0x0A-0x0E, CLUT raw at 0x2310 palette 13):
# PRG/MEMORY.BIN MEM_LISTS holds one sprite list per message (REC records, text CLUT 0x7C0D, box 0x7C0C; lists are
# runs of contiguous records). A message line is one atlas strip or pieces of several (メモリーカード + が + ...).
# English: one Spleen 6x12 strip per line (white 1, drop shadow 14 like the JP) packed into MEM_FREE; the line's
# leftmost record cuts it (centred lines stay centred), the others get w = h = 0. A record taller than 16 cuts a
# block of lines: its English lines are stacked at one u. はい / いいえ and the 第 話 frame are redrawn in place.
MEM = "PRG/MEMORY.BIN"
MEM_LISTS = (0x3BF4, 0x5470)
MEM_TEXT = 0x7C0D
MEM_FREE = ([(0x0A, 0, v, 256) for v in range(0, 256, 16)] + [(0x0B, 0, v, 152) for v in range(0, 48, 16)] +
            [(0x0B, 0, v, 256) for v in range(48, 256, 16)] + [(0x0C, 0, v, 176) for v in range(0, 64, 16)] +
            [(0x0C, 0, v, 256) for v in range(64, 256, 16)] + [(0x0E, 0, v, 256) for v in range(0, 176, 16) if v != 48] +
            [(0x0E, 72, 48, 184)] + [(0x0E, 128, v, 128) for v in range(176, 256, 16)])  # tp, u, v, w; 16 tall
MEM_RIGHT = 136  # right end of the widest JP line (0x5148: x -120, 256 wide)
MEM_INPLACE = [(0x0D, 216, 160, 32, "Yes", "c"), (0x0D, 176, 224, 48, "No", "c"),
               (0x0B, 152, 16, 48, "Ep.", 16)]  # tp, u, v, w, text, "c" = centred / n = right end at u + n
_MC = "the Memory Card"
MEM_EN = {  # list offset: (JP lines, English lines top to bottom; "" = line not drawn)
    0x3BF4: ("セーブ", ["Save"]), 0x3C20: ("ロード", ["Load"]), 0x3C4C: ("プロローグ", ["Prologue"]),
    0x3F88: ("もんじゃ村", ["Monja Village"]), 0x3FB4: ("コンビニ村", ["Konbini Village"]),
    0x3FE0: ("ガンボづくし村", ["Ganbozukushi Village"]), 0x400C: ("カネワローン", ["Kanewa Loans"]),
    0x4038: ("エキストラタウン", ["Extra Town"]), 0x4064: ("キャラクターシティ", ["Character City"]),
    0x4090: ("ケイコータウン", ["Keiko Town"]), 0x40BC: ("ビリビリタウン", ["Biribiri Town"]),
    0x40E8: ("アイドリアンシティ", ["Idorian City"]), 0x4114: ("下水道", ["Sewers"]),
    0x4140: ("サウンドエコー村", ["Sound Echo Village"]), 0x416C: ("ワルトリン城", ["Warutorin Castle"]),
    0x4198: ("アスリート村", ["Athlete Village"]), 0x41C4: ("アスレチック村", ["Athletic Village"]),
    0x41F0: ("ハナヨメ村", ["Bride Village"]), 0x421C: ("ハナヨメキャッスル", ["Bride Castle"]),
    0x4248: ("サビレータウン", ["Sabire Town"]), 0x4274: ("ワルジョの城", ["Warujo's Castle"]),
    0x42A0: ("魔神湯治場", ["Mashin Spa"]), 0x42CC: ("ムキリョク村", ["Mukiryoku Village"]),
    0x42F8: ("ワルモンダー城Ａ", ["Warumonder Castle A"]), 0x4324: ("ワルモンダー城 + Ｄ", ["Warumonder Castle D"]),
    0x4378: ("ファイル1", ["File 1"]), 0x4394: ("ファイル2", ["File 2"]), 0x43B0: ("ファイル3", ["File 3"]),
    0x43CC: ("ファイル4", ["File 4"]),
    0x4430: ("セーブするファイルを / 選んで下さい。", ["Select the file", "to save to."]),
    0x4478: ("セーブ中です。 / メモリーカードを / ぬかないで下さい。", ["Saving...", "Please do not remove", _MC + "."]),
    0x44CC: ("セーブを終了しました。", ["Save complete."]),
    0x4504: ("メモリーカードがいっぱいです。", ["The Memory Card is full."]),
    0x453C: ("不要なファイルを消してから / セーブして下さい。", ["Delete files you don't need,", "then save."]),
    0x4584: ("メモリーカードが / さしこまれていません。", ["No Memory Card", "is inserted."]),
    0x45CC: ("メモリーカードをさしてから / セーブして下さい。", ["Insert a Memory Card,", "then save."]),
    0x4614: ("ロードするファイルを / 選んで下さい。", ["Select the file", "to load."]),
    0x465C: ("ロード中です。 / メモリーカードを / ぬかないで下さい。", ["Loading...", "Please do not remove", _MC + "."]),
    0x46B0: ("ロードしました。", ["Load complete."]),
    0x46E8: ("メモリーカードが / さしこまれていません。", ["No Memory Card", "is inserted."]),
    0x4730: ("メモリーカードをさしてから / ロードして下さい。", ["Insert a Memory Card,", "then load."]),
    0x4778: ("メモリーカードがいっぱいです。 / このままつづけると / ゲーム中にセーブできません。",
             ["The Memory Card is full.", "If you go on, you won't be", "able to save in the game."]),
    0x47CC: ("メモリーカードに / 空きをつくってから / ゲームを立ちあげて下さい。",
             ["Make some room on", _MC + ", then", "restart the game."]),
    0x4874: ("炎部ワタル / 剣部アラゴト / 忍部サクヤ", ["Wataru", "Aragoto", "Sakuya"]),
    0x492A: ("炎部ワタル / ワルリーヌ / 忍部サクヤ", ["Wataru", "Warurine", "Sakuya"]),
    0x49E2: ("炎部ワタル / 剣部アラゴト / ワルリーヌ", ["Wataru", "Aragoto", "Warurine"]),
    0x4E70: ("メモリーカードが壊れています。 / 別のメモリーカードをセットして / ください。",
             ["The Memory Card is damaged.", "Please insert a different", "Memory Card."]),
    0x4EA8: ("メモリーカード + を / フォーマット + 中です。", ["Formatting", _MC + "..."]),
    0x4F0C: ("メモリーカード + を / チェック + 中です。", ["Checking", _MC + "..."]),
    0x4FA0: ("どのファイルにセーブしますか？", ["Which file do you want to save to?"]),
    0x4FD8: ("どのファイルをロードしますか？", ["Which file do you want to load?"]),
    0x5030: ("すでにメモリーカード上に / ファイルが存在します。", ["A file already exists", "on " + _MC + "."]),
    0x50A0: ("上書きしてよろしいですか？", ["Overwrite it?"]),
    0x50D8: ("メモリーカードがフォーマット / されていません。", ["The Memory Card", "is not formatted."]),
    0x5148: ("フォーマットしてよろしいですか？", ["Format it?"]),
    0x51B8: ("データの書き込みに失敗しました。 / もう１度セーブ + しますか？", ["Failed to save the data.", "Try saving again?"]),
    0x5244: ("データの + 読み + 込みに失敗しました。 / もう１度 + ロード + しますか？",
             ["Failed to load the data.", "Try loading again?"]),
    0x537C: ("メモリーカード + の + データ + が + 壊れています。 / データ + を + ロード + できません。",
             ["The data on " + _MC + " is damaged.", "It can't be loaded."]),
    0x5424: ("メモリーカード + の + データ + が + 壊れています。", ["The data on " + _MC + " is damaged."]),
}


def mem_lists(d):
    """{list offset: [(record offset, REC tuple)..]}: runs of contiguous memory-card sprite records."""
    out, o, start = {}, MEM_LISTS[0], None
    while o < MEM_LISTS[1]:
        r = struct.unpack_from(REC, d, o)
        if 0x0A <= r[0] <= 0x0E and r[1] in (0x7C0C, MEM_TEXT):
            if start is None:
                start = o
                out[o] = []
            out[start].append((o, r))
            o += 14
        else:
            start, o = None, o + 2
    return out


def mem_w(text):
    """Width put_bdf draws `text` at in Spleen 6x12 with the 1-px drop shadow."""
    return bdf_w(text) - 1


def bdf_w(text):
    import gfx_gen
    return gfx_gen.bdf_width(text)


def _mem_lines(recs):
    """Text records grouped by line (y), top first: [(y, [(offset, rec)..])]; a 32/48-tall record opens a block."""
    lines = {}
    for o, r in recs:
        if r[1] == MEM_TEXT:
            lines.setdefault(r[7], []).append((o, r))
    return sorted(lines.items())


def _mem_blocks(d):
    """[(list offset, [(lead record, English lines, centred)..])]: per line, or per block for a tall record."""
    lists = mem_lists(d)
    out = []
    for lo, (jp, en) in MEM_EN.items():
        lines = _mem_lines(lists[lo])
        n = sum(max(r[5] for _, r in ln) // 16 for _, ln in lines)
        assert n == len(en), (hex(lo), jp, n)
        k, items = 0, []
        for y, ln in lines:
            o, r = min(ln, key=lambda q: q[1][6])
            m = r[5] // 16
            assert m == 1 or len(ln) == 1, (hex(lo), "block shares its line")
            centred = len(lines) == 1 and len(ln) == 1 and abs(r[6] + r[4] // 2) <= 4
            items.append(((o, r), en[k:k + m], centred, ln))
            k += m
        out.append((lo, items))
    return out


def mem_layout(d):
    """{tuple of English lines: (tp, u, v, w)}: blocks (stacked lines) first, then single lines, widest first."""
    free = [list(f) for f in MEM_FREE]
    out = {}
    want = {tuple(t) for _, items in _mem_blocks(d) for _, t, _, _ in items if any(t)}
    for t in sorted(want, key=lambda t: (-len(t), -max(mem_w(s) for s in t if s), t)):
        w = max(mem_w(s) for s in t if s)
        for f in free:
            col = [next((g for g in free if g[0] == f[0] and g[1] == f[1] and g[2] == f[2] + 16 * i and g[3] >= w), None)
                   for i in range(len(t))]
            if all(col):
                break
        else:
            raise StopIteration("memory-card atlas full: " + str(t))
        out[t] = (f[0], f[1], f[2], w)
        for g in col:
            g[1] += w
            g[3] -= w
    return out


def mem_recs(d):
    """gfx.RECS-style entries for the G9 messages, checked against the original MEMORY.BIN bytes `d`."""
    lay = mem_layout(d)
    out = []
    for lo, items in _mem_blocks(d):
        for (lead, r), t, centred, ln in items:
            for o, q in ln:
                if o == lead and any(t):
                    tp, u, v, w = lay[tuple(t)]
                    x = -(w // 2) if centred else r[6] + 4 * (r[6] == -120)  # box lines: off the border
                    assert x + w <= MEM_RIGHT, (t, x, w)
                    new = (tp, q[1], u, v, w, 16 * len(t), x, q[7])
                else:
                    new = q[:4] + (0, 0) + q[6:]
                out.append((MEM, o, REC, q, new, "memcard " + (t[0] or "-")))
    return out


def mem_check(d):
    """No record left alone (or any other text record in MEMORY.BIN) cuts a freed atlas row."""
    done = {o for _, o, *_ in mem_recs(d)}
    for o in range(0, len(d) - 13, 2):
        r = struct.unpack_from(REC, d, o)
        if o in done or not (0x0A <= r[0] <= 0x0E and r[1] == MEM_TEXT and r[4] and r[5]):
            continue
        for tp, u, v, w in MEM_FREE:
            assert not (r[0] == tp and r[2] < u + w and u < r[2] + r[4] and r[3] < v + 16 and v < r[3] + r[5]), \
                (hex(o), r)


def rows():
    out = []
    for line in (GFX / "gfx.tsv").read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        png, path, off, bpp, cpath, coff, pal, rect = line.split("\t")[:8]
        coff = -int(coff[1:], 16) - 1 if coff.startswith("r") else int(coff, 16)  # rHEX: raw colours, "-": GREY
        out.append(dict(png=png, path=path, off=int(off, 16), bpp=int(bpp), cpath=cpath, coff=coff,
                        pal=int(pal), rect=tuple(int(v) for v in rect.split(","))))
    return out


def palette(d, coff, pal, bpp):
    """CLUT upload block at coff (16 palettes per 256-wide row), or raw colours when coff < 0 (at -coff - 1:
    YM/BR_17/OTHER*.CHG keep theirs in the 0xC00-byte header)."""
    n = 16 if bpp == 4 else 256
    if coff < 0:
        return _cols(struct.unpack_from(f"<{n}H", d, -coff - 1 + pal * 2 * n))
    w = struct.unpack_from("<H", d, coff + 4)[0]
    cols = struct.unpack_from(f"<{n}H", d, coff + 8 + pal * 32 * (bpp == 4))
    assert pal * n + n <= w or bpp == 8, "palette past the CLUT row"
    return _cols(cols)


GREY = [MAGENTA] + [(i * 17,) * 3 for i in range(1, 16)]  # clut file "-": room textures (G22), CLUT set per poly


def row_lut(r, data_of=None):
    """Row r's palette; data_of(path) -> file bytes (default: the extracted original)."""
    if r["cpath"] == "-":
        return GREY
    return palette((data_of or load)(r["cpath"]), r["coff"], r["pal"], r["bpp"])


def _cols(cols):
    return [MAGENTA if c == 0 else ((c & 31) * 255 // 31, (c >> 5 & 31) * 255 // 31, (c >> 10 & 31) * 255 // 31)
            for c in cols]


def _geom(d, off, bpp):
    x, y, w, h = struct.unpack_from("<4H", d, off)
    return w * 2 * (2 if bpp == 4 else 1), h  # pixel width, height


def get_px(d, off, bpp, px, py):
    pw, _ = _geom(d, off, bpp)
    if bpp == 8:
        return d[off + 8 + py * pw + px]
    b = d[off + 8 + py * pw // 2 + px // 2]
    return b >> 4 if px & 1 else b & 15


def set_px(buf, off, bpp, px, py, v):
    pw, _ = _geom(buf, off, bpp)
    if bpp == 8:
        buf[off + 8 + py * pw + px] = v
        return
    k = off + 8 + py * pw // 2 + px // 2
    buf[k] = (buf[k] & 0x0F | v << 4) if px & 1 else (buf[k] & 0xF0 | v)


def image(d, off, bpp, lut, rect=None):
    pw, ph = _geom(d, off, bpp)
    x0, y0, w, h = rect or (0, 0, pw, ph)
    im = Image.new("RGB", (w, h))
    im.putdata([lut[get_px(d, off, bpp, x0 + i, y0 + j)] for j in range(h) for i in range(w)])
    return im


def load(path, cache={}):
    if path not in cache:
        cache[path] = (TREE / path).read_bytes()
    return cache[path]


def export(only=()):
    for r in rows():
        if only and r["png"] not in only:
            continue
        d = load(r["path"])
        im = image(d, r["off"], r["bpp"], row_lut(r), r["rect"])
        for sub in ("orig", "en"):
            p = GFX / sub / r["png"]
            if sub == "orig" or not p.exists():
                p.parent.mkdir(parents=True, exist_ok=True)
                im.save(p)
        print(r["png"], r["path"], hex(r["off"]), r["rect"])


def indices(r, d, lut):
    """Palette indices of gfx/en/<png> for row r (ValueError on a colour outside the palette)."""
    im = Image.open(GFX / "en" / r["png"]).convert("RGB")
    x0, y0, w, h = r["rect"]
    assert im.size == (w, h), (r["png"], im.size, (w, h))
    first = {}
    for i, c in enumerate(lut):
        if c != MAGENTA or i == 0:
            first.setdefault(c, i)
    out = {}
    px = im.load()
    for j in range(h):
        for i in range(w):
            c = px[i, j]
            o = get_px(d, r["off"], r["bpp"], x0 + i, y0 + j)
            if lut[o] == c:
                continue
            if c not in first:
                raise ValueError(f"{r['png']} ({i},{j}): colour {c} not in palette {r['pal']}")
            out[(x0 + i, y0 + j)] = first[c]
    return out


def apply(put, bufs, orig, load_path):
    """Write every gfx.tsv row through insert.put(); one put per changed byte run."""
    for r in rows():
        p = load_path(r["path"])
        d = orig[p]
        buf = bytearray(bufs.get(p, d))
        lut = row_lut(r, lambda c: orig[load_path(c)])
        for (x, y), v in indices(r, d, lut).items():
            set_px(buf, r["off"], r["bpp"], x, y, v)
        cur = bufs.get(p, d)
        k, n = 0, len(buf)
        while k < n:
            if buf[k] == cur[k]:
                k += 1
                continue
            e = k
            while e < n and buf[e] != cur[e]:
                e += 1
            put(bufs, orig, p, k, bytes(buf[k:e]), "gfx " + r["png"])
            k = e
    sb = orig[load_path(SBT)]
    for path, off, fmt, old, new, why in (RECS + fm_recs(orig[load_path(FDS)]) + sbt_recs(sb) + cap_recs(sb) +
                                          mem_recs(orig[load_path(MEM)])):
        p = load_path(path)
        assert struct.unpack_from(fmt, orig[p], off) == old, (path, hex(off), why)
        put(bufs, orig, p, off, struct.pack(fmt, *new), "gfx rec " + why)
    import staff  # G25 staff roll: cell list, tile map and glyph image rebuilt from gfx/staff_en.txt
    p = load_path(staff.PATH)
    for off, data in staff.writes(orig[p]):
        put(bufs, orig, p, off, data, "gfx staff roll")


def spans(path):
    """Byte spans gfx.tsv rows may write in `path` (test_insert allowed_spans)."""
    out = []
    for r in rows():
        if r["path"] != path:
            continue
        d = load(path)
        pw, _ = _geom(d, r["off"], r["bpp"])
        x0, y0, w, h = r["rect"]
        bpr = pw if r["bpp"] == 8 else pw // 2
        for y in range(y0, y0 + h):
            a = r["off"] + 8 + y * bpr + (x0 if r["bpp"] == 8 else x0 // 2)
            out.append((a, a + (w if r["bpp"] == 8 else (w + 2) // 2)))
    out += [(off, off + struct.calcsize(fmt)) for p, off, fmt, *_ in RECS + fm_recs(load(FDS)) + sbt_recs(load(SBT))
            + cap_recs(load(SBT)) + mem_recs(load(MEM)) if p == path]
    import staff
    return out + (staff.spans() if path == staff.PATH else [])


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "export":
        export(set(a[1:]))
    elif a and a[0] == "show":
        f, off, bpp, cf, coff, pal, out = a[1:8]
        coff = -int(coff[1:], 16) - 1 if coff.startswith("r") else int(coff, 16)
        image(load(f), int(off, 16), int(bpp), palette(load(cf), coff, int(pal), int(bpp))).save(out)
    else:
        print(__doc__)
