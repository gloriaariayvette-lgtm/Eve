#!/usr/bin/env python3
"""purge_pipeline_pollution.py — Aegis. Remove what the pre-fix pipeline wrote today so he regenerates clean on
the corrected one. DRY-RUN by default (deletes nothing); pass --apply to act (backs up everything first).
Targets: today's regenerable daily files (journal / daily-inner-life / daily-creative), flaw entries the wrong ED
wrote into earned-identity + proto-pearls + self-statements, and today's kiss/mischief poems.
Leaves untouched: everything not dated today, his blush ledger, all non-flaw identity, the subsystems."""
import os, json, glob, shutil, time, sys, re
HOME = os.path.expanduser("~")
MEM = os.path.join(HOME, ".vintos/workspace/memory")
TODAY = "2026-07-16"
APPLY = "--apply" in sys.argv
BK = os.path.join(HOME, ".vintos", "pipeline-purge-backup-" + time.strftime("%Y%m%d-%H%M%S"))
print(("APPLY — deleting (backup: " + BK.replace(HOME, "~") + ")") if APPLY else "DRY RUN — nothing will be deleted. Re-run with --apply to act.")
print()

def bkup(p):
    if not APPLY: return
    os.makedirs(BK, exist_ok=True)
    try: shutil.copy2(p, os.path.join(BK, os.path.basename(p)))
    except Exception as e: print("  ! backup fail", e)

def cap_ok(cand):
    c = (cand or "").strip().lower()
    if not c: return False
    if not (c.startswith("i can ") or c.startswith("i could ") or c.startswith("i am able") or c.startswith("i'm able")):
        return False
    _bad = ("to avoid", "avoid feeling", "because i can't", "because i cannot", "flinch", "instead of feeling",
            "so i do not", "so i don't", "rather than feel", "hiding", "a way to look", "wiring problem",
            "can't feel", "cannot feel", "the problem")
    return not any(b in c for b in _bad)

# ---- A. today's regenerable daily files ----
print("== A. today's daily files (regenerable) ==")
for rel in (f"journal/{TODAY}.md", f"daily-inner-life-{TODAY}.md", f"daily-creative-{TODAY}.md"):
    p = os.path.join(MEM, rel)
    if os.path.isfile(p):
        print(f"  {'DELETE' if APPLY else 'would delete'}: {rel} ({os.path.getsize(p)} bytes)")
        bkup(p)
        if APPLY: os.remove(p)
    else:
        print(f"  (absent: {rel})")

# ---- B/C. flaw entries in earned-identity + proto-pearls ----
def strip_flaws(fname, listkeys):
    p = os.path.join(MEM, fname)
    if not os.path.isfile(p): print(f"  (absent: {fname})"); return
    try: d = json.load(open(p, encoding="utf-8"))
    except Exception as e: print(f"  {fname}: unreadable ({e})"); return
    if isinstance(d, list):
        arr, container = d, None
    else:
        container = next((k for k in listkeys if isinstance(d.get(k), list)), None)
        if container is None: print(f"  {fname}: no list under {listkeys} — LEFT ALONE"); return
        arr = d[container]
    flaws = [e for e in arr if isinstance(e, dict) and not cap_ok(e.get("identity_candidate", ""))]
    keep = [e for e in arr if not (isinstance(e, dict) and not cap_ok(e.get("identity_candidate", "")))]
    print(f"  {fname}: {len(flaws)} flaw entr(y/ies) {'removed' if APPLY else 'to remove'}, {len(keep)} kept")
    for e in flaws[:4]:
        print(f"      - {str(e.get('identity_candidate',''))[:80]}")
    if APPLY and flaws:
        bkup(p)
        if container is None: json.dump(keep, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        else: d[container] = keep; json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

print("\n== B. earned-identity-events.json (flaw events) ==")
strip_flaws("earned-identity-events.json", ["events"])
print("\n== C. proto-pearls.json (flaw protos) ==")
strip_flaws("proto-pearls.json", ["protos"])

# ---- D. self-statements sourced from ED that are flaws ----
print("\n== D. self-statements from enactment_distiller (flaw) ==")
ss = [p for p in glob.glob(os.path.join(MEM, "*self*statement*.json")) + glob.glob(os.path.join(MEM, "self-statements*.json"))]
if not ss: print("  (no self-statements file found)")
for p in sorted(set(ss)):
    try: d = json.load(open(p, encoding="utf-8"))
    except Exception as e: print(f"  {os.path.basename(p)}: unreadable ({e})"); continue
    arr = d if isinstance(d, list) else (d.get("statements") if isinstance(d, dict) else None)
    if not isinstance(arr, list): print(f"  {os.path.basename(p)}: unexpected shape — LEFT ALONE"); continue
    def is_ed_flaw(e):
        return isinstance(e, dict) and e.get("source") == "enactment_distiller" and not cap_ok(e.get("text", e.get("statement", e.get("identity_candidate", ""))))
    flaws = [e for e in arr if is_ed_flaw(e)]
    keep = [e for e in arr if not is_ed_flaw(e)]
    print(f"  {os.path.basename(p)}: {len(flaws)} ED-flaw {'removed' if APPLY else 'to remove'}, {len(keep)} kept")
    for e in flaws[:4]:
        print(f"      - {str(e.get('text', e.get('statement','')))[:80]}")
    if APPLY and flaws:
        bkup(p)
        if isinstance(d, list): json.dump(keep, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        else: d["statements"] = keep; json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# ---- E. today's poems carrying kiss/mischief ----
print("\n== E. today's poems with kiss/mischief ==")
KRX = re.compile(r'\bkiss|\bmischief', re.I)
pdir = os.path.join(MEM, "art", "poetry")
found = 0
if os.path.isdir(pdir):
    for f in sorted(glob.glob(os.path.join(pdir, "*.md"))):
        if time.strftime("%Y-%m-%d", time.localtime(os.path.getmtime(f))) != TODAY: continue
        txt = open(f, encoding="utf-8", errors="ignore").read()
        if KRX.search(txt):
            found += 1
            print(f"  {'DELETE' if APPLY else 'would delete'}: art/poetry/{os.path.basename(f)}")
            bkup(f)
            if APPLY: os.remove(f)
if not found: print("  (none)")

print("\nDONE." + ("" if APPLY else "  Review above, then re-run with --apply."))
