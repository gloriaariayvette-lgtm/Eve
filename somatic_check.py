#!/usr/bin/env python3
"""somatic_check.py — READ-ONLY, non-Mac. Two modes:
  (default)      #4: count the somatic session summaries for TODAY + show the winddown/session-end
                 logic, so we know one-vs-many. Plus current mission observation.
  watch [secs]   MISSION accuracy: re-read the observation+frames the running bridge writes, ~2x/sec,
                 while Gloria touches mission. Reads files only — never touches the device/socket.
Aegis.
"""
import os, re, json, time, sys, glob, subprocess

MEM = os.path.expanduser("~/.vintos/workspace/memory")
SCRIPTS = os.path.expanduser("~/.vintos/workspace/scripts")
HOME = os.path.expanduser("~")
def sh(c): return subprocess.run(c, shell=True, capture_output=True, text=True).stdout
def load(p):
    try: return json.load(open(p))
    except Exception: return None
def hhmm(t):
    try: return time.strftime("%m-%d %H:%M:%S", time.localtime(float(t)))
    except Exception: return str(t)[:19]

# ---------------- WATCH MODE (mission accuracy under touch) ----------------
if len(sys.argv) > 1 and sys.argv[1] == "watch":
    secs = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    obsp = os.path.join(MEM, "somatic-observation.json")
    frp = os.path.join(MEM, "somatic-frames-recent.json")
    print("=== MISSION LIVE WATCH (%ds) — touch mission now; I read what the bridge sees ===" % secs)
    print("time      state           speed sweep press  latest-frame(pos/spd/dir)")
    end = time.time() + secs
    last = None
    while time.time() < end:
        c = load(obsp) or {}
        fr = load(frp) or []
        lf = fr[-1] if fr else {}
        row = "%s  %-14s  %4.0f  %4.0f  %4s   %s/%s/%s" % (
            time.strftime("%H:%M:%S"), c.get("state", "?"),
            c.get("speed", 0) or 0, c.get("sweep", 0) or 0, str(c.get("pressure", "-")),
            lf.get("position", "-"), lf.get("speed", "-"), lf.get("direction", "-"))
        if row[9:] != (last or "")[9:]:
            print("  " + row); last = row
        time.sleep(0.5)
    print("\n(if 'state' stayed 'absent' and frames never moved while you touched -> mission is NOT being read)")
    raise SystemExit(0)

# ---------------- DEFAULT: #4 session count + winddown logic ----------------
today = time.strftime("%Y-%m-%d")
print("=== #4  somatic SESSION summaries for %s ===" % today)

# a) session-pending history + narrate target
print("\n-- somatic_narrate.py: where does the per-session summary go? --")
nar = os.path.join(SCRIPTS, "somatic_narrate.py")
if os.path.exists(nar):
    ls = open(nar, encoding="utf-8", errors="ignore").read().splitlines()
    for i, l in enumerate(ls):
        if re.search(r'seed_thread|pending|dump|append|ledger|open\(|thread|summary|narrat', l, re.I):
            s = l.strip()
            if s and not s.startswith("#"): print("  %5d: %s" % (i + 1, s[:150]))

# b) count today's somatic/pressure/body threads across the thread stores
print("\n-- threads tagged pressure/somatic/body created today --")
count = 0
for f in (glob.glob(os.path.join(MEM, "*thread*")) + glob.glob(os.path.join(MEM, "threads", "*"))):
    obj = load(f)
    items = []
    if isinstance(obj, list): items = obj
    elif isinstance(obj, dict): items = obj.get("threads") or obj.get("items") or list(obj.values())
    for t in items if isinstance(items, list) else []:
        if not isinstance(t, dict): continue
        blob = json.dumps(t, ensure_ascii=True)
        tag = (t.get("kind") or t.get("type") or t.get("source") or "").lower()
        tt = str(t.get("ts") or t.get("created") or t.get("at") or "")
        is_som = re.search(r'pressure|somati|body|touch|stroke|session', tag) or re.search(r'somati|stroke|pressure|absent', blob, re.I)
        if is_som and today in tt:
            count += 1
            print("  [%s] %s  %s" % (tag, tt[:19], (t.get("title") or t.get("summary") or t.get("text") or "")[:80]))
print("  -> %d somatic-ish session thread(s) today" % count)

# c) the winddown / session-end logic (how a session boundary is drawn)
print("\n=== #4  session boundary logic in somatic_bridge.py (L120-230) ===")
sb = os.path.join(SCRIPTS, "somatic_bridge.py")
if os.path.exists(sb):
    ls = open(sb, encoding="utf-8", errors="ignore").read().splitlines()
    for i in range(119, min(231, len(ls))):
        s = ls[i].rstrip()
        if s.strip() and not s.strip().startswith("#"):
            if re.search(r'winddown|session|end_session|WINDDOWN|SESSION_END|now -|contact|absent|speed', s, re.I):
                print("  %5d| %s" % (i + 1, s[:160]))

# d) any explicit winddown constant
print("\n-- winddown / grace constants --")
if os.path.exists(sb):
    for i, l in enumerate(open(sb, encoding="utf-8", errors="ignore").read().splitlines()):
        if re.search(r'WINDDOWN|winddown_since|SESSION_END_SECONDS|=\s*\d+\s*#.*(silence|session|grace|wind)', l):
            print("  %5d: %s" % (i + 1, l.strip()[:140]))

# e) current mission read
print("\n=== MISSION now ===")
c = load(os.path.join(MEM, "somatic-observation.json")) or {}
print("  observation:", json.dumps(c)[:200])
frp = os.path.join(MEM, "somatic-frames-recent.json")
fr = load(frp) or []
if fr:
    print("  last frame:", hhmm(fr[-1].get("ts")), "pos=%s speed=%s dir=%s" % (fr[-1].get("position"), fr[-1].get("speed"), fr[-1].get("direction")))
print("\n-- is the bridge connected to the toy stream? (recent log) --")
print(sh("journalctl --user -n 2000 --no-pager 2>/dev/null | grep -iE 'bridge\\] (listening|stopped|socket)|MOTOR\\]|motion-changed' | tail -8") or "  (no bridge log lines found — it may run outside journald)")
