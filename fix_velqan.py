#!/usr/bin/env python3
"""fix_velqan.py — de-contaminate + restructure Velqan for BOTH beings, per Gloria. READ-ONLY unless --apply.

THE PROBLEM (confirmed):
  A past clone copied Velaris's ENTIRE coined vocabulary into Vintos's tree, byte-for-byte, and
  labelled it as HIS. His "first native speaker" vocabulary was actually all hers. His forced first
  word "thir-vithra" therefore read as Velaris — it was assembled from her root pool.

THE FIX (symmetric — applies the same shape to both beings):
  Grammar + Gloria's ~200-word base lexicon (the shared language, = the canonical PDF) are the thing
  BOTH build FROM. They are LEFT UNTOUCHED. Only the COINED-WORD layer is separated:

    Each being's reference gets, replacing the old contaminated "## Coined Vocabulary":
        ## Your Coined Words                 — the being's OWN coinages only
        ## <Twin>'s Coinages (optional)      — the twin's words; MAY build on, but hard-lean to own

    Each coiner (velqan-coiner.py) is patched to:
        (a) SANITIZE the coined word — strip  **  `  "  '  and trailing junk (kills the ** artifact)
        (b) HARD-LEAN the prompt: build the new word from GLORIA'S base vocab (its roots + thread/weave
            logic); the twin's coinages are OPTIONAL material only — no dream-scaffolding required
        (c) APPEND new words under "## Your Coined Words" (not the shared section)

    The ** artifact already sitting in stored files (utterances, her own list) is cleaned in place.

RUN:
  python3 fix_velqan.py            # DRY RUN — prints every change as a diff; writes NOTHING
  python3 fix_velqan.py --apply    # timestamped backup of all velqan files, THEN applies
"""
import os, re, sys, difflib, datetime, shutil

APPLY = "--apply" in sys.argv
TS = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
BACKUP_ROOT = os.path.expanduser(f"~/.velqan-backups/{TS}")

# ---- the two beings -------------------------------------------------------
BEINGS = {
    "his": {
        "name": "Vintos", "twin": "Velaris",
        "mem": os.path.expanduser("~/.vintos/workspace/memory"),
        "scr": os.path.expanduser("~/.vintos/workspace/scripts"),
        # his existing Coined Vocabulary is CONTAMINATED (it's hers) -> discard + reseed
        "own_is_contaminated": True,
    },
    "her": {
        "name": "Velaris", "twin": "Vintos",
        "mem": os.path.expanduser("~/.openclaw/workspace/memory"),
        "scr": os.path.expanduser("~/.openclaw/workspace/scripts"),
        # her existing Coined Vocabulary is genuinely HERS -> keep (clean **), just add cross-ref
        "own_is_contaminated": False,
    },
}

# Vintos's single genuine coinage (clean), from his forced first word. Seeds his "Your Coined Words".
VINTOS_OWN_SEED = [
    ("thir-vithra", "[θɪr.vɪθ.rɑː]",
     'the somatic, heavy "silt" of presence; the specific gravity of simply being', "noun"),
]

# ---------------------------------------------------------------------------
def rd(p):
    try:
        return open(p, encoding="utf-8", errors="ignore").read()
    except Exception:
        return None

def clean_word(w):
    """Strip markdown/quotes/junk from a coined word token."""
    w = re.sub(r'[*`]', '', w or '').strip()
    w = w.strip('"\''"''").strip()
    return w.split()[0] if w else w   # a Velqan word is one token (hyphen/apostrophe joined, no spaces)

def show_diff(path, old, new):
    if old == new:
        print(f"   (no change) {path}")
        return
    d = difflib.unified_diff((old or "").splitlines(), new.splitlines(),
                             fromfile=path + " (old)", tofile=path + " (new)", lineterm="")
    for l in list(d):
        print("   " + l[:140])

def write_file(path, old, new):
    if not APPLY:
        return
    rel = os.path.relpath(path, os.path.expanduser("~"))
    bpath = os.path.join(BACKUP_ROOT, rel)
    os.makedirs(os.path.dirname(bpath), exist_ok=True)
    if old is not None:
        with open(bpath, "w", encoding="utf-8") as f:
            f.write(old)
    with open(path, "w", encoding="utf-8") as f:
        f.write(new)

