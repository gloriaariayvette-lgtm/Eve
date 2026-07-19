#!/usr/bin/env python3
"""velqan_gapfill.py — guarantee both beings have the COMPLETE canonical Velqan. READ-ONLY unless --apply.

Gloria's canonical PDF is the authoritative source of the language (full grammar + ~200 base words).
The hand-copied reference in each tree may be incomplete ("Claude was funky when I asked him to copy it in").
This script, non-destructively:

  1. Installs the canonical guide verbatim at  <tree>/memory/velqan/canonical-guide.md  in BOTH trees —
     a guaranteed-complete source of grammar + every base word, alongside (not replacing) their reference.
  2. Reports which canonical CONTENT/FUNCTION words are absent from each being's own knowledge
     (velqan-reference.md + velqan/full-lexicon.md combined); with --apply, appends only the truly-missing
     ones to full-lexicon.md under a clearly-marked section (the coiner builds from full-lexicon).
  3. Reports each reference's GRAMMAR coverage (tense/aspect/mood/plural/definite/derivation markers) so
     we can SEE whether the hand-copied grammar is complete — the guide now backstops any gaps regardless.

Grammar/base already present is never overwritten. Coined-word layers are untouched.

RUN:
  python3 velqan_gapfill.py            # DRY RUN — report + preview; writes nothing
  python3 velqan_gapfill.py --apply    # installs guide + appends missing words (backs up first)
"""
import os, re, sys, urllib.request, datetime

APPLY = "--apply" in sys.argv
HOME = os.path.expanduser("~")
TS = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
BACKUP = os.path.join(HOME, ".velqan-backups", TS + "-gapfill")

GUIDE_URL = ("https://raw.githubusercontent.com/gloriaariayvette-lgtm/Eve/"
             "claude/chat-path-connection-errors-stgozf/velqan-canonical-guide.md")

TREES = {
    "Vintos":  os.path.join(HOME, ".vintos/workspace/memory"),
    "Velaris": os.path.join(HOME, ".openclaw/workspace/memory"),
}

VELQAN = re.compile(r"^(ne-)?[a-zāēīōū][a-zāēīōū'\-]{1,15}$")
DERIV = re.compile(r'\b(from|add|derived)\b', re.I)
TOKEN = re.compile(r"[a-zāēīōū][a-zāēīōū'\-]{1,15}")

def rd(p):
    try:
        return open(p, encoding="utf-8", errors="ignore").read()
    except Exception:
        return None

def fetch_guide():
    try:
        with urllib.request.urlopen(GUIDE_URL, timeout=30) as r:
            return r.read().decode("utf-8", "ignore")
    except Exception as e:
        print("!! could not fetch canonical guide:", e)
        return None

def parse_canon(guide):
    """Words from the vocab regions of the canonical guide: 'word - gloss' / 'word (gloss)'."""
    def region(a, b):
        i = guide.find(a); j = guide.find(b, i + 1) if i >= 0 else -1
        return guide[i:j] if i >= 0 and j >= 0 else ""
    vocab = (region("4. Core Vocabulary", "5. Example Sentences") + "\n"
             + region("10. Additional Vocabulary", "Ne-thira qethilil") + "\n"
             + region("Common Adverbs", "3. Syntax"))
    canon = {}
    NOISE = {"adjectives", "nouns", "pronouns", "numbers"}
    for l in vocab.splitlines():
        l = l.strip()
        m = re.match(r"^([A-Za-zāēīōū'\-]{2,16})\s*[-–]\s*(.+)$", l) or \
            re.match(r"^([A-Za-zāēīōū'\-]{2,16})\s*\((.+)\)\s*$", l)
        if not m:
            continue
        w, g = m.group(1).lower(), m.group(2).strip()
        if not VELQAN.match(w) or w in NOISE:
            continue
        if "-" in w and DERIV.search(g):     # skip derivation examples (skriv-or, sylk-eso...)
            continue
        canon.setdefault(w, g)
    return canon

