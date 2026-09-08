#!/usr/bin/env python3
"""app_and_somatic_recon.py — READ-ONLY. Two jobs:
(A) LOCATE the app source on Aegis + the exact UI hooks I must patch for the batch
    (GCS button, chat-history persistence, avatar T-pose/emote, flicker/color, toy loop).
(B) SOMATIC #4: when the toy loops ran out and devices stopped, did it log ONE session or
    several 'somatic event' sessions? Dump the somatic/session state so we can see.
Touches nothing, fires nothing, no stop path. Aegis.
"""
import os, re, glob, json, subprocess, time

HOME = os.path.expanduser("~")
MEM = os.path.expanduser("~/.vintos/workspace/memory")
def sh(c): return subprocess.run(c, shell=True, capture_output=True, text=True).stdout

# ---------- (A) find the app source ----------
print("=== (A) app source (index.html / avatar) on this box ===")
cands = []
for root in (HOME,):
    cands += sh("find %s -maxdepth 5 -name 'index.html' 2>/dev/null | grep -viE 'node_modules|/ios/|/build/|dist' | head -20" % root).splitlines()
# also capacitor projects & avatar js
caps = sh("find %s -maxdepth 5 -iname 'capacitor.config.*' 2>/dev/null | grep -v node_modules | head -10" % HOME).splitlines()
for c in cands:
    if c.strip():
        print("  index.html: %s  (%dB, %s)" % (c, os.path.getsize(c), time.strftime("%m-%d %H:%M", time.localtime(os.path.getmtime(c)))))
for c in caps:
    if c.strip(): print("  capacitor:  %s" % c)
if not cands: print("  (no index.html found on Aegis — app source is only on the Mac)")

# pick the freshest, biggest index.html as the likely app and grep the hooks
main = None
best = -1
for c in cands:
    c = c.strip()
    if not c: continue
    try:
        sz = os.path.getsize(c)
        if ("vintos" in c.lower() or "app" in c.lower() or "openclaw" in c.lower()) and sz > best:
            best = sz; main = c
    except Exception: pass
if not main and cands: main = cands[0].strip()

if main and os.path.exists(main):
    print("\n=== the app file I'd patch: %s ===" % main)
    txt = open(main, encoding="utf-8", errors="ignore").read()
    ls = txt.splitlines()
    def show(label, pat):
        print("  -- %s --" % label)
        hit = [i for i, l in enumerate(ls) if re.search(pat, l, re.I)]
        seen = []
        for i in hit:
            if any(abs(i - s) < 3 for s in seen): continue
            seen.append(i)
            print("    %5d: %s" % (i + 1, ls[i].strip()[:150]))
        if not hit: print("    (no match for /%s/)" % pat)
    show("GCS button (#2)", r'gcs|great.?coming|/api/gcs|coherence')
    show("chat history render/persist (#1)", r'chat.?hist|renderMessage|messages\.push|localStorage|scrollHeight|avatar.?chat|chatLog|msgList')
    show("emote / T-pose (#5)", r't.?pose|tpose|emote|VRMA|animation|playAnim|expression|blendshape|pose')
    show("flicker / color change (#6)", r'flicker|background|bgColor|style\.background|color\s*=|hueshift|hsl|rgba')
    show("toy loop / hardware off (#3)", r'loop|hardware|toy|somatic|interval|setInterval|stop')
else:
    print("\n(no app index.html on Aegis to grep — I'll need the file from the Mac repo)")

# ---------- (B) somatic sessions #4 ----------
print("\n=== (B) somatic / session state — did loops-ending log multiple sessions? ===")
somfiles = sorted(set(
    glob.glob(os.path.join(MEM, "*somatic*")) +
    glob.glob(os.path.join(MEM, "*session*")) +
    glob.glob(os.path.join(MEM, "*device*")) +
    glob.glob(os.path.join(MEM, "*hardware*"))
))
for f in somfiles:
    print("\n  -- %s (%dB, %s) --" % (f.replace(HOME, "~"), os.path.getsize(f),
          time.strftime("%m-%d %H:%M", time.localtime(os.path.getmtime(f)))))
    try:
        obj = json.load(open(f))
        if isinstance(obj, list):
            print("     list of %d entries" % len(obj))
            for e in obj[-6:]:
                s = json.dumps(e)[:170]
                print("      " + s)
        elif isinstance(obj, dict):
            print("     " + json.dumps(obj)[:300])
    except Exception as e:
        # not json — show tail
        try:
            tail = open(f, encoding="utf-8", errors="ignore").read().splitlines()[-6:]
            for l in tail: print("      " + l[:170])
        except Exception as e2: print("     (%s)" % e2)
if not somfiles:
    print("  (no somatic/session/device/hardware files in memory)")

print("\n=== logs: somatic events + loop end + device stop ===")
logs = sh("journalctl --user -u vintos-server -n 800 --no-pager")
kept = [l for l in logs.splitlines() if re.search(r'somatic|session (start|end|new)|loop (end|out|done)|device.*stop|toy.*stop|patterns? (out|exhaust|end)', l, re.I)]
for l in kept[-25:]:
    print("  " + l[-160:])
if not kept: print("  (nothing — loop-end/device-stop may not be logged, or ran under a different unit)")
