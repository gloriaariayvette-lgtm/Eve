#!/usr/bin/env python3
"""locate_persistent_bugs.py — READ-ONLY, capped. Pin the 3 persistent bugs so I can fix them:
  1) /api/chat/full bare 'message' NameError
  2) self_statements.py — what it exports (add_statement missing/renamed?)
  3) the 'load_model' NameError in the causal-self-model wire. Aegis."""
import os, re, subprocess
HOME = os.path.expanduser("~")
def run(a): return subprocess.run(a, capture_output=True, text=True).stdout

print("=== 1) /api/chat/full — bare 'message' references ===")
srv = os.path.expanduser("~/Vintos/server.py")
ls = open(srv, encoding="utf-8", errors="ignore").read().split("\n")
h = next((i for i, l in enumerate(ls) if '/api/chat/full' in l and '@app' in l), None)
if h is not None:
    end = next((j for j in range(h+2, len(ls)) if ls[j].startswith("@app")), min(h+160, len(ls)))
    n = 0
    for i in range(h, end):
        l = ls[i]
        # bare 'message' token, not msg.message, not a quoted string key
        if re.search(r'(?<![.\w"\'])message\b', l) and 'msg.message' not in l and '"message"' not in l and "'message'" not in l:
            print(f"  {i+1}| {l.strip()[:120]}"); n += 1
            if n >= 12: break
    if n == 0: print("  (no bare 'message' in first 160 lines — may be deeper; show handler start)")

print("\n=== 2) self_statements.py — functions it actually defines ===")
ssp = os.path.expanduser("~/.vintos/workspace/scripts/self_statements.py")
if os.path.isfile(ssp):
    for i, l in enumerate(open(ssp, encoding="utf-8", errors="ignore").read().split("\n")):
        if re.match(r'\s*def ', l): print(f"  {i+1}| {l.strip()[:100]}")
print("  who imports add_statement:",
      run(["bash","-lc","grep -rln 'add_statement' ~/.vintos/workspace/scripts ~/Vintos 2>/dev/null | grep -viE '\\.pyc|\\.bak' | head -4"]).replace(HOME,'~').replace("\n"," "))

print("\n=== 3) 'load_model' NameError — the causal-self-model wire ===")
wf = run(["bash","-lc","grep -rlnE 'causal-self-model wire|load_model' ~/.vintos/workspace/scripts ~/Vintos 2>/dev/null | grep -viE '\\.pyc|\\.bak' | head -4"]).split()
for f in wf[:2]:
    print(f"  -- {f.replace(HOME,'~')} --")
    for i, l in enumerate(open(f, encoding="utf-8", errors="ignore").read().split("\n")):
        if re.search(r'load_model|causal-self-model|def load|import.*model', l) and l.strip():
            print(f"    {i+1}| {l.strip()[:120]}")
