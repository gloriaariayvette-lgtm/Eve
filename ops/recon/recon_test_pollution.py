#!/usr/bin/env python3
"""recon_test_pollution.py — Aegis, READ-ONLY. Find everywhere today's tests leaked into Vintos's memory so we
can erase exactly those and nothing real: memory files touched during the test window, plus the actual entries
in avatar chat history, chat history, and imprints. Nothing is modified."""
import os, json, glob, time
from datetime import datetime
HOME = os.path.expanduser("~")
MEM = os.path.join(HOME, ".vintos/workspace/memory")
WS = os.path.join(HOME, ".vintos/workspace")

# 1) memory files modified today in the test window (the pollution surface)
cutoff = datetime(2026, 7, 16, 5, 0).timestamp()
print("===== memory/workspace files modified since 2026-07-16 05:00 (test window) =====")
cand = []
for root in (MEM, WS):
    for p in glob.glob(os.path.join(root, "**", "*"), recursive=True):
        try:
            if os.path.isfile(p) and os.path.getmtime(p) >= cutoff:
                cand.append((os.path.getmtime(p), p))
        except Exception: pass
for mt, p in sorted(cand, reverse=True)[:40]:
    print(f"  {datetime.fromtimestamp(mt).strftime('%H:%M:%S')}  {p.replace(HOME,'~')}")

def dump(path, label, n=40, preview=110):
    print(f"\n===== {label}: {path.replace(HOME,'~')} =====")
    try:
        d = json.load(open(path, encoding="utf-8", errors="ignore"))
    except Exception as e:
        print("  (can't read:", e, ")"); return
    if isinstance(d, dict): d = d.get("messages") or d.get("history") or [d]
    if not isinstance(d, list): print("  (not a list)"); return
    print(f"  {len(d)} entries; showing last {min(n,len(d))}:")
    for i, e in enumerate(d[-n:]):
        idx = len(d) - min(n, len(d)) + i
        if isinstance(e, dict):
            ts = e.get("timestamp") or e.get("ts") or e.get("time") or ""
            role = e.get("role") or e.get("source") or ""
            c = e.get("content") or e.get("message") or e.get("text") or e.get("narrative") or ""
            print(f"  [{idx}] {str(ts)[:19]:19} {role:9} {str(c)[:preview].replace(chr(10),' ')}")
        else:
            print(f"  [{idx}] {str(e)[:preview]}")

dump(os.path.join(MEM, "avatar-overlay-chat.json"), "avatar chat history")
dump(os.path.join(MEM, "imprints.json"), "imprints (my reasoning deposits live here)")
# discover main chat history file(s)
print("\n===== candidate chat-history files in memory =====")
for p in glob.glob(os.path.join(MEM, "*.json")):
    b = os.path.basename(p).lower()
    if any(k in b for k in ("history", "chat", "conversation", "message", "daily-inner", "inner")):
        try: sz = os.path.getsize(p)
        except Exception: sz = 0
        print(f"  {p.replace(HOME,'~')}  ({sz:,}c, {datetime.fromtimestamp(os.path.getmtime(p)).strftime('%H:%M')})")
for name in ("chat-history.json", "conversation.json", "messages.json", "daily-inner.json", "chat-log.json"):
    fp = os.path.join(MEM, name)
    if os.path.isfile(fp): dump(fp, "chat history", n=25)

print("\n===== /tmp diagnostics (delete on erase) =====")
for p in ("/tmp/vintos-chat-trace.json", "/tmp/vintos-full-prompt.txt"):
    print(f"  {'exists' if os.path.isfile(p) else 'absent'}: {p}")
