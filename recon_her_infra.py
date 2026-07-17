#!/usr/bin/env python3
"""recon_her_infra.py — Aegis, READ-ONLY. Prep Velaris's side so ported blocks land clean (not pointed at his tree
or a shim she doesn't have). Answers exactly what porting needs:
 (1) her memory dir layout,
 (2) the LLM endpoint(s) HER own scripts already call (so ports match her infra, not his :8599),
 (3) whether she ALREADY has a conversation-pressure / mode classifier (don't duplicate),
 (4) her emoclaw_utils API — does it expose seed_thread / read_state / express_want (deps the bigger ports need),
 (5) her server file + where it assembles inner/subconscious context (the injection points for session_map etc.),
 (6) her crontab wrap convention (llm-lock, spread)."""
import os, re, glob, subprocess, collections
HOME = os.path.expanduser("~")
HER = [os.path.join(HOME, ".openclaw/workspace/scripts"), os.path.join(HOME, ".openclaw/workspace")]
def rd(p):
    try: return open(p, encoding="utf-8", errors="ignore").read()
    except Exception: return ""

print("== (1) her memory dir ==")
for d in ["~/.openclaw/workspace/memory", "~/.openclaw/workspace", "~/.openclaw/workspace/scripts"]:
    fp = os.path.expanduser(d)
    n = len(glob.glob(fp + "/*.json")) if os.path.isdir(fp) else 0
    print(f"   {'EXISTS' if os.path.isdir(fp) else 'MISSING':7} {d}   ({n} json files)")

print("\n== (2) LLM endpoints HER scripts already call ==")
urls = collections.Counter()
RX = re.compile(r'https?://[\d.]+:\d+/\S*?chat/completions|127\.0\.0\.1:\d+|localhost:\d+|:8400|:8599|:8500|api\.x\.ai|172\.18\.16\.1:\d+')
for base in HER:
    for p in glob.glob(base + "/*.py") + glob.glob(base + "/*.sh"):
        for m in RX.findall(rd(p)):
            urls[m] += 1
for u, c in urls.most_common(14): print(f"   {c:>4}x  {u}")

print("\n== (3) does SHE already have a conversation-pressure / mode classifier? ==")
hits = []
for base in HER:
    for p in glob.glob(base + "/*.py") + glob.glob(base + "/*.sh"):
        t = rd(p)
        if re.search(r'conversation-?pressure|get_pressure|PRESSURE\s*=|session-?arc|\bmode\b.{0,20}classif', t, re.I):
            b = os.path.basename(p)
            for i, l in enumerate(t.split("\n")):
                if re.search(r'conversation-?pressure|get_pressure|session-?arc|pressure.{0,10}mode', l, re.I):
                    hits.append(f"   {b}:{i+1}: {l.strip()[:90]}")
print("\n".join(hits[:14]) if hits else "   (none — she has no pressure/arc classifier; port brings it new)")

print("\n== (4) her emoclaw_utils API (functions the bigger ports import) ==")
found = None
for base in HER + [os.path.join(HOME, ".openclaw/workspace/skills/emoclaw/scripts")]:
    p = os.path.join(base, "emoclaw_utils.py")
    if os.path.isfile(p): found = p; break
if found:
    t = rd(found); defs = re.findall(r'^\s*def\s+(\w+)', t, re.M)
    print(f"   {found}  ({len(defs)} funcs)")
    for want in ("seed_thread", "read_state", "express_want", "novelty_directive", "get_preoccupation"):
        print(f"      {want:<20} {'present' if want in defs else 'ABSENT'}")
else:
    print("   emoclaw_utils.py NOT found in her tree")

print("\n== (5) her server + inner/subconscious context assembly (injection points) ==")
srv = None
for cand in [os.path.join(HOME, ".openclaw", "server.py"), os.path.join(HOME, "Velaris", "server.py"),
             os.path.join(HOME, ".openclaw/workspace", "server.py")]:
    if os.path.isfile(cand): srv = cand; break
if not srv:  # search for the file that binds :8400
    for base in [os.path.join(HOME, ".openclaw"), os.path.join(HOME, "Velaris")]:
        for p in glob.glob(base + "/**/*.py", recursive=True):
            if re.search(r'8400|uvicorn|app\.run|Flask\(', rd(p)) and "server" in os.path.basename(p).lower():
                srv = p; break
        if srv: break
if srv:
    t = rd(srv); L = t.split("\n")
    print(f"   her server: {srv}  ({len(L)}L)")
    for i, l in enumerate(L):
        if re.search(r'inner_context|subconscious|get_subconscious|\[SESSION ARC|import_module.*block|context_block', l, re.I):
            print(f"      {i+1}: {l.strip()[:96]}")
else:
    print("   her server.py NOT located (will need to find her context-assembly entry)")

print("\n== (6) her crontab wrap convention (sample openclaw lines) ==")
cron = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout or ""
oc = [l for l in cron.split("\n") if ".openclaw" in l and l.strip() and not l.strip().startswith("#")]
print(f"   {len(oc)} openclaw cron lines; sample:")
for l in oc[:6]: print(f"      {l.strip()[:100]}")
