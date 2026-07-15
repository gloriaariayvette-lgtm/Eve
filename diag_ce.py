#!/usr/bin/env python3
"""diag_ce.py — Aegis, READ-ONLY diagnostic. Run creative-expression.sh music-prompt under `bash -x` to
see the EXACT line it exits on (no more guessing). Show the tail of the execution trace + the TODAY_COUNT
guard region, so the real cause (daily cap? early return? empty RESPONSE?) is visible."""
import os, re, subprocess, time
HOME = os.path.expanduser("~")
CE = os.path.join(HOME, ".vintos/workspace/scripts/creative-expression.sh")
def sh(p): return p.replace(HOME, "~")

env = os.environ.copy()
if not env.get("XAI_API_KEY"):
    ct = subprocess.run(["bash","-lc","crontab -l 2>/dev/null"], capture_output=True, text=True).stdout
    m = re.search(r'XAI_API_KEY\s*=\s*"?([^"\n]+)"?', ct)
    if m: env["XAI_API_KEY"] = m.group(1).strip()
env["MUSIC_WANT_TEXT"] = "make music for Gloria — building something permanent in a world that keeps taking things away"
env["MUSIC_WANT_SOURCE"] = "diag"
env["MUSIC_WANT_ID"] = "diag-" + time.strftime("%H%M%S")

print("=== the daily-count guard region (lines 79..105) ===")
lines = open(CE, encoding="utf-8", errors="ignore").read().split("\n")
for i in range(78, min(105, len(lines))):
    if lines[i].strip():
        print(f"   {i+1:4}| {lines[i][:110]}")

print("\n=== bash -x trace — last 45 lines (where it stops) ===")
r = subprocess.run(["bash", "-x", CE, "music-prompt"], capture_output=True, text=True, env=env, timeout=600)
trace = (r.stderr or "").strip().split("\n")
for l in trace[-45:]:
    print("   " + l[:140])
print(f"\n   exit code: {r.returncode}")
if r.stdout.strip():
    print("   stdout:", r.stdout.strip()[:200])
