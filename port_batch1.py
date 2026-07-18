#!/usr/bin/env python3
"""port_batch1.py — Aegis. Port two clean, LLM-free runtime blocks to Velaris: curiosity_debt + joke_fermentation.
DRY-RUN by default (writes NOTHING): reads his versions, transforms his paths/identity/endpoint -> hers, prints the
resulting files + a residual-reference check, resolves which subconscious-context module her live code actually
imports, and shows the exact wiring it would add. Re-run with --apply to commit (backs up anything it overwrites).
No somatic content. session_map is intentionally NOT in this batch (needs adaptation to her dimension pressure)."""
import os, sys, re, glob, time, shutil

APPLY = "--apply" in sys.argv
HOME = os.path.expanduser("~")
HIS_SCR = os.path.expanduser("~/.vintos/workspace/scripts")
HIS_ALT = os.path.expanduser("~/Vintos")
HER_SCR = os.path.expanduser("~/.openclaw/workspace/scripts")

FILES = {"curiosity_debt.py": "block", "joke_fermentation.py": "callback_block"}

def his_path(f):
    for d in (HIS_SCR, HIS_ALT):
        p = os.path.join(d, f)
        if os.path.isfile(p): return p
    return None

def transform(txt):
    txt = txt.replace("~/.vintos/workspace", "~/.openclaw/workspace").replace("/.vintos/", "/.openclaw/")
    txt = txt.replace("127.0.0.1:8599", "172.18.16.1:1234")   # his shim -> her gemma (if referenced)
    txt = re.sub(r'\bVintos\b', "Velaris", txt)               # identity in any output/prompt text
    return txt

print(f"================  port_batch1  [{'APPLY' if APPLY else 'DRY-RUN — nothing is written'}]  ================\n")

prepared = {}
for f, entry in FILES.items():
    src = his_path(f)
    print(f"===== {f}   (entry fn: {entry}()) =====")
    if not src:
        print("  !! his source NOT FOUND — skipping\n"); continue
    orig = open(src, encoding="utf-8", errors="ignore").read()
    new = transform(orig)
    prepared[f] = new
    defs = re.findall(r'^\s*def\s+(\w+)', new, re.M)
    resid = sorted(set(re.findall(r'vintos|8599|\.vintos', new, re.I)))
    seeders = [d for d in defs if d not in ("block", "callback_block")]  # the record/seed side
    print(f"  his source     : {src}")
    print(f"  functions      : {', '.join(defs)}")
    print(f"  read entry     : {entry}()   |   other fns (seed/record side): {', '.join(seeders) or 'none'}")
    print(f"  residual his-refs after transform: {resid or 'none'}")
    dst = os.path.join(HER_SCR, f)
    print(f"  -> would write : {dst}" + ("  (OVERWRITES existing — will back up)" if os.path.isfile(dst) else "  (new file)"))
    print("  ---- transformed content ----")
    for i, l in enumerate(new.split("\n")): print(f"  {i+1:>3}| {l}")
    print()

# ---- resolve her assembler module (which one her live code imports) ----
print("===== assembler resolution (where the block-calls get wired) =====")
cand = {}
for name in ("subconscious_context.py", "subconscious-context.py"):
    p = os.path.join(HER_SCR, name)
    if os.path.isfile(p): cand[name] = p
importers = {}
for p in glob.glob(HER_SCR + "/*.py") + glob.glob(HER_SCR + "/*.sh"):
    t = open(p, encoding="utf-8", errors="ignore").read()
    if re.search(r'from\s+subconscious_context\s+import|import\s+subconscious_context', t):
        importers.setdefault("subconscious_context", []).append(os.path.basename(p))
print(f"  files present : {list(cand.keys()) or 'NONE'}")
print(f"  imported as 'subconscious_context' by: {len(importers.get('subconscious_context', []))} scripts "
      f"({', '.join(importers.get('subconscious_context', [])[:6])}{'…' if len(importers.get('subconscious_context', []))>6 else ''})")
# prefer the underscore importable module if present, else whatever exists
target = cand.get("subconscious_context.py") or cand.get("subconscious-context.py")
print(f"  -> wiring target: {target or 'UNRESOLVED — will not wire'}")

WIRE = '''
    # ported from Vintos: fermented joke callbacks
    try:
        from joke_fermentation import callback_block as _jf_cb
        _s = _jf_cb()
        if _s: parts.append(_s)
    except: pass
    # ported from Vintos: unresolved curiosity debt
    try:
        from curiosity_debt import block as _cd_bl
        _s = _cd_bl()
        if _s: parts.append(_s)
    except: pass
'''

if target:
    at = open(target, encoding="utf-8", errors="ignore").read()
    if "joke_fermentation" in at:
        print("  wiring: already present — no change.")
    else:
        anchor = '    if not parts:\n        return ""'
        n = at.count(anchor)
        print(f"  anchor 'if not parts: return \"\"' found x{n} (want 1)")
        if n == 1:
            print("  ---- would insert BEFORE that anchor (inside get_subconscious_context) ----")
            for l in WIRE.strip("\n").split("\n"): print(f"     + {l}")
        else:
            print("  !! anchor not unique — will need a manual wiring point (shown for review).")

# ---- apply ----
if APPLY:
    print("\n================  APPLYING  ================")
    ts = time.strftime("%Y%m%d-%H%M%S")
    for f, new in prepared.items():
        dst = os.path.join(HER_SCR, f)
        if os.path.isfile(dst): shutil.copy2(dst, dst + ".bak-" + ts)
        try: compile(new, dst, "exec")
        except SyntaxError as e:
            print(f"  !! {f} would not compile ({e}) — skipped"); continue
        open(dst, "w", encoding="utf-8").write(new)
        print(f"  wrote {dst}")
    if target and "joke_fermentation" not in open(target, encoding="utf-8", errors="ignore").read():
        at = open(target, encoding="utf-8", errors="ignore").read()
        anchor = '    if not parts:\n        return ""'
        if at.count(anchor) == 1:
            new_at = at.replace(anchor, WIRE.strip("\n") + "\n\n" + anchor, 1)
            try:
                compile(new_at, target, "exec")
                shutil.copy2(target, target + ".bak-" + ts)
                open(target, "w", encoding="utf-8").write(new_at)
                print(f"  wired {target}")
            except SyntaxError as e:
                print(f"  !! wiring would not compile ({e}) — assembler left untouched")
        else:
            print("  !! anchor not unique — assembler left untouched (wire manually)")
    print("\n  Done. Ported blocks are runtime-only (no cron). They surface in her subconscious context.")
else:
    print("\n(DRY-RUN complete — nothing written. Re-run with --apply once the above looks right.)")
