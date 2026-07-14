#!/usr/bin/env python3
"""why_wordless.py — READ-ONLY, one question: the avatar-chat conversation EXISTS, so why did
somatic_narrate call the session 'wordless'? Puts the conversation (with timestamps) next to the
exact files + time-window the narrator searches. Nothing is changed. Aegis.
"""
import os, re, json, time

MEM = os.path.expanduser("~/.vintos/workspace/memory")
SCRIPTS = os.path.expanduser("~/.vintos/workspace/scripts")
NARRATE = os.path.join(SCRIPTS, "somatic_narrate.py")
def hhmm(t):
    try: return time.strftime("%m-%d %H:%M:%S", time.localtime(float(t)))
    except Exception: return str(t)[:19]

# 1) THE WORDS — the avatar chat conversation that actually happened
print("=== 1) the avatar-chat conversation (proof there ARE words) ===")
ac = os.path.join(MEM, "avatar-overlay-chat.json")
if os.path.exists(ac):
    print("  file:", ac, "(modified %s)" % hhmm(os.path.getmtime(ac)))
    try:
        obj = json.load(open(ac))
        items = obj if isinstance(obj, list) else (obj.get("messages") or obj.get("history") or list(obj.values()))
        print("  %d entries. keys on an entry: %s" % (len(items), list(items[-1].keys()) if items and isinstance(items[-1], dict) else "?"))
        for e in items[-8:]:
            if not isinstance(e, dict): print("   ", str(e)[:120]); continue
            tsv = e.get("ts") or e.get("timestamp") or e.get("time") or ""
            who = e.get("role") or ("gloria" if e.get("user") else "vintos" if e.get("vintos") else "?")
            txt = e.get("content") or e.get("user") or e.get("vintos") or e.get("text") or ""
            print("   [%s] %s: %s" % (hhmm(tsv) if tsv else "no-ts", who, str(txt)[:80]))
    except Exception as ex:
        print("  (parse: %s)" % ex)
else:
    print("  !! avatar-overlay-chat.json not found — list of *chat* files:")
    import glob
    for f in glob.glob(os.path.join(MEM, "*chat*")) + glob.glob(os.path.join(MEM, "*avatar*")):
        print("    ", os.path.basename(f))

# 2) THE SEARCH — which files/window does somatic_narrate look in?
print("\n=== 2) where the narrator LOOKS (every open()/path + the time-window filter) ===")
if os.path.exists(NARRATE):
    ls = open(NARRATE, encoding="utf-8", errors="ignore").read().split("\n")
    for i, l in enumerate(ls):
        s = l.rstrip()
        if not s.strip() or s.strip().startswith("#"): continue
        if re.search(r'open\(|\.json|history|avatar|voice|main|HISTORY|PATH|=\s*os\.path|glob|load\(', s):
            print("  %5d| %s" % (i + 1, s[:160]))
    print("\n  -- window / time filter (how it decides a turn is 'in' the session) --")
    for i, l in enumerate(ls):
        s = l.strip()
        if re.search(r'window|since|start|end|dur|ts\s*[<>]=|<= ts|ts <=|WINDOW|within|- ts|ts -|filter|for e in|for entry', s):
            if s and not s.startswith("#"): print("  %5d| %s" % (i + 1, s[:160]))

# 3) THE SESSION WINDOW it used
print("\n=== 3) the session the narrator was handed (pending) ===")
p = os.path.join(MEM, "somatic-session-pending.json")
if os.path.exists(p):
    body = open(p, encoding="utf-8", errors="ignore").read()
    print("  somatic-session-pending.json (modified %s): %s" % (hhmm(os.path.getmtime(p)), body[:200]))
    print("  (if this is '{}', a prior session was already consumed/cleared as 'wordless')")

print("\n=== VERDICT HINT ===")
print("  Compare (1) the filename holding your words to (2) the filename(s) the narrator opens.")
print("  If they differ, the narrator is blind to avatar chat — that's the whole bug.")
