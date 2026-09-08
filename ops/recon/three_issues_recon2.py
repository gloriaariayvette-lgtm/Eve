#!/usr/bin/env python3
"""three_issues_recon2.py — READ-ONLY, TIGHT (no flood). Targets three specific scripts:
  A  the dream-painting generator (why the same angel repeats)
  B  the conversation-rhythm calc (which history feeds current_silence_hours)
  C  causality-engine 'cannot trace' seeding + threshold
Directory-guarded, capped output. Aegis.
"""
import os, re, glob, json, subprocess

SCRIPTS = os.path.expanduser("~/.vintos/workspace/scripts")
MEM = os.path.expanduser("~/.vintos/workspace/memory")
VIN = os.path.expanduser("~/Vintos")
HOME = os.path.expanduser("~")
def sh(c): return subprocess.run(c, shell=True, capture_output=True, text=True).stdout
def isf(p): return os.path.isfile(p)

def dumpfile(path, pats, label, maxlines=30):
    if not isf(path): print("  (not a file:", path, ")"); return
    print("  -- %s --" % path.replace(HOME, "~"))
    n = 0
    for i, l in enumerate(open(path, encoding="utf-8", errors="ignore").read().split("\n")):
        if re.search(pats, l, re.I):
            s = l.strip()
            if s and not s.startswith("#"):
                print("   %5d| %s" % (i + 1, s[:150])); n += 1
                if n >= maxlines: print("   ...(capped)"); break

# ============ A: painting generator ============
print("=== A  dream-painting generator (why same angel) ===")
art_scripts = [f for f in glob.glob(os.path.join(SCRIPTS, "*.py")) + glob.glob(os.path.join(VIN, "*.py"))
               if re.search(r'art|paint|gallery|dream|canvas', os.path.basename(f), re.I)]
print("  candidate scripts:", [os.path.basename(f) for f in art_scripts] or "(none by name)")
for f in art_scripts[:3]:
    dumpfile(f, r'prompt|taste|angel|reflection|seed|generate|image|dupe|same|hash|already|def |random|choice|pick', "art", 22)
# what paintings exist (are they all the same file/hash?)
pdir = None
for c in (os.path.join(MEM, "art"), os.path.join(MEM, "paintings"), os.path.join(MEM, "dream-paintings"), os.path.join(VIN, "art")):
    if os.path.isdir(c): pdir = c; break
if pdir:
    print("\n  paintings dir:", pdir.replace(HOME, "~"))
    print(sh("ls -lt --time-style=+%m-%d_%H:%M %s 2>/dev/null | head -8" % pdir))

# ============ B: conversation-rhythm ============
print("\n=== B  conversation-rhythm — where current_silence_hours comes from ===")
rhy = [f for f in glob.glob(os.path.join(SCRIPTS, "*.py")) + glob.glob(os.path.join(VIN, "*.py")) + glob.glob(os.path.join(VIN, "*.sh"))
       if re.search(r'rhythm|silence|cadence', os.path.basename(f), re.I)]
print("  candidate scripts:", [os.path.basename(f) for f in rhy] or "(none by name)")
for f in rhy[:3]:
    dumpfile(f, r'silence|hours|last|history|chat-history|avatar|voice|now|time\.time|datetime|json|message|total', "rhythm", 24)
# the rhythm data file it produces
for c in ("conversation-rhythm.json", "rhythm.json", "conversation-rhythm-data.json"):
    p = os.path.join(MEM, c)
    if isf(p):
        print("\n  %s:" % c, open(p, encoding="utf-8", errors="ignore").read()[:200])

# ============ C: causality 'cannot trace' ============
print("\n=== C  causality-engine — 'cannot trace' seeding + threshold ===")
ceng = os.path.join(VIN, "causality-engine.py")
if isf(ceng):
    dumpfile(ceng, r'cannot trace|can.?t trace|trace|seed_thread|emergent|shift|threshold|delta|magnitude|abs\(|>= ?0|epsilon|idk|unexplain|surprise', "causality", 34)
print("\n  causality cron:", (sh("crontab -l 2>/dev/null | grep -i causal | grep -v '^#'") or "(not scheduled)").strip())