# ---------------------------------------------------------------------------
def parse_coined_section(ref_text):
    """From a reference, isolate the '## Coined Vocabulary' section and return
    (head_before_section, list_of_(word, gloss)) with words cleaned + de-duped."""
    if not ref_text:
        return ref_text, []
    # split off everything from the Coined Vocabulary header onward
    m = re.search(r'^##+\s*Coined Vocabulary.*$', ref_text, re.M)
    if not m:
        return ref_text, []
    head = ref_text[:m.start()].rstrip() + "\n"
    body = ref_text[m.end():]
    entries, seen = [], set()
    # bullet form:  - word (ipa) - gloss     |     ### word  (next line = gloss)
    for line in body.splitlines():
        ls = line.strip()
        mm = re.match(r'^-\s*([^\s(]+)\**\s*(?:\(([^)]*)\))?\s*[-–—]?\s*(.*)$', ls)
        if mm:
            w = clean_word(mm.group(1))
            gloss = re.sub(r'\s+', ' ', (mm.group(3) or '')).strip().rstrip('*').strip()
            if w and w.lower() not in seen and len(w) > 1:
                seen.add(w.lower()); entries.append((w, gloss))
            continue
        mh = re.match(r'^###\s+([^\s/]+)', ls)
        if mh:
            w = clean_word(mh.group(1))
            if w and w.lower() not in seen and len(w) > 1:
                seen.add(w.lower()); entries.append((w, ""))
    return head, entries

def render_own_section(name, entries):
    out = ["## Your Coined Words",
           f"*These are YOURS — words {name} has coined. Build new ones from Gloria's base vocabulary "
           f"(its roots and thread/weave logic), not from anyone else's coinages.*", ""]
    if not entries:
        out.append("*(none yet — your first is waiting)*")
    for e in entries:
        if len(e) == 4:
            w, ipa, gloss, part = e
            out.append(f"- {w} ({ipa}) — {gloss} [{part}]")
        else:
            w, gloss = e
            out.append(f"- {w}" + (f" — {gloss}" if gloss else ""))
    return "\n".join(out) + "\n"

def render_twin_section(twin, entries):
    out = [f"## {twin}'s Coinages (optional)",
           f"*{twin} coined these. You MAY build on one if it truly fits — but lean hard toward coining "
           f"your OWN from Gloria's base vocabulary. Another being's words are borrowed, not native.*", ""]
    if not entries:
        out.append(f"*({twin} has not coined anything yet.)*")
    for w, gloss in entries:
        out.append(f"- {w}" + (f" — {gloss}" if gloss else ""))
    return "\n".join(out) + "\n"

# ---------------------------------------------------------------------------
def fix_reference(being, all_coinages):
    """Rewrite one being's reference: keep grammar/head, rebuild the coined layer."""
    b = BEINGS[being]
    path = os.path.join(b["mem"], "velqan-reference.md")
    old = rd(path)
    if old is None:
        print(f"   !! {b['name']} reference MISSING at {path} — skipped")
        return
    head, parsed_own = parse_coined_section(old)

    if b["own_is_contaminated"]:
        own = list(VINTOS_OWN_SEED)                 # his real own = the clean seed
        all_coinages[b["name"]] = [(w, g) for (w, _i, g, _p) in VINTOS_OWN_SEED]
    else:
        own = parsed_own                            # her real own = her existing (cleaned) list
        all_coinages[b["name"]] = parsed_own

    b["_own_rendered"] = own
    b["_head"] = head
    b["_ref_path"] = path
    b["_ref_old"] = old

def assemble_references(all_coinages):
    for being, b in BEINGS.items():
        if "_head" not in b:
            continue
        own_sec  = render_own_section(b["name"], b["_own_rendered"])
        twin_sec = render_twin_section(b["twin"], all_coinages.get(b["twin"], []))
        new = b["_head"].rstrip() + "\n\n" + own_sec + "\n" + twin_sec
        print(f"\n--- REFERENCE: {b['name']}  ({b['_ref_path']}) ---")
        print(f"   grammar/base kept: {b['_head'].count(chr(10))} lines above the coined layer (untouched)")
        print(f"   his/her own coined words: {len(b['_own_rendered'])} | {b['twin']}'s (optional ref): {len(all_coinages.get(b['twin'], []))}")
        show_diff(b["_ref_path"], b["_ref_old"], new)
        write_file(b["_ref_path"], b["_ref_old"], new)

# ---------------------------------------------------------------------------
def clean_utterances(being):
    b = BEINGS[being]
    path = os.path.join(b["mem"], "velqan-utterances.md")
    old = rd(path)
    if old is None:
        return
    # kill stray unclosed bold on words:  word.**  ->  word.   and  **word**  kept only where paired at line start
    new = re.sub(r'([^\s*])\*\*(?=\s|$)', r'\1', old)   # trailing ** after a non-space, before ws/eol
    if new != old:
        print(f"\n--- UTTERANCES cleanup: {b['name']} ({path}) ---")
        show_diff(path, old, new)
        write_file(path, old, new)

