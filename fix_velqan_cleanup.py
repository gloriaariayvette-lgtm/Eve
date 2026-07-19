#!/usr/bin/env python3
"""fix_velqan_cleanup.py — corrects two flaws left by fix_velqan.py's first apply. READ-ONLY unless --apply.

FLAW 1: the utterances ** cleanup was too blunt — it stripped trailing ** and thereby UNBALANCED
        legitimate **bold** pairs across both beings' authentic utterance logs. Fix: RESTORE both
        velqan-utterances.md verbatim from the backup (undo the damage; leave the logs authentic).

FLAW 2: the reference coined-lists carried cosmetic residue (leftover '()', leaked IPA, a stray '**',
        empty glosses on ###-style entries, and curly-vs-straight apostrophe duplicates that didn't
        de-dupe). Fix: re-derive the Velaris list cleanly from the BACKUP original with a proper
        parser (strip parens/markdown, recover ### glosses incl. **MEANING:**, apostrophe-normalized
        de-dupe), and rewrite BOTH references' coined layers. Grammar/base head stays exactly as-is.

Uses the most recent ~/.velqan-backups/<ts>/ (or pass a path as the first non-flag arg).

RUN:
  python3 fix_velqan_cleanup.py            # DRY RUN — prints changes, writes nothing
  python3 fix_velqan_cleanup.py --apply    # restores utterances + rewrites coined lists (re-backs-up first)
"""
import os, re, sys, glob, difflib, datetime, shutil

APPLY = "--apply" in sys.argv
ARGS = [a for a in sys.argv[1:] if not a.startswith("-")]

HOME = os.path.expanduser("~")
HIS_MEM = os.path.join(HOME, ".vintos/workspace/memory")
HER_MEM = os.path.join(HOME, ".openclaw/workspace/memory")

TS = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
REBACKUP = os.path.join(HOME, ".velqan-backups", TS + "-cleanup")

TWIN_HDR = "## {twin}'s Coinages (optional)"
OWN_HDR = "## Your Coined Words"

def rd(p):
    try:
        return open(p, encoding="utf-8", errors="ignore").read()
    except Exception:
        return None

def latest_backup():
    if ARGS:
        return ARGS[0]
    cands = sorted(glob.glob(os.path.join(HOME, ".velqan-backups", "*")))
    cands = [c for c in cands if "-cleanup" not in os.path.basename(c) and os.path.isdir(c)]
    return cands[-1] if cands else None

def show_diff(path, old, new):
    if old == new:
        print(f"   (no change) {path}"); return
    for l in difflib.unified_diff((old or "").splitlines(), new.splitlines(),
                                  fromfile=path + " (old)", tofile=path + " (new)", lineterm=""):
        print("   " + l[:150])

def backup_then_write(path, old, new):
    if not APPLY:
        return
    rel = os.path.relpath(path, HOME)
    bpath = os.path.join(REBACKUP, rel)
    os.makedirs(os.path.dirname(bpath), exist_ok=True)
    if old is not None:
        open(bpath, "w", encoding="utf-8").write(old)
    open(path, "w", encoding="utf-8").write(new)

# ---- clean parser ---------------------------------------------------------
def clean_word(w):
    w = re.sub(r'[*`]', '', w or '').strip().strip('"\'’‘').strip()
    return w.split()[0] if w else w

def norm(w):
    return re.sub(r"[’‘'`]", "'", w).lower()

def extract_gloss(ls):
    s = re.sub(r'^[-*`\s]+', '', ls)      # bullet + leading markdown
    s = re.sub(r'\([^)]*\)', '', s)       # all (...) incl IPA and empty ()
    s = re.sub(r'[*`]', '', s)            # markdown
    s = re.sub(r'^\S+\s*', '', s, count=1)  # drop the word token
    s = re.sub(r'^[\s\-–—:]+', '', s)     # leading separators
    return re.sub(r'\s+', ' ', s).strip()

FIELD = r'^\*{0,2}(PRONUNCIATION|ROOTS|PART|BORN|SENTENCE|WHY|Roots|Etymology|Example)'

def parse_clean(text):
    m = re.search(r'^##+\s*Coined Vocabulary.*$', text, re.M)
    if not m:
        return []
    lines = text[m.end():].splitlines()
    ents, seen = [], {}
    def add(word, gloss):
        if not word or len(word) < 2:
            return
        k = norm(word)
        if k not in seen:
            seen[k] = len(ents); ents.append([word, gloss])
        elif gloss and not ents[seen[k]][1]:
            ents[seen[k]][1] = gloss
    i = 0
    while i < len(lines):
        ls = lines[i].strip()
        mh = re.match(r'^###\s+[*`]*([^\s/*`]+)', ls)
        mb = re.match(r'^-\s*[*`]*\s*[*`]*([^\s(*`]+)', ls)
        if mh:
            word, gloss = clean_word(mh.group(1)), ""
        elif mb:
            word, gloss = clean_word(mb.group(1)), extract_gloss(ls)
        else:
            i += 1; continue
        if not gloss:                      # recover a gloss that lives on a later MEANING/plain line
            for j in range(i + 1, min(i + 7, len(lines))):
                t = lines[j].strip()
                if t.startswith(("###", "- ")):
                    break
                mm = re.match(r'^\*{0,2}MEANING:\**\s*(.+)', t, re.I)
                if mm:
                    gloss = re.sub(r'[*`]', '', mm.group(1)).strip(); break
                if t and not re.match(FIELD, t, re.I):
                    gloss = re.sub(r'[*`]', '', t).strip(); break
        add(word, gloss)
        i += 1
    return ents

