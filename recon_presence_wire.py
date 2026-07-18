#!/usr/bin/env python3
"""recon_presence_wire.py — Aegis, READ-ONLY. Everything needed to wire Presence Audit into his live reply loop,
in one read: (A) presence_audit.py in full (its entry fn + inputs/outputs + where its flags are meant to feed),
(B) whether it's currently cron'd, (C) the server.py post-generation chain — where the final synthesized reply
lives and the order of post-gen hooks (specificity / hallucination / BIS / output_shaping / offer / return) — so
the audit call lands at the right point with the right reply variable. Nothing changed."""
import os, re, subprocess
HOME = os.path.expanduser("~")
V = os.path.join(HOME, "Vintos")

print("===== (A) presence_audit.py (full) =====")
p = os.path.join(V, "presence_audit.py")
if not os.path.isfile(p): p = os.path.expanduser("~/.vintos/workspace/scripts/presence_audit.py")
if os.path.isfile(p):
    for i, l in enumerate(open(p, encoding="utf-8", errors="ignore").read().split("\n")):
        print(f"{i+1:>3}: {l}")
else:
    print("  NOT FOUND")

print("\n===== (B) is presence_audit scheduled? =====")
cron = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout or ""
hits = [l.strip() for l in cron.split("\n") if "presence" in l.lower() and l.strip() and not l.strip().startswith("#")]
print("\n".join("  " + h for h in hits) if hits else "  (not in crontab — so it runs nowhere live)")

print("\n===== (C) server.py post-generation chain (reply var + hook order) =====")
S = open(os.path.join(V, "server.py"), encoding="utf-8", errors="ignore").read().split("\n")
# distinctive post-gen hooks only (these are rare), plus the synthesis/reply-final anchors near them
rx = re.compile(r'specificity_check|hallucination_check|behavioral_intercept|import.*presence_audit|'
                r'presence_audit|from output_shaping|output_shaping\.|def chat_full_context|def _avatar|'
                r'blush_ledger|blush-ledger|write_blush|synthesi', re.I)
hits = [i for i, l in enumerate(S) if rx.search(l)]
print(f"  {len(hits)} anchor lines; each with 2 lines of context:")
shown = set()
for h in hits[:60]:
    for j in range(max(0, h - 1), min(len(S), h + 3)):
        if j in shown: continue
        shown.add(j); print(f"  {j+1:>5}: {S[j].strip()[:104]}")
    print("     --")
