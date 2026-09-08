#!/usr/bin/env python3
"""compare_journal_intro.py — Aegis, READ-ONLY, terse. Journals work at ~19k tok; introspection is ~37k for
the same job. Find what introspection carries that the journal doesn't. Compare how each pulls chat/ledger,
and list the memory files each reads (so we align introspection to the journal's proven-lean set)."""
import os, re
HOME = os.path.expanduser("~")
SC = os.path.join(HOME, ".openclaw/workspace/scripts")
J = os.path.join(SC, "idle-journal.sh")
I = os.path.join(SC, "introspection.sh")
def files_read(p):
    t = open(p, encoding="utf-8", errors="ignore").read()
    fs = set(re.findall(r'memory/([A-Za-z0-9._-]+)\b', t))
    return fs, t
jf, jt = files_read(J); iff, it = files_read(I)
print("== chat/ledger handling ==")
print("JOURNAL:")
for i, l in enumerate(jt.split("\n")):
    if re.search(r'chat-history|interaction-ledger|recent_chat|RECENT_CHAT|\[-\d+:\]|\[:\d+\]', l) and l.strip():
        print(f"  {i+1}: {l.strip()[:92]}")
print("INTROSPECTION:")
for i, l in enumerate(it.split("\n")):
    if re.search(r'chat-history|interaction-ledger|recent_chat|\[-20:\]|last 20', l) and l.strip():
        print(f"  {i+1}: {l.strip()[:92]}")
print("\n== files introspection reads that the JOURNAL does NOT ==")
for f in sorted(iff - jf):
    fp = os.path.join(HOME, ".openclaw/workspace/memory", f)
    sz = os.path.getsize(fp) if os.path.isfile(fp) else 0
    print(f"  {sz:>8,}B  {f}")
