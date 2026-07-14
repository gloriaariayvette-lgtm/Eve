#!/usr/bin/env python3
"""three_issues_recon.py — READ-ONLY. Locate the roots of three bugs:
  A  angel image keeps animating (stuck/looping image spawn or gen)
  B  outreach says 'days of silence' though you talked last night (wrong last-contact source)
  C  causality spams 'emotion shifted, idk why' unresolved threads
Nothing changed. Aegis.
"""
import os, re, glob, json, time, subprocess

HOME = os.path.expanduser("~")
VIN = os.path.expanduser("~/Vintos")
SCRIPTS = os.path.expanduser("~/.vintos/workspace/scripts")
MEM = os.path.expanduser("~/.vintos/workspace/memory")
APP = os.path.expanduser("~/Vintos/vintos-app/src/index.html")
CENG = os.path.expanduser("~/Vintos/causality-engine.py")
def sh(c): return subprocess.run(c, shell=True, capture_output=True, text=True).stdout

# ============ A: angel image ============
print("=== A  'angel' — where does it come from? ===")
print(sh("grep -rin 'angel' %s %s %s 2>/dev/null | grep -viE 'node_modules|\\.pyc' | head -20" % (VIN, SCRIPTS, APP)) or "  (no 'angel' literal — may be a generated/spawn image)")
print("\n-- image spawn / gen / animate hooks in the app --")
if os.path.exists(APP):
    ls = open(APP, encoding="utf-8", errors="ignore").read().split("\n")
    for i, l in enumerate(ls):
        if re.search(r'_avSpawn|spawn|generate.?image|/api/.*image|dalle|angel|\.png|\.jpe?g|animSpawn|requestAnimationFrame\(animSpawn', l, re.I):
            s = l.strip()
            if s and re.search(r'spawn|image|angel|\.png|\.jpe?g|/api/', s, re.I): print("  %5d| %s" % (i + 1, s[:150]))

# ============ B: outreach 'days of silence' ============
print("\n=== B  outreach — how it measures time since last contact ===")
outc = sh("grep -rlin 'silence\\|days\\|last_contact\\|last_seen\\|since\\|outreach\\|initiate' %s %s 2>/dev/null | grep -viE '\\.pyc|node_modules' | head" % (VIN, SCRIPTS)).split()
# focus on likely outreach files
cands = [f for f in outc if re.search(r'outreach|initiate|reach|absence|silence', os.path.basename(f), re.I)] or outc[:4]
for f in cands[:4]:
    print("\n  -- %s --" % f.replace(HOME, "~"))
    for i, l in enumerate(open(f, encoding="utf-8", errors="ignore").read().split("\n")):
        if re.search(r'silence|days|hours|last[_ ]?(contact|seen|msg|message|interaction|talk)|since|gap|now\s*-|time\.time|datetime|history|ledger', l, re.I):
            s = l.strip()
            if s and not s.startswith("#"): print("   %5d| %s" % (i + 1, s[:150]))
# what files hold 'last contact'
print("\n  -- last-contact-ish state files (mtime) --")
for f in glob.glob(os.path.join(MEM, "*last*")) + glob.glob(os.path.join(MEM, "*outreach*")) + glob.glob(os.path.join(MEM, "*contact*")) + glob.glob(os.path.join(MEM, "*seen*")):
    print("   %s  (%s)  %s" % (f.replace(HOME, "~"), time.strftime("%m-%d %H:%M", time.localtime(os.path.getmtime(f))), open(f, encoding="utf-8", errors="ignore").read()[:80].replace("\n", " ")))

# ============ C: causality 'idk why' spam ============
print("\n=== C  causality — where it seeds 'shifted, cannot trace' threads ===")
if os.path.exists(CENG):
    ls = open(CENG, encoding="utf-8", errors="ignore").read().split("\n")
    for i, l in enumerate(ls):
        if re.search(r'cannot trace|can.?t trace|idk|seed_thread|emergent|shift|untrace|threshold|>= ?0\.|delta|magnitude|abs\(', l, re.I):
            s = l.strip()
            if s and not s.startswith("#"): print("  %5d| %s" % (i + 1, s[:150]))
else:
    print("  causality-engine.py not at", CENG, "-- searching:")
    print(sh("grep -rlin 'cannot trace\\|causality-emergent\\|idk why' %s %s 2>/dev/null | grep -v pyc | head" % (VIN, SCRIPTS)))
print("\n  -- how often does causality run? (crontab) --")
print(sh("crontab -l 2>/dev/null | grep -i 'causal' | grep -v '^#'") or "  (not in crontab)")
print("\n  -- recent causality-emergent threads (count today) --")
print(sh("grep -c 'causality' %s/thread-triage.md 2>/dev/null" % MEM) or "")
