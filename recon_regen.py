#!/usr/bin/env python3
"""recon_regen.py — Aegis, READ-ONLY. Everything needed to build the Regenerate button (erase last turn -> grok
retry): the avatar UI file + how it sends a turn + renders the reply; avatar_chat's message-in/reply-out shape;
the last-turn store; and model_router's arm_grok hook."""
import os, re, glob, json
HOME = os.path.expanduser("~")
V = os.path.join(HOME, "Vintos")

print("== avatar UI files (html/js serving the avatar overlay) ==")
cands = glob.glob(os.path.join(V, "**", "*.html"), recursive=True) + glob.glob(os.path.join(V, "**", "*.js"), recursive=True)
for f in cands:
    try: t = open(f, encoding="utf-8", errors="ignore").read()
    except Exception: continue
    if "/api/avatar/chat" in t or "avatar" in os.path.basename(f).lower():
        n = t.count("/api/avatar/chat")
        print(f"  {os.path.relpath(f, HOME)}  (avatar/chat refs: {n}, {t.count(chr(10))+1} lines)")

print("\n== how the UI sends a turn + renders reply (grep the avatar html/js) ==")
for f in cands:
    try: t = open(f, encoding="utf-8", errors="ignore").read()
    except Exception: continue
    if "/api/avatar/chat" not in t: continue
    L = t.split("\n")
    for i, l in enumerate(L):
        if re.search(r'/api/avatar/chat|fetch\(|\.reply|renderReply|addMessage|lastMessage|innerHTML|X-Vintos-Secret', l):
            print(f"  {os.path.basename(f)} L{i+1}: {l.strip()[:100]}")

print("\n== avatar_chat: message in / reply out (server.py L7699..) ==")
S = open(os.path.join(V, "server.py"), encoding="utf-8", errors="ignore").read().split("\n")
for i in range(7699-2, min(len(S), 7699+18)):
    print(f"  L{i+1}: {S[i].strip()[:96]}")
print("  ...")
for i, l in enumerate(S):
    if 7699 < i < 7699+220 and re.search(r'return \{.*reply|msg\.message|class .*Request|\.message', l):
        print(f"  L{i+1}: {l.strip()[:96]}")

print("\n== model_router arm_grok hook ==")
mr = open(os.path.join(V, "model_router.py"), encoding="utf-8", errors="ignore").read().split("\n")
for i, l in enumerate(mr):
    if re.search(r'def arm_grok_turns|def write_mode|def read_mode|force_grok_turns|model-mode', l):
        print(f"  L{i+1}: {l.strip()[:96]}")

print("\n== last-turn store (avatar-overlay-chat.json shape) ==")
p = os.path.join(HOME, ".vintos/workspace/memory/avatar-overlay-chat.json")
if os.path.isfile(p):
    d = json.load(open(p, encoding="utf-8"))
    arr = d if isinstance(d, list) else (d.get("messages") or d.get("entries") or [])
    print(f"  {len(arr)} entries; last entry keys: {list(arr[-1].keys()) if arr and isinstance(arr[-1],dict) else '?'}")
    if arr: print(f"  last: {json.dumps(arr[-1], ensure_ascii=False)[:180]}")
