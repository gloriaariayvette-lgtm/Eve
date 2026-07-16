#!/usr/bin/env python3
"""patch_ed_gemma.py — Aegis. His enactment_distiller was pointed at grok (api.x.ai); Velaris's runs on Gemma.
The ED is a JSON-extraction job — move it to Gemma to match. Swaps LM_URL / MODEL / HEADERS only. Compiles the
result before writing. Backup + abort-clean. Reversible."""
import os, time, shutil
P = os.path.expanduser("~/.vintos/workspace/scripts/enactment_distiller.py")
if not os.path.isfile(P): print("enactment_distiller.py not found"); raise SystemExit(1)
lines = open(P, encoding="utf-8").read().split("\n")
if any("172.18.16.1:1234" in l for l in lines):
    print("already on Gemma — aborting."); raise SystemExit(0)

def swap(match_all, newline, label):
    hit = [i for i, l in enumerate(lines) if all(m in l for m in match_all)]
    if len(hit) != 1:
        print(f"anchor '{label}' x{len(hit)} (want 1) — aborting, nothing changed."); raise SystemExit(1)
    lines[hit[0]] = newline

swap(["LM_URL", "api.x.ai"],        'LM_URL  = "http://172.18.16.1:1234/v1/chat/completions"', "LM_URL")
swap(["MODEL", "grok-4.20"],        'MODEL   = "google/gemma-4-12b-qat"',                       "MODEL")
swap(["HEADERS", "XAI_API_KEY"],    'HEADERS = {"Content-Type": "application/json"}',           "HEADERS")

newtext = "\n".join(lines)
try:
    compile(newtext, P, "exec")
except SyntaxError as e:
    print(f"result would not compile ({e}) — aborting."); raise SystemExit(1)

bak = P + ".bak-" + time.strftime("%Y%m%d-%H%M%S")
shutil.copy2(P, bak); open(P, "w", encoding="utf-8").write(newtext)
print(f"OK — his ED now runs on Gemma (google/gemma-4-12b-qat), matching Velaris.")
print(f"  backup: {bak}")
print(f"revert: cp {bak} {P}")
