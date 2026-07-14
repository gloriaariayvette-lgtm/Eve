#!/usr/bin/env python3
"""confirm_capture_fix.py — READ-ONLY. Show the two exact spots the capture fix will edit:
  (A) somatic_narrate.py gather_turns() — the CHAT_SOURCES list + how it parses an entry (role/content
      vs user/vintos) + the ts filter.
  (B) server.py — where /api/avatar/chat appends to avatar-overlay-chat.json (to add a ts there).
Nothing changed. Aegis.
"""
import os, re

SCRIPTS = os.path.expanduser("~/.vintos/workspace/scripts")
NARRATE = os.path.join(SCRIPTS, "somatic_narrate.py")
SERVER = os.path.expanduser("~/Vintos/server.py")

print("=== (A) somatic_narrate.py — CHAT_SOURCES + gather_turns() body (L20-60) ===")
if os.path.exists(NARRATE):
    ls = open(NARRATE, encoding="utf-8", errors="ignore").read().split("\n")
    for i in range(19, min(62, len(ls))):
        print("  %5d| %s" % (i + 1, ls[i][:170]))

print("\n=== (B) server.py — where avatar-overlay-chat.json is written ===")
if os.path.exists(SERVER):
    sl = open(SERVER, encoding="utf-8", errors="ignore").read().split("\n")
    hits = [i for i, l in enumerate(sl) if "avatar-overlay-chat" in l]
    print("  lines mentioning avatar-overlay-chat.json:", [h + 1 for h in hits])
    shown = []
    for h in hits:
        if any(abs(h - s) < 6 for s in shown): continue
        shown.append(h)
        print("\n  -- around L%d --" % (h + 1))
        for k in range(max(0, h - 8), min(h + 6, len(sl))):
            s = sl[k].rstrip()
            if s.strip(): print("   %5d| %s" % (k + 1, s[:170]))
    if not hits:
        print("  (not found by that name — searching 'avatar' + append/dump)")
        for i, l in enumerate(sl):
            if re.search(r'avatar.*chat.*(append|dump|open\()|append.*avatar', l, re.I):
                print("   %5d| %s" % (i + 1, l.strip()[:170]))

print("\n=== the conversation entry shape (so I match role->who correctly) ===")
import json
ac = os.path.expanduser("~/.vintos/workspace/memory/avatar-overlay-chat.json")
if os.path.exists(ac):
    try:
        obj = json.load(open(ac)); items = obj if isinstance(obj, list) else list(obj.values())
        print("  sample entry:", json.dumps(items[-1])[:160] if items else "(empty)")
    except Exception as e: print("  (%s)" % e)
