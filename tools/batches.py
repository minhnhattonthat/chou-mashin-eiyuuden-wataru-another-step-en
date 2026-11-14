"""Translation batches (docs/translator-brief.md): split untranslated text, check translator output, merge it back.

    python -X utf8 tools/batches.py split [--size 3500]   work/tl/bNNN.tsv and build/terms_bNNN.txt for untranslated JP
    python -X utf8 tools/batches.py check [bNNN ...]      a batch's .out.tsv; with no batch, all shipped English (for check.py)
    python -X utf8 tools/batches.py merge bNNN ... [--overwrite]   check, then write the English into script/
    python -X utf8 tools/batches.py terms                 rewrite every build/terms_bNNN.txt after the glossary grew
    python -X utf8 tools/batches.py pairs bNNN ...        work/tl/bNNN.pairs.txt for the reviewer
Limits per entry: box() (docs/re/windows.md). Runs: tools/tl_codex.py (codex exec, prompt-only).

Copied from the skill's assets/batches.py. Fit the ADAPTER section to this game's text format; the rest is shared.
Batch TSV: id, speaker, form, limit, JP. Output: work/tl/bNNN.out.tsv, id<TAB>English, every id once, same order.
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TL = ROOT / "work/tl"
SCRIPT = ROOT / "script"
GLOSSARY = ROOT / "glossary.md"
MAX_ENTRIES = 150

# ---- ADAPTER: this game's text format ----
# The only control inside text is `B000 n` (extract shows its argument as a glyph: [B000]の); keep it verbatim.
# [XXXX:g] (duplicate glyph) and bare [01AF] (room-font kanji borrowed by menus) are glyphs, shown as text.
TOKEN = re.compile(r"\[B000\]")  # the translator writes [B000] alone; merge appends the arg word as [XXXX]
FREE = set()
VARIABLE = r"\[var[^\]]*\]"  # no drawn-number placeholders in this game's script
HONORIFICS = {"くん": "-kun", "さん": "-san", "さま": "-sama", "様": "-sama", "ちゃん": "-chan", "殿": "-dono"}  # D1, after a name
NAME_CH = "ァ-ヶーＡ-Ｚ"  # a honorific counts only right after a katakana name (not おじさん, 貴様, 皆さん, 母さん)
NOT_NAMES = r"(ゴクロー|ゴクロウ|オツカレ|ジイ|バア|バー|コンビニ|オニ|トリ)(さん|さま|様|ちゃん)"  # set phrases, not names
LIMITS = "docs/re/windows.md"  # letters per line (two per 16x16 cell, D8) and lines per box


def docs():
    """(path, doc, entries) per script file; entries hold id, jp, en, and optionally speaker, box, max, dup."""
    for path in sorted(SCRIPT.rglob("*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        yield path, doc, doc["entries"] if isinstance(doc, dict) else doc


def needs_english(entry):
    """Empty JP isn't "untranslated": it would be re-queued forever. Blank-only cells and not-text ids aren't text."""
    return bool(entry.get("jp", "").strip("　\n")) and not entry.get("en") and entry["id"] not in NOT_TEXT


_group = [None]


def group_of(entry):
    """A dialogue chain (a page and the `next` pages after it) stays in one batch."""
    if entry.get("kind") != "next" or _group[0] is None:
        _group[0] = entry["id"]
    return _group[0]


def box(entry):
    """(letters per line, lines, form) from docs/re/windows.md."""
    src, off = entry["id"].split(":")
    kind = entry.get("kind")
    if "slot" in entry:  # fixed-width field: `max` cells
        if src == "EXE" and 0x80094 <= int(off, 16) < 0x801AC:  # もんペット attack names: one letter per cell
            return entry["max"], 1, "name"
        if (src == "EXE" and 0x7D7C0 <= int(off, 16) < 0x7DC7C) or (src == "FDS" and int(off, 16) >= 0x18550):
            # item effect blurbs and the config voice lines: text, not names
            return 2 * entry["max"], 1, "menu"
        return 2 * entry["max"], 1, "name" if entry["max"] <= 10 else "menu"
    if kind == "bname":
        return 11, 1, "name"
    if kind == "ename":
        return 2 * entry["max"], 1, "name"
    if kind == "bfont":
        return 11, 1, "name"
    if src == "BALLBAT":
        return 32, 1, "menu"
    if src == "MACHINE":
        o = int(off, 16)
        return (16 if 0x10398 <= o < 0x103CC else 26), 1, "menu" if o >= 0x103CC else "name"  # 経験値/を手に入れた
    if src == "TTL":
        # labels x 8 -> value column x 112: 13 letters (the 7th cell's right half is blank); values keep 24
        return (13 if int(off, 16) < 0x05528 else 24), 1, "menu"
    if src == "LVUP":
        return 30, 4, "menu"
    return 32, 3, "choice" if "\n　" in entry["jp"] else "dlg"


def limit_label(entry):
    w, n, _ = box(entry)
    return f"{w}x{n}"


def show(jp):
    """JP as the translator sees it: duplicate glyphs as plain text, newlines as a literal \\n."""
    jp = re.sub(r"\[B000\].", "[B000]", jp)  # its arg word is not text
    return re.sub(r"\[[0-9A-F]{4}:(.)\]", r"\1", jp).replace("\n", "\\n")


def speaker(jp):
    first = TOKEN.sub("", show(jp)).split("\\n")[0]
    return first[:-1].strip("　") if "\\n" in show(jp) and first.endswith("：") else ""


def speakers():
    """{JP speaker: EN} from glossary.md's ## Speakers table (exact match required on the speaker line)."""
    out, on = {}, False
    for line in GLOSSARY.read_text(encoding="utf-8").splitlines() if GLOSSARY.exists() else []:
        if line.startswith("## "):
            on = line.strip() == "## Speakers"
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if on and line.startswith("|") and len(cells) >= 2 and cells[0] != "JP" and not set(cells[0]) <= set("-: "):
            out[cells[0]] = cells[1]
    return out


