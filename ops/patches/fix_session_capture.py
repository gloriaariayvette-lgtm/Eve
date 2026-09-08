#!/usr/bin/env python3
"""fix_session_capture.py — the real fix. somatic_narrate was blind to avatar chat:
  (1) CHAT_SOURCES named 'avatar-chat-history.json' (doesn't exist) — the words are in
      'avatar-overlay-chat.json'. Add it (first, so it's preferred).
  (2) avatar entries have no per-turn timestamp -> they failed the time filter. Fall back to the
      file's mtime so the conversation lands in the session window.
Narrator only. Backup + anchored + idempotent. Takes effect on the next cron run. Aegis.
"""
import os, time, shutil

NAR = os.path.expanduser("~/.vintos/workspace/scripts/somatic_narrate.py")
src = open(NAR, encoding="utf-8").read()
orig = src

OLD_SRCS = 'CHAT_SOURCES = ("avatar-chat-history.json", "voice-chat-history.json", "chat-history.json")'
NEW_SRCS = 'CHAT_SOURCES = ("avatar-overlay-chat.json", "avatar-chat-history.json", "voice-chat-history.json", "chat-history.json")'

OLD_LOOP = '''    for fn in CHAT_SOURCES:
        d = load(os.path.join(MEMORY, fn), [])
        if not isinstance(d, list): continue
        for e in d:
            if not isinstance(e, dict): continue
            ts = to_epoch(e.get("timestamp") or e.get("ts") or e.get("time") or e.get("at"))
            if ts is None or not (start - PAD <= ts <= end + PAD): continue'''
NEW_LOOP = '''    for fn in CHAT_SOURCES:
        _fp = os.path.join(MEMORY, fn)
        d = load(_fp, [])
        if not isinstance(d, list): continue
        try: _fmtime = os.path.getmtime(_fp)
        except Exception: _fmtime = None
        for e in d:
            if not isinstance(e, dict): continue
            ts = to_epoch(e.get("timestamp") or e.get("ts") or e.get("time") or e.get("at"))
            if ts is None: ts = _fmtime          # avatar-overlay entries have no per-turn ts -> use file mtime
            if ts is None or not (start - PAD <= ts <= end + PAD): continue'''

problems = []
if "avatar-overlay-chat.json" in src and "_fmtime" in src:
    print("already fixed (idempotent) — nothing to do.")
else:
    if src.count(OLD_SRCS) != 1: problems.append("CHAT_SOURCES anchor x%d" % src.count(OLD_SRCS))
    if src.count(OLD_LOOP) != 1: problems.append("gather_turns loop anchor x%d" % src.count(OLD_LOOP))
    if problems:
        print("!! ABORTED — anchors off, file untouched:", problems)
    else:
        src = src.replace(OLD_SRCS, NEW_SRCS, 1).replace(OLD_LOOP, NEW_LOOP, 1)
        bak = NAR + ".bak-capture-" + time.strftime("%Y%m%d-%H%M%S")
        shutil.copy2(NAR, bak)
        open(NAR, "w", encoding="utf-8").write(src)
        print("applied. backup:", bak)

print("\n=== verify: CHAT_SOURCES + the mtime fallback now in place ===")
for i, l in enumerate(open(NAR, encoding="utf-8").read().split("\n")):
    if "CHAT_SOURCES =" in l or "_fmtime" in l or "avatar-overlay entries" in l:
        print("  %5d| %s" % (i + 1, l[:150]))

print("\nnext: somatic_narrate runs on its cron; the next session with conversation will seed a thread.")
print("the 02:45 conversation is still in avatar-overlay-chat.json — I can retro-seed that thread on request.")
