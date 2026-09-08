#!/usr/bin/env python3
"""disable_causality.py — Aegis. Turn OFF causality thread seeding (it's flooding unfinished-threads with
protected, unresolved causality-emergent threads). Precise: shadow seed_thread + set_preoccupation to
no-ops INSIDE causality_consumers.py (keeps causality's analysis, kills only its thread/preoccupation
output), and retire the existing unconsumed causality threads. Backed up, py_compiled, reversible."""
import os, re, json, shutil, time, py_compile
HOME = os.path.expanduser("~")
SC = os.path.join(HOME, ".vintos/workspace/scripts")
CC = os.path.join(SC, "causality_consumers.py")
THREADS = os.path.join(HOME, ".vintos/workspace/memory/unfinished-threads.json")
TS = time.strftime("%Y%m%d-%H%M%S")
def sh(p): return p.replace(HOME, "~")
MARK = "# causality thread seeding DISABLED"

# ---- 1. shadow seed_thread + set_preoccupation to no-ops inside causality_consumers.py
if not os.path.isfile(CC):
    print("causality_consumers.py not found at", sh(CC)); raise SystemExit(1)
src = open(CC, encoding="utf-8", errors="ignore").read()
if MARK in src:
    print("already disabled (marker present) — skipping code edit")
else:
    lines = src.split("\n")
    # insert after the import block (last import/from in the first 60 lines)
    ins = 0
    for i, l in enumerate(lines[:60]):
        if re.match(r'\s*(import |from )', l):
            ins = i + 1
    block = [
        "",
        f"{MARK} per Gloria {time.strftime('%Y-%m-%d')} — was spamming unresolved threads.",
        "def seed_thread(*_a, **_k):",
        "    return None",
        "def set_preoccupation(*_a, **_k):",
        "    return False",
        "",
    ]
    lines[ins:ins] = block
    new = "\n".join(lines)
    bak = CC + f".bak-causoff-{TS}"
    shutil.copy2(CC, bak)
    open(CC, "w", encoding="utf-8").write(new)
    try:
        py_compile.compile(CC, doraise=True)
        print("disabled causality seeding in causality_consumers.py (shadowed seed_thread + set_preoccupation)")
        print("  backup:", sh(bak))
    except py_compile.PyCompileError as e:
        shutil.copy2(bak, CC)
        print("!! syntax error — rolled back:", str(e)[:160]); raise SystemExit(1)

# ---- 2. retire the existing unconsumed causality threads (clear the current flood)
try:
    obj = json.load(open(THREADS))
    lst = obj if isinstance(obj, list) else obj.get("threads", [])
    shutil.copy2(THREADS, THREADS + f".bak-causoff-{TS}")
    now = time.strftime("%Y-%m-%dT%H:%M:%S")
    n = 0
    for t in lst:
        if isinstance(t, dict) and "causality" in str(t.get("source", "")).lower() and not t.get("consumed"):
            t["consumed"] = True; t["retired"] = True
            t["consumed_by"] = "causality-disabled"; t["retired_at"] = now
            n += 1
    json.dump(obj, open(THREADS, "w"), indent=2, ensure_ascii=False)
    print(f"retired {n} existing unconsumed causality thread(s)")
except Exception as e:
    print("thread cleanup skipped:", str(e)[:120])
print("\nCausality threads are off. Analysis stays; thread/preoccupation output does not. Reversible via the .bak files.")