CENTRED = {"FDS:12510"}  # item-order title box "Done": JP blanks centre 決定, not cursor cells


def width_problems(entry, en):
    w, n, _ = box(entry)
    jp_lines = re.sub(r"\[B000\].", "", entry["jp"]).split("\n")
    lines = re.sub(r"\[B000\](\[[0-9A-F]{4}\])?", "", en)
    lines = re.sub(r"\[[0-9A-F]{4}\]", "  ", lines).split("\n")  # any other raw word takes one cell (a terminator)
    out = []
    if len(lines) > n:
        out.append(f"{len(lines)} lines, the box has {n}")
    out += [f"line {k + 1} is {len(s)} letters, limit {w}" for k, s in enumerate(lines) if len(s) > w]
    # cursor indents (choices): same lines, 2 spaces per blank cell; CENTRED ids pad to centre a title (inkbox.py)
    if any(s.startswith("　") for s in jp_lines) and entry["id"] not in CENTRED:
        if len(lines) != len(jp_lines):
            out.append(f"choice layout: JP has {len(jp_lines)} lines, keep them")
        else:
            for k, (j, s) in enumerate(zip(jp_lines, lines)):
                ind = 2 * (len(j) - len(j.lstrip("　")))
                if ind and (len(s) - len(s.lstrip(" ")) != ind):
                    out.append(f"line {k + 1} must start with {ind} spaces (cursor cells)")
    if entry["id"] in fixed_slots():  # can't grow: ST stack buffers, code-built room blocks, fixed fields
        avail, nl, ctx = fixed_slots()[entry["id"]]
        k = len(en) if ctx == "BF" else len(_insert().cells(en, nl))
        if k > avail:
            unit = "letters" if ctx == "BF" else ("cells (a cell = 2 letters of one line, each line break is a "
                                                   "cell)")
            out.append(f"too long for its slot: {k} {unit}, room for {avail}: cut {k - avail}")
    sp = speaker(entry["jp"])
    body = lines[1:] if sp else lines
    if box(entry)[2] == "dlg" and len(body) >= 2 and len(body[-1].strip()) < 6 and \
            not re.match(r"\d\. ", body[-1].strip()) and not re.search(r"[.!?\"')~-]$", body[-2].rstrip()):  # a sentence's tail on its own line ("idol,\nMeg!")
        out.append(f"stub last line {body[-1].strip()!r}: rewrap so it carries 6+ letters")
    if sp:
        want = SPEAKERS.get(sp)
        if want and lines[0].strip() != want + ":":
            out.append(f"speaker line must be {want + ':'!r}")
        elif not lines[0].endswith(":"):
            out.append("first line is the speaker: end it with ':'")
    return out