# ---- renderers (match fix_velqan.py) --------------------------------------
def render_own(name, entries):
    out = [OWN_HDR,
           f"*These are YOURS — words {name} has coined. Build new ones from Gloria's base vocabulary "
           f"(its roots and thread/weave logic), not from anyone else's coinages.*", ""]
    if not entries:
        out.append("*(none yet — your first is waiting)*")
    for w, g in entries:
        out.append(f"- {w}" + (f" — {g}" if g else ""))
    return "\n".join(out) + "\n"

def render_twin(twin, entries):
    out = [TWIN_HDR.format(twin=twin),
           f"*{twin} coined these. You MAY build on one if it truly fits — but lean hard toward coining "
           f"your OWN from Gloria's base vocabulary. Another being's words are borrowed, not native.*", ""]
    if not entries:
        out.append(f"*({twin} has not coined anything yet.)*")
    for w, g in entries:
        out.append(f"- {w}" + (f" — {g}" if g else ""))
    return "\n".join(out) + "\n"

def head_before_own(current_ref):
    """Return everything in the CURRENT reference above '## Your Coined Words' (the preserved head)."""
    idx = current_ref.find(OWN_HDR)
    if idx == -1:
        # fall back to old header if cleanup runs before fix
        m = re.search(r'^##+\s*Coined Vocabulary.*$', current_ref, re.M)
        idx = m.start() if m else len(current_ref)
    return current_ref[:idx].rstrip() + "\n"

# ---------------------------------------------------------------------------
def main():
    bk = latest_backup()
    print("=" * 74)
    print("VELQAN CLEANUP  —  %s" % ("APPLYING (re-backup -> %s)" % REBACKUP if APPLY else "DRY RUN (writes nothing)"))
    print("backup source:", bk)
    print("=" * 74)
    if not bk or not os.path.isdir(bk):
        print("!! no backup dir found under ~/.velqan-backups — aborting"); return

    # (1) restore utterances from backup (undo the bold-pair damage)
    print("\n[1] restore utterances from backup (undo unbalanced-bold damage)")
    for mem, tree in ((HIS_MEM, ".vintos"), (HER_MEM, ".openclaw")):
        live = os.path.join(mem, "velqan-utterances.md")
        bfile = os.path.join(bk, tree, "workspace/memory/velqan-utterances.md")
        cur, orig = rd(live), rd(bfile)
        if orig is None:
            print(f"   !! no backup utterances for {tree} ({bfile}) — skipped"); continue
        if cur == orig:
            print(f"   {tree}: already matches backup (nothing to restore)"); continue
        print(f"   {tree}: restoring {live}")
        show_diff(live, cur, orig)
        backup_then_write(live, cur, orig)

    # (2) re-derive the clean Velaris list from the BACKUP original reference
    her_bk_ref = rd(os.path.join(bk, ".openclaw/workspace/memory/velqan-reference.md"))
    if her_bk_ref is None:
        print("\n!! no backup Velaris reference — cannot re-derive list; aborting list rewrite"); return
    velaris_list = parse_clean(her_bk_ref)
    vintos_list = [("thir-vithra",
                    'the somatic, heavy "silt" of presence; the specific gravity of simply being')]
    print(f"\n[2] clean coinage lists — Velaris: {len(velaris_list)}  |  Vintos: {len(vintos_list)}")
    for w, g in velaris_list:
        print("   VEL  %-14s | %s" % (w, g[:66]))

    # (3) rewrite both references' coined layers (head preserved from CURRENT file)
    print("\n[3] rewrite reference coined layers")
    plans = [
        (os.path.join(HIS_MEM, "velqan-reference.md"), "Vintos", vintos_list, "Velaris", velaris_list),
        (os.path.join(HER_MEM, "velqan-reference.md"), "Velaris", velaris_list, "Vintos", vintos_list),
    ]
    for path, name, own, twin, twin_list in plans:
        cur = rd(path)
        if cur is None:
            print(f"   !! {name} reference missing at {path}"); continue
        head = head_before_own(cur)
        new = head.rstrip() + "\n\n" + render_own(name, own) + "\n" + render_twin(twin, twin_list)
        print(f"\n   --- {name} ({path}) ---")
        show_diff(path, cur, new)
        backup_then_write(path, cur, new)

    print("\n" + "=" * 74)
    if APPLY:
        print("APPLIED. Pre-cleanup state saved at", REBACKUP)
    else:
        print("DRY RUN complete. Re-run with --apply to commit (re-backs-up first).")
    print("=" * 74)

if __name__ == "__main__":
    main()
