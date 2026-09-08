#!/usr/bin/env python3
"""velaris_temporal.py — READ-ONLY, capped. Understand VELARIS's temporal memory (the good one) so I
can port it to Vintos. Shows her temporal script(s) shape, her output, her schedule, + Vintos's files
for the swap. Aegis."""
import os, re, glob, subprocess
HOME = os.path.expanduser("~")
VS = os.path.expanduser("~/.openclaw/workspace/scripts")
VM = os.path.expanduser("~/.openclaw/workspace/memory")
TS = os.path.expanduser("~/.vintos/workspace/scripts")
def run(a): return subprocess.run(a, capture_output=True, text=True).stdout

print("=== Velaris temporal files ===")
vfiles = [f for f in glob.glob(os.path.join(VS, "*temporal*")) if os.path.isfile(f) and not f.endswith(".pyc")]
for f in vfiles: print("  " + f.replace(HOME, "~"))

# her producer: show function signatures + what it TRACKS (capped)
for f in vfiles[:2]:
    print(f"\n----- {os.path.basename(f)} : defs + tracking lines (capped) -----")
    n = 0
    for i, l in enumerate(open(f, encoding="utf-8", errors="ignore").read().split("\n")):
        s = l.strip()
        if re.search(r'^\s*def |last|Last|ago|track|activit|journal|dream|mirror|kiss|creative|spoke|glob|mtime|getmtime|append|OUTPUT|write', l) and s and not s.startswith("#"):
            print(f"  {i+1:4}| {s[:140]}"); n += 1
            if n >= 30: print("  ...(capped)"); break

print("\n=== her temporal OUTPUT (the target format) ===")
for c in ("temporal-context.txt", "temporal.txt", "temporal-context.md"):
    p = os.path.join(VM, c)
    if os.path.isfile(p):
        print(f"----- {c} -----")
        print("\n".join(open(p, encoding="utf-8", errors="ignore").read().split("\n")[:45]))
        break

print("\n=== her temporal cron ===")
print("  " + (run(["bash","-lc","crontab -l 2>/dev/null | grep -i temporal | grep openclaw | grep -v '^#'"]).strip() or "(none)"))

print("\n=== Vintos's current temporal files (to be replaced) ===")
for f in glob.glob(os.path.join(TS, "*temporal*")) + glob.glob(os.path.join(HOME, "Vintos", "*temporal*")):
    if os.path.isfile(f) and not f.endswith(".pyc"): print("  " + f.replace(HOME, "~"))