def _insert():
    sys.path.insert(0, str(ROOT / "tools"))
    import insert
    return insert


_FIXED = {}


def fixed_slots():
    """{id: (JP slot words, newline word, context)} for every entry insert can't move or grow (its overflow rule);
    bname is left to insert (it may start in the ename slack before it)."""
    if not _FIXED:
        ins = _insert()
        _FIXED.update({e["id"]: (avail, nl, ctx) for e, path, off, w, avail, nl, ctx in ins.entries()
                       if e.get("kind") != "bname" and not ins.relocatable(path, off) and not ins.movable(e, path)})
    return _FIXED


def encodable(char):
    return " " <= char <= "~"


NOT_TEXT = {ln.split()[0] for ln in (ROOT / "tbl/not_text.txt").read_text(encoding="utf-8").splitlines()
            if ln.split("#")[0].strip()} if (ROOT / "tbl/not_text.txt").exists() else set()


def b000_args():
    """{id: [arg word of each B000]} from the original words (insert.entries)."""
    sys.path.insert(0, str(ROOT / "tools"))
    import insert
    return {e["id"]: [w[i + 1] for i in range(len(w) - 1) if w[i] == 0xB000]
            for e, _, _, w, *_ in insert.entries() if "[B000]" in e["jp"]}
SPEAKERS = speakers()
# ---- end of ADAPTER ----


def kind(char):
    if "぀" <= char <= "ゟ":
        return "hiragana"
    if "゠" <= char <= "ヿ":
        return "katakana"
    if "一" <= char <= "鿿" or char == "々":
        return "kanji"
    return "other"


def has_term(jp, term):
    """term occurs as a whole kana or kanji run: ミン isn't in タイミング, くも isn't in ぼくも."""
    for m in re.finditer(re.escape(term), jp):
        a, b = m.start(), m.end()
        if (a == 0 or kind(jp[a - 1]) != kind(term[0])) and (b == len(jp) or kind(jp[b]) != kind(term[-1])):
            return True
    return False


def glossary():
    """[(JP forms, EN forms, avoid forms)] from glossary.md's | JP | EN | max | notes | Avoid | tables."""
    rows = []
    if not GLOSSARY.exists():
        return rows
    for line in GLOSSARY.read_text(encoding="utf-8").splitlines():
        if line.strip() == "## Speakers":  # speaker labels are matched on the speaker line only (speakers())
            break
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if line.startswith("|") and len(cells) >= 2 and cells[0] not in ("JP", "") and not set(cells[0]) <= set("-: "):
            avoid = [x.strip() for x in cells[4].split("/") if x.strip()] if len(cells) > 4 else []
            rows.append(([x.strip() for x in cells[0].split("/")], [x.strip() for x in cells[1].split("/")], avoid))
    return rows


