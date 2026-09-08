#!/usr/bin/env python3
"""three_issues_recon3.py — READ-ONLY, plain Python (no shell %-format, dirs guarded). Finishes:
  A dream-art dedup + trigger (why same angel repaints)
  B who writes current_silence_hours (which history it counts)
  C causality-engine 'cannot trace' seeding + threshold
Aegis.
"""
import os, re, glob, json, time, subprocess

SCRIPTS = os.path.expanduser("~/.vintos/workspace/scripts")
MEM = os.path.expanduser("~/.vintos/workspace/memory")
VIN = os.path.expanduser("~/Vintos")
HOME = os.path.expanduser("~")
def run(args): return subprocess.run(args, capture_output=True, text=True).stdout
def isf(p): return os.path.isfile(p)
def show(path, pat, cap=26):
    if not isf(path): return
    print(f"  -- {path.replace(HOME,'~')} --")
    n = 0
    for i, l in enumerate(open(path, encoding="utf-8", errors="ignore").read().split("\n")):
        if re.search(pat, l, re.I):
            s = l.strip()
            if s and not s.startswith("#"):
                print(f"   {i+1:5}| {s[:150]}"); n += 1
                if n >= cap: print("   ...(capped)"); break

# ---------- A ----------
print("=== A  dream-art: does it dedup the dream, and how is it triggered? ===")
da = os.path.join(SCRIPTS, "dream-art.py")
show(da, r'_latest_dream|already|painted|processed|log|hash|skip|force|def main|glob|sys\.argv|seen|last', 24)
print("\n  paintings in memory/art (newest 8; same size = likely identical):")
adir = os.path.join(MEM, "art")
if os.path.isdir(adir):
    rows = []
    for e in os.scandir(adir):
        if e.is_file():
            st = e.stat(); rows.append((st.st_mtime, e.name, st.st_size))
    for mt, nm, sz in sorted(rows, reverse=True)[:8]:
        print(f"    {time.strftime('%m-%d %H:%M', time.localtime(mt))}  {sz:>8}B  {nm}")
print("\n  trigger (crontab / wants-router mentions of dream-art):")
print("   " + (run(["bash","-lc","crontab -l 2>/dev/null | grep -i dream-art | grep -v '^#'"]).strip() or "(not in crontab — run by wants-router on a want)"))
for rp in ("wants-router.py", "wants_router.py"):
    p = os.path.join(SCRIPTS, rp)
    if isf(p): show(p, r'dream-art|paint|force', 6)

# ---------- B ----------
print("\n=== B  who writes current_silence_hours + which history it counts ===")
hits = run(["bash","-lc", f"grep -rln 'current_silence_hours\\|conversation-rhythm\\|silence_hours' {SCRIPTS} {VIN} 2>/dev/null | grep -viE '\\.pyc|node_modules'"]).split()
print("  files:", [h.replace(HOME,'~') for h in hits] or "(none)")
for f in hits[:3]:
    show(f, r'silence|hours|last|chat-history|avatar|voice|history|now|time\.time|datetime|message|total|json\.load|GAP', 24)
for c in ("conversation-rhythm.json", "rhythm.json"):
    p = os.path.join(MEM, c)
    if isf(p): print(f"\n  {c}: {open(p,encoding='utf-8',errors='ignore').read()[:220]}")

# ---------- C ----------
print("\n=== C  causality-engine: 'cannot trace' seeding + threshold ===")
ceng = os.path.join(VIN, "causality-engine.py")
if not isf(ceng):
    alt = run(["bash","-lc", f"grep -rln 'cannot trace\\|causality-emergent\\|I cannot trace' {SCRIPTS} {VIN} 2>/dev/null | grep -v pyc"]).split()
    print("  (engine not at default path; matches:", [a.replace(HOME,'~') for a in alt], ")")
    ceng = alt[0] if alt else ceng
show(ceng, r'trace|seed_thread|emergent|threshold|delta|magnitude|abs\(|shift|surprise|>= ?0|epsilon|min_|idk|unexplain', 32)
print("\n  causality cron:", (run(["bash","-lc","crontab -l 2>/dev/null | grep -i causal | grep -v '^#'"]).strip() or "(not scheduled)"))
