#!/usr/bin/env python3
"""recon_chatfull_body.py — Aegis, READ-ONLY. Dump chat_full_context (/api/chat/full) verbatim — his 'COMPLETE
lived context' route — so the ephemeral first-thought test can REPLICATE its context assembly read-only (read the
same memory files, build the same system prompt) and reconsider as him, saving nowhere. Show the body until the
next route. Nothing written."""
import os, re
SP = os.path.expanduser("~/Vintos/server.py")
L = open(SP, encoding="utf-8", errors="ignore").read().split("\n")
start = next((i for i, l in enumerate(L) if re.search(r'async def chat_full_context', l)), None)
if start is None:
    print("!! chat_full_context not found"); raise SystemExit(1)
end = start + 150
for i in range(start + 3, min(start + 150, len(L))):
    if re.match(r'@app\.(post|get)', L[i]):
        end = i; break
print("===== chat_full_context  lines %d–%d =====" % (start + 1, end))
for i in range(start, end):
    print("%5d: %s" % (i + 1, L[i][:150]))
print("\n(READ-ONLY. Gives the exact files/sections to replicate read-only for a saves-nowhere, full-context test.)")