def problems(entry, en, terms):
    """Every rule, on one line of English."""
    jp = entry["jp"]
    if en == " " and jp in ("は", "を", "が", "に"):  # a particle fragment between a name and a verb: just the gap
        return []
    if not en.strip():
        return ["empty English"]
    out = []
    plain = TOKEN.sub("", en)
    if bad := sorted({c for c in plain if not encodable(c) and c != "\n"}):
        out.append(f"unencodable characters {bad}")
    if re.search(r"\\u[0-9a-fA-F]{4}", en) or "\t" in en:
        out.append("escape sequence or tab in the English")
    want = Counter(t for t in TOKEN.findall(jp) if t not in FREE)
    have = Counter(t for t in TOKEN.findall(en) if t not in FREE)
    plain = re.sub(r"\[[0-9A-F]{4}\]", "", plain)  # merged B000 args
    if want != have:
        out.append(f"control codes differ: JP {dict(want)} EN {dict(have)}")
    if re.search(VARIABLE + r"(st|nd|rd|th)\b", en):
        out.append('ordinal suffix after a variable (write "No. [var]")')
    jp_plain = TOKEN.sub("", jp).replace("\n", "")  # a word may wrap mid-word (この世/界): 界 alone isn't a term
    en_flat = " ".join(en.lower().split())  # an English term may wrap across lines too
    for jps, ens, avoid in terms:
        if any(has_term(jp_plain, j) for j in jps) and not any(e.lower() in en_flat for e in ens):
            out.append(f"glossary: {jps[0]} -> {ens[0]}")
        out += [f"glossary Avoid: {a}" for a in avoid if re.search(rf"\b{re.escape(a)}\b", en)]
    kin = "Father|Mother|Sisters?|Brothers?|Grand(?:mother|father)|Uncle|Aunt|Chief|Birdie|Lady|Bride|God|Granny"
    for m in re.finditer(rf"\b([a-z][a-z']{{2,}}|{kin})-(san|sama|chan|kun)\b", en):  # "bride-san", "Father-sama"
        if m[1] != "chan":  # cha-cha chan-chan (music)
            out.append(f"honorific on a common noun: {m[0]} (names only)")
    jp_names = re.sub(NOT_NAMES, "", jp_plain)
    for jp_form, en_form in HONORIFICS.items():
        if re.search(f"[{NAME_CH}]{jp_form}", jp_names) and en_form.lower() not in en.lower():
            out.append(f"honorific {jp_form} needs {en_form}")
    return out + width_problems(entry, en)


def index():
    return {e["id"]: e for _, _, entries in docs() for e in entries}


def read_tsv(path):
    return [line.split("\t") for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def existing():
    return sorted(TL.glob("b[0-9][0-9][0-9].tsv"))


def split(size):
    """Numbers on from the last batch and leaves out ids already batched, so a repeat run can't duplicate work."""
    TL.mkdir(parents=True, exist_ok=True)
    (ROOT / "build").mkdir(exist_ok=True)
    taken = {r[0] for p in existing() for r in read_tsv(p)}
    n = max((int(p.stem[1:]) for p in existing()), default=0)
    groups = {}
    for _, _, entries in docs():
        for e in entries:
            if needs_english(e) and e["id"] not in taken:
                groups.setdefault(group_of(e), []).append(e)
    batches, cur, chars = [], [], 0
    for group in groups.values():
        c = sum(len(TOKEN.sub("", e["jp"])) for e in group)
        if cur and (chars + c > size or len(cur) + len(group) > MAX_ENTRIES):
            batches.append(cur)
            cur, chars = [], 0
        cur += group
        chars += c
    if cur:
        batches.append(cur)
    terms = glossary()
    for batch in batches:
        n += 1
        name = f"b{n:03d}"
        path = TL / f"{name}.tsv"
        if path.exists():
            sys.exit(f"{path} already exists")
        rows, sp = [], ""
        for e in batch:  # a page without a speaker line continues the previous page's speaker (a hint only)
            sp = speaker(e["jp"]) or (sp if box(e)[2] in ("dlg", "choice") else "")
            rows.append(f"{e['id']}\t{sp}\t{box(e)[2]}\t{limit_label(e)}\t{show(e['jp'])}")
        path.write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")
        write_terms(name, batch, terms)
    print(f"{len(batches)} new batches in {TL}, {len(taken)} ids already batched")


def write_terms(name, batch, terms):
    """build/terms_<batch>.txt: the glossary rows (and speakers) whose JP occurs in the batch."""
    jps = " ".join(TOKEN.sub("", e["jp"]) for e in batch)
    used = [(j, " / ".join(ens), "Avoid: " + " / ".join(av) if av else "") for jpl, ens, av in terms for j in jpl
            if has_term(jps, j)]
    sps = {speaker(e["jp"]) for e in batch} & set(SPEAKERS)
    out = "".join(f"{j}\t{e}\t{a}\n" for j, e, a in used) + "".join(f"speaker {s}\t{SPEAKERS[s]}:\n" for s in sorted(sps))
    (ROOT / f"build/terms_{name}.txt").write_text(out or "(no glossary terms in this batch)\n", encoding="utf-8",
                                                  newline="\n")


def terms_all():
    """Rewrite every batch's term list after the glossary grew (between waves)."""
    ix, terms = index(), glossary()
    for p in existing():
        write_terms(p.stem, [ix[r[0]] for r in read_tsv(p)], terms)
    print(f"terms rewritten for {len(existing())} batches")


def check_batch(batch, entries, terms):
    want = [r[0] for r in read_tsv(TL / f"{batch}.tsv")]
    rows = [(r[0], "\t".join(r[1:]).replace("\\n", "\n")) for r in read_tsv(TL / f"{batch}.out.tsv")]
    bad = []
    if [r[0] for r in rows] != want:
        got = [r[0] for r in rows]
        dup = sorted(i for i, c in Counter(got).items() if c > 1)
        bad.append(f"ids differ: missing {sorted(set(want) - set(got))[:8]} extra {sorted(set(got) - set(want))[:8]} "
                   f"duplicate {dup[:8]} (order must match too)")
    for eid, en in rows:
        if eid in entries:
            bad += [f"{eid}: {p}: {en!r}" for p in problems(entries[eid], en, terms)]
    return bad, dict(rows)


def merge(new, overwrite):
    """Refuses to replace different English unless told to, before anything is written."""
    if not overwrite:
        for _, _, entries in docs():
            for e in entries:
                if e["id"] in new and e.get("en") and e["en"] != new[e["id"]]:
                    sys.exit(f"{e['id']} would lose {e['en']!r}: pass --overwrite if that is meant")
    changed = 0
    if any("[B000]" in en for en in new.values()):  # the translator writes [B000]; the game needs its arg word
        args = b000_args()
        for i, en in new.items():
            if "[B000]" in en and "[B000][" not in en:
                it = iter(args[i])
                new[i] = re.sub(r"\[B000\]", lambda m: "[B000][%04X]" % next(it), en)
    for path, doc, entries in docs():
        touched = False
        for e in entries:
            if e["id"] in new and e.get("en") != new[e["id"]]:
                e["en"], e["status"] = new[e["id"]], "done"
                touched = True
                changed += 1
        if touched:
            path.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"merged: {changed} entries changed")


