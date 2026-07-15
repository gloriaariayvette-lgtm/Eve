#!/usr/bin/env python3
"""recon_journal_gate.py — Aegis, READ-ONLY. The journal run no-op'd (old entry, no a1/b1 drafts). Find its
early-exit gates (idle check, cooldown, lock, time window) so we can force a real test run that reaches the
bilateral a1/b1 path. Dumps head + every exit/return/lock/cooldown condition with context."""
import os, re
HOME = os.path.expanduser("~")
P = os.path.join(HOME, ".openclaw/workspace/scripts/idle-journal.sh")
def sh(p): return p.replace(HOME, "~")
lines = open(P, encoding="utf-8", errors="ignore").read().split("\n")

print("=== head (first 55 lines) ===")
for i, l in enumerate(lines[:55]):
    if l.strip(): print(f"  {i+1}| {l.rstrip()[:120]}")

print("\n=== exit / return / continue guards + their nearby condition ===")
for i, l in enumerate(lines):
    if re.search(r'\bexit\b|\breturn\b|lock|cooldown|idle|last.?run|LAST_|sleep|flock|already|\bcap\b|>= ?\d|too soon|recent', l, re.I) and l.strip() \
       and not l.strip().startswith("#"):
        print(f"  {i+1}| {l.strip()[:120]}")
print("\n(done — point me at the gate and I'll craft a forced test invocation)")