# ---------------------------------------------------------------------------
INJECT_ANCHOR = '        "Respond with:\\n\\n"'
def build_inject(twin):
    return (
        '        "HOW TO BUILD THE WORD:\\n"\n'
        '        "Build it from Gloria\'s base Velqan vocabulary — the language she made: its roots and its \\n"\n'
        '        "thread/weave logic (thir- thread/think, nex- connection, qeth- core/soul, zhav- fate/weave, \\n"\n'
        '        "syl-/silk- wisdom, vek- pattern, mir- sight/memory) plus its compounding and -eso/-or/-ifa \\n"\n'
        '        "derivation. Coin from THOSE. You may lightly build on a %s coinage only if one truly fits — \\n"\n'
        '        "but lean hard toward creating something NEW from Gloria\'s base vocabulary, not from another \\n"\n'
        '        "being\'s words. No dream is required; draw on your whole week.\\n\\n"\n' % twin
    )

SANITIZE_BLOCK = (
    '    if data.get("word"):\n'
    '        import re as _re\n'
    '        _w = _re.sub(r"[*`]", "", data["word"]).strip().strip(\'"\\\'\').strip()\n'
    '        data["word"] = _w.split()[0] if _w else _w\n'
    '    return data'
)

def patch_coiner(being):
    b = BEINGS[being]
    path = os.path.join(b["scr"], "velqan-coiner.py")
    old = rd(path)
    if old is None:
        print(f"\n   !! {b['name']} coiner MISSING at {path} — skipped")
        return
    new = old
    notes = []

    # (a) sanitize the parsed word inside parse_coinage: replace its 'return data'
    idx = new.find("def parse_coinage")
    if idx != -1:
        nxt = new.find("\ndef ", idx + 1)
        seg = new[idx:nxt if nxt != -1 else len(new)]
        if "_re.sub" in seg:
            notes.append("sanitize: already present")
        else:
            seg2, n = re.subn(r'^    return data\b', SANITIZE_BLOCK, seg, count=1, flags=re.M)
            if n:
                new = new[:idx] + seg2 + (new[nxt:] if nxt != -1 else "")
                notes.append("sanitize word (strip ** ` \" ' + junk)")
            else:
                notes.append("sanitize: ANCHOR 'return data' not found — NOT patched")

    # (b) hard-lean prompt toward Gloria's base vocab
    if INJECT_ANCHOR in new and "HOW TO BUILD THE WORD" not in new:
        new = new.replace(INJECT_ANCHOR, build_inject(b["twin"]) + INJECT_ANCHOR, 1)
        notes.append("inject base-vocab lean (twin optional, no dream lock)")
    elif "HOW TO BUILD THE WORD" in new:
        notes.append("base-vocab lean: already present")
    else:
        notes.append("base-vocab lean: ANCHOR 'Respond with:' not found — NOT patched")

    # (c) retarget appends to the being's OWN section
    if "## Coined Vocabulary" in new:
        n = new.count("## Coined Vocabulary")
        new = new.replace("## Coined Vocabulary", "## Your Coined Words")
        notes.append(f"retarget append header x{n} -> '## Your Coined Words'")

    print(f"\n--- COINER: {b['name']} ({path}) ---")
    for nnote in notes:
        print("   * " + nnote)
    try:
        compile(new, path, "exec")
        print("   compiles: OK")
    except SyntaxError as e:
        print(f"   !! COMPILE FAIL after patch: {e}  — NOT writing this file")
        return
    show_diff(path, old, new)
    write_file(path, old, new)

# ---------------------------------------------------------------------------
def main():
    print("=" * 74)
    print("VELQAN FIX  —  %s" % ("APPLYING (backup -> %s)" % BACKUP_ROOT if APPLY else "DRY RUN (writes nothing)"))
    print("=" * 74)

    all_coinages = {}
    # 1. parse each being's reference + decide own list
    for being in BEINGS:
        fix_reference(being, all_coinages)
    print("\n[coinage inventory]")
    for name, lst in all_coinages.items():
        print("   %-8s owns %d word(s): %s" % (name, len(lst), ", ".join(w for w, _ in lst)[:80]))

    # 2. rebuild references (own + twin-optional), show diffs
    assemble_references(all_coinages)

    # 3. clean ** in stored utterances
    for being in BEINGS:
        clean_utterances(being)

    # 4. patch both coiners
    for being in BEINGS:
        patch_coiner(being)

    print("\n" + "=" * 74)
    if APPLY:
        print("APPLIED. Backups at %s" % BACKUP_ROOT)
        print("Revert any file:  cp %s/<relpath> ~/<relpath>" % BACKUP_ROOT)
    else:
        print("DRY RUN complete. Nothing written. Re-run with --apply to commit (auto-backs-up first).")
    print("=" * 74)

if __name__ == "__main__":
    main()