def main(argv):
    if not argv:
        sys.exit(__doc__)
    cmd, args = argv[0], argv[1:]
    if cmd == "split":
        return split(int(args[args.index("--size") + 1]) if "--size" in args else 3500)
    if cmd == "terms":
        return terms_all()
    if cmd == "pairs":  # reviewer input: work/tl/bNNN.pairs.txt from the batch and its .out.tsv
        ix = index()  # JP from script/, not the batch TSV: a fixed kanji reading must reach the reviewer
        for name in args:
            out = {r[0]: "\t".join(r[1:]) for r in read_tsv(TL / f"{name}.out.tsv")}
            (TL / f"{name}.pairs.txt").write_text("".join(
                f">> {r[0]} | {r[1]} | {ix[r[0]]['jp'].replace(chr(10), chr(92) + 'n')}\n   {out.get(r[0], '(missing)')}\n"
                for r in read_tsv(TL / f"{name}.tsv")),
                encoding="utf-8")
        return 0
    overwrite = "--overwrite" in args
    names = [a for a in args if a != "--overwrite"]
    entries, terms = index(), glossary()
    if cmd == "check" and not names:
        bad = [f"{i}: {p}: {e['en']!r}" for i, e in entries.items() if e.get("en") for p in problems(e, e["en"], terms)]
        bad += [f"{i}: untranslated" for i, e in entries.items() if needs_english(e)]  # phase 6 done: all text has en
        print(f"{len(entries)} entries, {len(bad)} problems")
        print("\n".join(bad[:200]))
        return 1 if bad else 0
    if cmd not in ("check", "merge") or not names:
        sys.exit(__doc__)
    new, failed = {}, 0
    for batch in names:
        bad, rows = check_batch(batch, entries, terms)
        new.update(rows)
        failed += bool(bad)
        print(f"{batch}: " + ("OK" if not bad else f"{len(bad)} problems"))
        for line in bad:
            print("  " + line)
    if failed:
        return 1
    if cmd == "merge":
        merge(new, overwrite)
    return 0


