#!/usr/bin/env python3
"""wire_6b.py — Aegis. Phase 2 of 6b: wire the temperature into the three consumers.
  mirror.sh      -> temperature after priority in the sort key (instability sorts first)
  dream path     -> temperature as PRIMARY sort key on thread selection (heat first)
  pearl-engine.py-> surface candidates closest to crystallization first (cooling -> crystallize)
Per file: backup, apply on real anchors, syntax-check (bash -n / py_compile), rollback on failure.
Idempotent (skips an edit whose marker is already present)."""
import os, glob, shutil, time, subprocess, py_compile
HOME = os.path.expanduser("~")
SC = os.path.join(HOME, ".vintos/workspace/scripts")
TS = time.strftime("%Y%m%d-%H%M%S")
def sh(p): return p.replace(HOME, "~")

def check(path):
    if path.endswith(".sh"):
        r = subprocess.run(["bash", "-n", path], capture_output=True, text=True)
        return r.returncode == 0, r.stderr[:160]
    try:
        py_compile.compile(path, doraise=True); return True, ""
    except py_compile.PyCompileError as e:
        return False, str(e)[:160]

def apply_edits(path, edits):
    """edits: list of (old, new, replace_all). Returns (status, detail)."""
    if not os.path.isfile(path):
        return "missing", ""
    txt = open(path, encoding="utf-8", errors="ignore").read()
    orig = txt
    applied = 0
    for old, new, all_ in edits:
        if new in txt:          # idempotent — marker already present
            continue
        c = txt.count(old)
        if c == 0:
            continue
        txt = txt.replace(old, new) if all_ else txt.replace(old, new, 1)
        applied += c if all_ else 1
    if txt == orig:
        return "nochange", ""
    bak = path + f".bak-6b-{TS}"
    shutil.copy2(path, bak)
    open(path, "w", encoding="utf-8").write(txt)
    ok, err = check(path)
    if not ok:
        shutil.copy2(bak, path)
        return "rolledback", err
    return f"wired x{applied}", sh(bak)

# ---- MIRROR: temperature after priority (both sort sites) ----
mirror = os.path.join(SC, "mirror.sh")
st, d = apply_edits(mirror, [
    ('-(t.get("priority") or 0), -(t.get("dream_passes", 0)),',
     '-(t.get("priority") or 0), -(t.get("temperature") or 0), -(t.get("dream_passes", 0)),', True),
])
print(f"mirror.sh          {st}   {d}")

# ---- PEARLS: most-settled (most passes) surface first ----
pearl = os.path.join(SC, "pearl-engine.py")
st, d = apply_edits(pearl, [
    ('    for c in active[:3]:',
     '    active.sort(key=lambda c: -len((c.get("verification") or {}).get("passes", [])))  # 6b: pearls seek cooling\n    for c in active[:3]:', False),
])
print(f"pearl-engine.py    {st}   {d}")

# ---- DREAMS: temperature as primary sort key on any thread-sort in the dream path ----
dream_files = sorted({f for pat in ("*dream*.sh", "*dream*.py", "preoccupation*.sh", "should-dream*.sh")
                      for f in glob.glob(os.path.join(SC, pat)) if os.path.isfile(f) and ".bak" not in f})
wired_any = False
for f in dream_files:
    txt = open(f, encoding="utf-8", errors="ignore").read()
    if ".sort(key=lambda t: (" not in txt:
        continue
    st, d = apply_edits(f, [
        (".sort(key=lambda t: (", ".sort(key=lambda t: (-(t.get(\"temperature\") or 0), ", True)])
    print(f"{os.path.basename(f):18} {st}   {d}")
    wired_any = wired_any or st.startswith("wired")
if not dream_files or not any(".sort(key=lambda t: (" in open(f, encoding="utf-8", errors="ignore").read() for f in dream_files):
    print("dreams             no thread-sort in the dream scripts — dream seed comes via set_preoccupation;")
    print("                   threads already carry temperature, so the setter can be biased next (small follow-up).")

print("\n6b phase 2 done where anchors existed. Every change backed up (.bak-6b-*), syntax-checked, reversible.")
