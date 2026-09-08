#!/usr/bin/env python3
"""somatic_mission_recon.py — READ-ONLY, no Mac, no rebuild. Two questions:
 #4  When the toy loops ran out / devices stopped, did it log ONE somatic session or SEVERAL?
     -> find who WRITES somatic sessions/episodes, and show the records around the last run.
 MISSION  Is mission reading accurately again? -> find who produces the position frames + what
     mission's live reading looks like vs what was set. Fires nothing, touches nothing. Aegis.
"""
import os, re, glob, json, time, subprocess

SCRIPTS = os.path.expanduser("~/.vintos/workspace/scripts")
MEM = os.path.expanduser("~/.vintos/workspace/memory")
HOME = os.path.expanduser("~")
def sh(c): return subprocess.run(c, shell=True, capture_output=True, text=True).stdout
def ts(t):
    try: return time.strftime("%m-%d %H:%M:%S", time.localtime(float(t)))
    except Exception: return str(t)

# ---------- who writes the somatic session / episode records? ----------
print("=== #4  who WRITES somatic sessions/episodes (grep scripts) ===")
for key in ("somatic-episodes", "somatic-session", "somatic-frames-recent", "session-arc"):
    hits = sh("grep -rln %r %s 2>/dev/null" % (key, SCRIPTS)).split()
    print("  writes/uses %-24s -> %s" % (key, ", ".join(os.path.basename(h) for h in hits) or "(none in scripts)"))

# show the session open/close logic in whichever script owns episodes
owner = (sh("grep -rl 'somatic-episodes' %s 2>/dev/null" % SCRIPTS).split() or
         sh("grep -rl 'somatic-session' %s 2>/dev/null" % SCRIPTS).split())
for f in owner[:2]:
    print("\n=== session logic in %s ===" % os.path.basename(f))
    ls = open(f, encoding="utf-8", errors="ignore").read().splitlines()
    for i, l in enumerate(ls):
        if re.search(r'session|episode|new_session|start|end|flush|gap|idle|append|dump|absent|pending|GAP|SETTLE|stop', l, re.I):
            s = l.strip()
            if s and not s.startswith("#"): print("  %5d: %s" % (i + 1, s[:150]))

# ---------- the actual records around the last run ----------
print("\n=== #4  somatic-episodes.jsonl (every entry, with time) ===")
ep = os.path.join(MEM, "somatic-episodes.jsonl")
if os.path.exists(ep):
    for line in open(ep, encoding="utf-8", errors="ignore"):
        line = line.strip()
        if not line: continue
        try:
            o = json.loads(line)
            print("  %s  intent=%s target=%s tempo=%s" % (o.get("ts"), o.get("intent"), o.get("target"), o.get("tempo")))
        except Exception: print("  " + line[:120])
else:
    print("  (none)")

print("\n=== #4  interaction-ledger: recent somatic/session entries ===")
led = os.path.join(MEM, "interaction-ledger.json")
if os.path.exists(led):
    try:
        L = json.load(open(led))
        rows = L if isinstance(L, list) else L.get("entries", [])
        somrows = [e for e in rows if re.search(r'somatic|device|toy|session|absent|stop', json.dumps(e), re.I)]
        print("  %d total entries, %d touch somatic/device; last 8 of those:" % (len(rows), len(somrows)))
        for e in somrows[-8:]:
            print("   " + json.dumps(e)[:190])
    except Exception as e: print("  (%s)" % e)
else:
    print("  (no interaction-ledger.json)")

print("\n=== #4  session/observation/pending state (mtime = when it last changed) ===")
for f in ("somatic-session-pending.json", "somatic-observation.json", "somatic-felt.json",
          "session-arc.json", "somatic-frames-recent.json"):
    p = os.path.join(MEM, f)
    if os.path.exists(p):
        try: body = json.dumps(json.load(open(p)))
        except Exception: body = open(p, encoding="utf-8", errors="ignore").read()
        print("  %-30s %s  ::  %s" % (f, ts(os.path.getmtime(p)), body[:160]))
    else:
        print("  %-30s (none)" % f)

# ---------- MISSION: who produces position frames + live reading ----------
print("\n=== MISSION  who produces the position frames (grep) ===")
prod = sh("grep -rln 'somatic-frames-recent\\|position\\|GetToys\\|\"depth\"\\|stroke' %s 2>/dev/null" % SCRIPTS).split()
for f in prod[:6]: print("  " + os.path.basename(f))

print("\n=== MISSION  how mission is read (grep the frame producer / bridge) ===")
for cand in ("somatic_bridge.py", "toy_link.py", "device_patterns.py", "device_context.py"):
    p = os.path.join(SCRIPTS, cand)
    if not os.path.exists(p): continue
    ls = open(p, encoding="utf-8", errors="ignore").read().splitlines()
    hit = [i for i, l in enumerate(ls) if re.search(r'mission|position|depth|GetToys|status|battery|frame|read|poll', l, re.I)]
    if not hit: continue
    print("\n  -- %s --" % cand)
    shown = []
    for i in hit:
        if any(abs(i - s) < 2 for s in shown): continue
        shown.append(i)
        s = ls[i].strip()
        if s and not s.startswith("#"): print("    %5d: %s" % (i + 1, s[:150]))
        if len(shown) > 24: break

print("\n=== MISSION  live vs set right now ===")
dsp = os.path.join(MEM, "device-state.json")
if os.path.exists(dsp):
    print("  device-state.json:", json.dumps(json.load(open(dsp)))[:240])
# device_context STATE (what the model is told mission is doing)
dcp = os.path.join(SCRIPTS, "device_context.py")
if os.path.exists(dcp):
    m = re.search(r'STATE\s*=\s*[\'"]([^\'"]+)[\'"]', open(dcp, encoding="utf-8", errors="ignore").read())
    if m and os.path.exists(m.group(1)):
        try: print("  device_context STATE:", json.dumps(json.load(open(m.group(1))))[:240])
        except Exception as e: print("  device_context STATE: (%s)" % e)

print("\n=== MISSION  recent frames (are positions changing / realistic?) ===")
fp = os.path.join(MEM, "somatic-frames-recent.json")
if os.path.exists(fp):
    try:
        fr = json.load(open(fp))
        for f in fr[-10:]:
            print("   %s  pos=%s speed=%s dir=%s" % (ts(f.get("ts")), f.get("position"), f.get("speed"), f.get("direction")))
    except Exception as e: print("  (%s)" % e)
