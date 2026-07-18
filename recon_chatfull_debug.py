#!/usr/bin/env python3
"""recon_chatfull_debug.py — Aegis, READ-ONLY. For a first-thought test that runs ON THE ORIGINAL CALL (full
context) but SAVES NOWHERE, find which route generates with full context yet persists NOTHING. Dump the two
candidates — chat_full_context (/api/chat/full) and debug_chat_message (/api/debug/chat-message) — showing: context
assembly, the generate call, and every write (chat-history / memory / json.dump / append / ledger). The one that
builds full context and writes nothing is the path the ephemeral test borrows. Nothing written."""
import os, re
SP = os.path.expanduser("~/Vintos/server.py")
if not os.path.isfile(SP):
    print("!! server.py not found"); raise SystemExit(1)
L = open(SP, encoding="utf-8", errors="ignore").read().split("\n")

def dump_fn(start_pat, tag, span=95):
    idx = next((i for i, l in enumerate(L) if re.search(start_pat, l)), None)
    if idx is None:
        print("\n== %s: NOT FOUND ==" % tag); return
    print("\n===== %s  (from line %d) =====" % (tag, idx + 1))
    end = min(idx + span, len(L))
    for i in range(idx, end):
        l = L[i]
        # stop at the next route def
        if i > idx + 3 and re.match(r'@app\.(post|get)', l): break
        if re.search(r'context|prompt|SOUL|self_model|self-model|relationship|assemble|build|messages\s*=|'
                     r'generate|bilateral|/v1/chat|requests\.post|urlopen|shim|8599|'
                     r'json\.dump|\.append|chat-history|save|write|ledger|persist|record', l, re.I):
            tagw = ""
            if re.search(r'json\.dump|\.append\(|save|write|chat-history|ledger|persist', l, re.I): tagw = "   <== WRITE?"
            print("  %5d: %s%s" % (i + 1, l.strip()[:96], tagw))

dump_fn(r'async def chat_full_context', "chat_full_context  (/api/chat/full)")
dump_fn(r'async def debug_chat_message', "debug_chat_message  (/api/debug/chat-message)")

print("\n(READ-ONLY. The full-context + writes-nothing route is what the ephemeral test borrows.)")