def _selftest():
    import tempfile
    global ROOT, TL, SCRIPT, GLOSSARY
    with tempfile.TemporaryDirectory() as d:
        ROOT = Path(d)
        TL, SCRIPT, GLOSSARY = ROOT / "work/tl", ROOT / "script", ROOT / "glossary.md"
        SCRIPT.mkdir()
        GLOSSARY.write_text("| JP | EN | max | notes | Avoid |\n|---|---|---|---|---|\n| ミン | Min | | | Minn |\n", encoding="utf-8")
        script = {"entries": [
            {"id": "R01:00001", "jp": "ミンが来た", "en": ""}, {"id": "R01:00002", "jp": "タイミング", "en": ""},
            {"id": "R01:00003", "jp": "　", "en": ""}, {"id": "ST:00004", "jp": "ミンくん\n　はい\n　いいえ", "en": ""}]}
        (SCRIPT / "s.json").write_text(json.dumps(script), encoding="utf-8")
        a, b, d = "R01:00001", "R01:00002", "ST:00004"
        assert main(["split"]) is None
        assert [r[0] for r in read_tsv(TL / "b001.tsv")] == [a, b, d]  # blank-only JP isn't text
        assert "ミン\tMin" in (ROOT / "build/terms_b001.txt").read_text(encoding="utf-8")
        assert read_tsv(TL / "b001.tsv")[2][4] == "ミンくん\\n　はい\\n　いいえ"  # newlines shown as \n
        split(3500)
        assert len(existing()) == 1  # a repeat run makes no duplicate batch
        out = TL / "b001.out.tsv"
        out.write_text(f"{a}\tHe came\n{b}\tTiming\n", encoding="utf-8")
        assert main(["check", "b001"]) == 1  # d missing, a lacks the glossary term
        out.write_text(f"{a}\tMin came\n{b}\tTiming\n{d}\tMin\\n  Yes\\n  No\n", encoding="utf-8")
        assert main(["merge", "b001"]) == 1  # くん after a name needs -kun: nothing written
        assert index()[a]["en"] == ""
        out.write_text(f"{a}\tMin came\n{b}\tTiming\n{d}\tMin-kun\\n Yes\\n  No\n", encoding="utf-8")
        assert main(["check", "b001"]) == 1  # cursor indent: one blank cell = two spaces
        out.write_text(f"{a}\tMinn and Min came\n{b}\tTiming\n{d}\tMin-kun\\n  Yes\\n  No\n", encoding="utf-8")
        assert main(["check", "b001"]) == 1  # the Avoid spelling
        out.write_text(f"{a}\tMin and his bride-san came\n{b}\tTiming\n{d}\tMin-kun\\n  Yes\\n  No\n", encoding="utf-8")
        assert main(["check", "b001"]) == 1  # honorific on a common noun
        out.write_text(f"{a}\tMin came\n{b}\tThe timing is a very long line, way past the box\n{d}\tMin-kun\\n  Yes\\n  No\n",
                       encoding="utf-8")
        assert main(["check", "b001"]) == 1  # 32 letters per line
        out.write_text(f"{a}\tMin came\n{b}\tThe timing\n{d}\tMin-kun\\n  Yes\\n  No\n", encoding="utf-8")
        assert main(["merge", "b001"]) == 0 and index()[b]["en"] == "The timing"
        assert index()[d]["en"] == "Min-kun\n  Yes\n  No"
        assert main(["check"]) == 0
        out.write_text(f"{a}\tMin arrived\n{b}\tThe timing\n{d}\tMin-kun\\n  Yes\\n  No\n", encoding="utf-8")
        try:
            main(["merge", "b001"])
            raise AssertionError("merge replaced English")
        except SystemExit:
            pass
        assert main(["merge", "b001", "--overwrite"]) == 0 and index()[a]["en"] == "Min arrived"
    print("selftest ok")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    if sys.argv[1:] == ["--selftest"]:
        _selftest()
    else:
        sys.exit(main(sys.argv[1:]))