def backup_then_write(path, old, new):
    if not APPLY:
        return
    rel = os.path.relpath(path, HOME)
    bp = os.path.join(BACKUP, rel)
    os.makedirs(os.path.dirname(bp), exist_ok=True)
    if old is not None:
        open(bp, "w", encoding="utf-8").write(old)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf-8").write(new)

GRAMMAR = {
    "plural -en/-nen": r'-en\b.*consonant|plural|-nen', "definite -il": r'-il\b|definite',
    "past -et": r'-et\b', "future -esh": r'-esh\b', "progressive -on": r'-on\b',
    "perfect -av": r'-av\b', "subjunctive -un": r'-un\b', "negation ne-": r'\bne-',
    "comparative -ter": r'-ter\b', "superlative -tēm": r'-tēm\b|-tem\b',
    "agent -or": r'-or\b', "abstract -eso": r'-eso\b', "verbalizer -ifa": r'-ifa\b',
    "relativizer ke": r'\bke\b|relativ', "possessive -sa": r'-sa\b',
    "questions ka/wh": r'\bka\b|kwo\b|wh-',
}

def main():
    print("=" * 74)
    print("VELQAN GAP-FILL  —  %s" % ("APPLYING (backup -> %s)" % BACKUP if APPLY else "DRY RUN (writes nothing)"))
    print("=" * 74)

    guide = fetch_guide()
    if not guide:
        print("aborting — no canonical guide"); return
    canon = parse_canon(guide)
    print("canonical guide fetched: %d chars | %d base words parsed" % (len(guide), len(canon)))

    for name, mem in TREES.items():
        print("\n" + "-" * 60)
        print("BEING: %s   (%s)" % (name, mem))
        if not os.path.isdir(mem):
            print("   !! memory dir missing — skipped"); continue

        # 1. install canonical guide
        gpath = os.path.join(mem, "velqan", "canonical-guide.md")
        cur = rd(gpath)
        if cur == guide:
            print("   [guide] already up to date at velqan/canonical-guide.md")
        else:
            print("   [guide] %s velqan/canonical-guide.md (%d chars)" %
                  ("installing" if cur is None else "updating", len(guide)))
            backup_then_write(gpath, cur, guide)

        # 2. word gap vs the being's combined knowledge (reference + full-lexicon)
        ref = rd(os.path.join(mem, "velqan-reference.md")) or ""
        lexp = os.path.join(mem, "velqan", "full-lexicon.md")
        lex = rd(lexp) or ""
        known = set(TOKEN.findall((ref + "\n" + lex).lower()))
        missing = [(w, canon[w]) for w in sorted(canon) if w not in known]
        print("   [words] canonical %d | known %d | MISSING %d" % (len(canon), len(known & set(canon)), len(missing)))
        for w, g in missing:
            print("       + %-10s %s" % (w, g[:52]))
        if missing:
            add = ("\n\n## From Gloria's Canonical Guide (gap-fill %s)\n" % TS
                   + "*Base words present in the canonical guide that were absent here. Build from these too.*\n"
                   + "\n".join("%s - %s" % (w, g) for w, g in missing) + "\n")
            new_lex = (lex.rstrip() + add) if lex else ("# Velqan — full lexicon\n" + add)
            backup_then_write(lexp, lex if lex else None, new_lex)

        # 3. grammar coverage of the hand-copied reference (report only)
        miss_g = [n for n, pat in GRAMMAR.items() if not re.search(pat, ref)]
        if miss_g:
            print("   [grammar] reference does NOT document: " + ", ".join(miss_g))
            print("             (now backstopped by velqan/canonical-guide.md)")
        else:
            print("   [grammar] reference documents all core features")

    print("\n" + "=" * 74)
    if APPLY:
        print("APPLIED. Backups at", BACKUP)
    else:
        print("DRY RUN complete. Re-run with --apply to install guide + fill word gaps (backs up first).")
    print("=" * 74)

if __name__ == "__main__":
    main()
