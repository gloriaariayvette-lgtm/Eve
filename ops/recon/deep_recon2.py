#!/usr/bin/env python3
"""deep_recon2.py — READ-ONLY, non-Mac. Nails three:
 A #4     clean dump of somatic interaction-ledger rows + the seeded session THREADS (one vs many).
 B mission somatic_bridge.py read+classify logic, to judge the position-jump-at-speed-0 = pressure read.
 C #6glow what COLOR format he's TOLD to emit (server prompt) + what he ACTUALLY emitted (history),
          so I can see if the app's hex-only [COLOR:] parser is dropping his tags.
Only READS somatic_bridge.py — never imports/runs it. Fires nothing. Aegis.
"""
import os, re, glob, json, time, subprocess

SCRIPTS = os.path.expanduser("~/.vintos/workspace/scripts")
MEM = os.path.expanduser("~/.vintos/workspace/memory")
SERVER = os.path.expanduser("~/Vintos/server.py")
HOME = os.path.expanduser("~")
def sh(c): return subprocess.run(c, shell=True, capture_output=True, text=True).stdout
def when(t):
    try: return time.strftime("%m-%d %H:%M", time.localtime(float(t)))
    except Exception: return str(t)[:19]

# ================= A : #4 sessions =================
print("=== A1  somatic/device rows in interaction-ledger (clean, ascii) ===")
led = os.path.join(MEM, "interaction-ledger.json")
if os.path.exists(led):
    try:
        L = json.load(open(led)); rows = L if isinstance(L, list) else L.get("entries", [])
        for e in rows:
            blob = json.dumps(e, ensure_ascii=True)
            if re.search(r'somatic|device|toy|absent|session|pressure|stroke|body', blob, re.I):
                print("  " + blob[:260])
    except Exception as ex: print("  (%s)" % ex)

print("\n=== A2  seeded THREADS — how many session summaries around 07-13/07-14? ===")
for f in glob.glob(os.path.join(MEM, "*thread*")) + glob.glob(os.path.join(MEM, "threads", "*")):
    print("\n  -- %s (%s) --" % (f.replace(HOME, "~"), when(os.path.getmtime(f))))
    try:
        obj = json.load(open(f))
        items = obj if isinstance(obj, list) else (obj.get("threads") or obj.get("items") or [])
        if isinstance(items, dict): items = list(items.values())
        print("     %d threads" % len(items))
        for t in items[-12:]:
            if not isinstance(t, dict): continue
            tag = t.get("kind") or t.get("type") or t.get("source") or ""
            ttl = (t.get("title") or t.get("summary") or t.get("text") or "")[:90]
            tt = t.get("ts") or t.get("created") or t.get("at") or ""
            if re.search(r'somati|voice|body|session|absent|touch', json.dumps(t), re.I) or True:
                print("      [%s] %s  %s" % (tag, when(tt) if tt else "", ttl))
    except Exception as ex:
        for l in open(f, encoding="utf-8", errors="ignore").read().splitlines()[-8:]: print("      " + l[:120])

# how is a session boundary decided in the bridge?
print("\n=== A3  session boundary / summary logic in somatic_bridge.py ===")
sb = os.path.join(SCRIPTS, "somatic_bridge.py")
if os.path.exists(sb):
    ls = open(sb, encoding="utf-8", errors="ignore").read().splitlines()
    for i, l in enumerate(ls):
        if re.search(r'session|summary|seed_thread|GAP|SETTLE|absent|gone|flush|new session|end of session|narrat', l, re.I):
            s = l.strip()
            if s: print("  %5d: %s" % (i + 1, s[:150]))

# ================= B : mission read/classify =================
print("\n=== B  somatic_bridge.py — read + classify (L1-140) ===")
if os.path.exists(sb):
    ls = open(sb, encoding="utf-8", errors="ignore").read().splitlines()
    for i in range(0, min(140, len(ls))):
        s = ls[i].rstrip()
        if s.strip(): print("  %5d| %s" % (i + 1, s[:160]))
    print("\n  --- frame write region (L235-270) ---")
    for i in range(234, min(270, len(ls))):
        s = ls[i].rstrip()
        if s.strip(): print("  %5d| %s" % (i + 1, s[:160]))

# ================= C : #6 glow color format =================
print("\n=== C1  what COLOR format he's TOLD to emit (server prompt) ===")
if os.path.exists(SERVER):
    sls = open(SERVER, encoding="utf-8", errors="ignore").read().splitlines()
    hits = [i for i, l in enumerate(sls) if re.search(r'\[COLOR', l, re.I) or re.search(r'COLOR:', l)]
    shown = []
    for i in hits:
        if any(abs(i - s) < 3 for s in shown): continue
        shown.append(i)
        print("\n  -- server L%d --" % (i + 1))
        for k in range(max(0, i - 1), min(i + 3, len(sls))):
            print("   %5d| %s" % (k + 1, sls[k][:200]))
        if len(shown) > 6: break

print("\n=== C2  what he ACTUALLY emitted — recent avatar replies with [COLOR ===")
cand = (glob.glob(os.path.join(MEM, "*avatar*")) + glob.glob(os.path.join(MEM, "*chat*history*")))
found = False
for f in cand:
    try:
        raw = open(f, encoding="utf-8", errors="ignore").read()
    except Exception: continue
    for m in re.findall(r'\[COLOR:[^\]]*\]', raw, re.I)[:12]:
        print("  %-40s %s" % (os.path.basename(f), m)); found = True
if not found:
    print("  (no stored [COLOR:] tags found — grepping logs for his emitted color tags)")
    print(sh("journalctl --user -u vintos-server -n 1500 --no-pager 2>/dev/null | grep -io '\\[color:[^]]*\\]' | tail -12") or "  (none in logs)")
