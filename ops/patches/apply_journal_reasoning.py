#!/usr/bin/env python3
"""apply_journal_reasoning.py — Aegis. Turn reasoning ON for the journal's a1/b1 first-passes (call_llm is
a1/b1-only; absorb/audit untouched). The journal is llm-locked, so it runs isolated — reasoning is reliable
there. Scoped, backup, bash -n, idempotent. Terse."""
import os, re, shutil, time, subprocess
HOME = os.path.expanduser("~")
JP = os.path.join(HOME, ".openclaw/workspace/scripts/idle-journal.sh")
t = open(JP, encoding="utf-8", errors="ignore").read()
i = t.find("def call_llm():")
m = re.search(r"\n\s*def\s", t[i+1:]); end = i+1+m.start() if m else i+1500
seg = t[i:end]
if "reasoning_effort" in seg:
    print("already on"); raise SystemExit(0)
mm = re.search(r'"model":\s*"google/gemma-4-12b-qat",', seg)
if not mm:
    print("model line not found in call_llm"); raise SystemExit(1)
new = t[:i] + seg[:mm.end()] + '"reasoning_effort":"low",' + seg[mm.end():] + t[end:]
bak = JP + ".bak-reason-" + time.strftime("%Y%m%d-%H%M%S")
shutil.copy2(JP, bak); open(JP, "w", encoding="utf-8").write(new)
c = subprocess.run(["bash", "-n", JP], capture_output=True, text=True)
if c.returncode: shutil.copy2(bak, JP); print("bash -n failed, reverted"); raise SystemExit(1)
print("reasoning ON for a1/b1 | backup saved | next locked run (9am) will show it")
