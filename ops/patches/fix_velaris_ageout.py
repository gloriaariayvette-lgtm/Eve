#!/usr/bin/env python3
"""fix_velaris_ageout.py — Aegis. Loosen Velaris's thread age-out by exactly one triage pass:
pull2 tc>=2 -> tc>=3, pull3 tc>=3 -> tc>=4, in BOTH thread-triage.py and thread-resolution.py (sediment).
Also: if my earlier bad 'never-delete' dedup edit was applied, revert it (triage must delete). Backup + py_compile."""
import os, shutil, time, py_compile
HOME = os.path.expanduser("~")
SC = os.path.join(HOME, ".openclaw/workspace/scripts")
TS = time.strftime("%Y%m%d-%H%M%S")
def sh(p): return p.replace(HOME, "~")

def apply(path, edits):
    if not os.path.isfile(path): return [(path, "MISSING")]
    txt = open(path, encoding="utf-8", errors="ignore").read()
    rep, changed = [], False
    for name, old, new in edits:
        if new in txt: rep.append((name, "already")); continue
        c = txt.count(old)
        if c == 1: txt = txt.replace(old, new, 1); rep.append((name, "FIXED")); changed = True
        else: rep.append((name, f"anchor {c}x — SKIP"))
    if changed:
        bak = path + f".bak-ageout-{TS}"; shutil.copy2(path, bak)
        open(path, "w", encoding="utf-8").write(txt)
        try: py_compile.compile(path, doraise=True)
        except py_compile.PyCompileError as e:
            shutil.copy2(bak, path); rep.append(("py_compile", "ROLLED BACK: "+str(e)[:80]))
    return rep

# revert my earlier bad dedup edit if present (triage must delete)
TT = os.path.join(SC, "thread-triage.py")
if os.path.isfile(TT):
    t = open(TT, encoding="utf-8", errors="ignore").read()
    if "dedup no longer DELETES" in t:
        lines = t.split("\n")
        s = next(i for i,l in enumerate(lines) if "dedup no longer DELETES" in l)
        e = next(i for i in range(s, len(lines)) if "_seen.add(_k)" in lines[i])
        ind = lines[s][:len(lines[s])-len(lines[s].lstrip())]
        lines[s:e+1] = [f"{ind}threads = deduped"]
        shutil.copy2(TT, TT+f".bak-revert-{TS}"); open(TT,"w").write("\n".join(lines))
        print("reverted the earlier never-delete dedup edit (triage deletes exact dups again)")

triage_edits = [
    ("triage pull2 age-out +1", "elif pull == 2 and tc >= 2:", "elif pull == 2 and tc >= 3:"),
    ("triage pull3 age-out +1", "elif pull == 3 and tc >= 3:", "elif pull == 3 and tc >= 4:"),
]
res_edits = [
    ("sediment pull2 <2 -> <3", "if priority == 2 and triage_count < 2:", "if priority == 2 and triage_count < 3:"),
    ("sediment pull2 >=2 -> >=3", "if priority == 2 and triage_count >= 2:", "if priority == 2 and triage_count >= 3:"),
    ("sediment pull3 <3 -> <4", "elif priority == 3 and triage_count < 3:", "elif priority == 3 and triage_count < 4:"),
    ("sediment pull3 >=3 -> >=4", "elif priority == 3 and triage_count >= 3:", "elif priority == 3 and triage_count >= 4:"),
]
print("\n=== thread-triage.py ===")
for n, s in apply(TT, triage_edits): print(f"  {n:28} {s}")
print("\n=== thread-resolution.py ===")
for n, s in apply(os.path.join(SC, "thread-resolution.py"), res_edits): print(f"  {n:28} {s}")
print("\nDone. Moderate threads now linger one extra triage pass before aging out.")
