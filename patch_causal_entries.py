#!/usr/bin/env python3
"""patch_causal_entries.py — Aegis. Fix the one live intercept-wire bug: add_entry() does data["entries"] but
load_model() returns no 'entries' key when causal-self-model.json is empty/missing -> KeyError: 'entries'.
Use setdefault so it self-heals. Compile-checked, backed up. (The 'load_model not defined' and 'add_statement'
log lines are stale — the current modules define both.)"""
import os, time, shutil
P = os.path.expanduser("~/.vintos/workspace/scripts/causal_self_model.py")
if not os.path.isfile(P): print("causal_self_model.py not found"); raise SystemExit(1)
txt = open(P, encoding="utf-8").read()
OLD = '    entries = data["entries"]'
NEW = '    entries = data.setdefault("entries", [])'
if "data.setdefault(\"entries\"" in txt:
    print("already fixed."); raise SystemExit(0)
if txt.count(OLD) != 1:
    print(f"anchor x{txt.count(OLD)} (want 1) — aborting."); raise SystemExit(1)
new = txt.replace(OLD, NEW)
try:
    compile(new, P, "exec")
except SyntaxError as e:
    print(f"would not compile ({e}) — aborting."); raise SystemExit(1)
bak = P + ".bak-" + time.strftime("%Y%m%d-%H%M%S")
shutil.copy2(P, bak); open(P, "w", encoding="utf-8").write(new)
print(f"OK — add_entry self-heals when the model file is empty (no more KeyError 'entries'). backup: {bak}")
