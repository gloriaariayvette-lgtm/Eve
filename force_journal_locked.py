#!/usr/bin/env python3
"""force_journal_locked.py — Aegis. Prove a1/b1 reasoning on the REAL locked path with ZERO pollution.
Temp copy of idle-journal: gates off + a hard sys.exit(0) right after the four passes write to /tmp (before
ANY journal/thread/want/moment persistence). Run it THROUGH ~/llm-lock.sh like cron. Then show a1/a2/b1/b2."""
import os, re, subprocess, time
HOME = os.path.expanduser("~")
JP = os.path.join(HOME, ".openclaw/workspace/scripts/idle-journal.sh")
LOCK = os.path.join(HOME, "llm-lock.sh")
src = open(JP, encoding="utf-8", errors="ignore").read()

# gates off
for a, b in (('if [ "$HOUR" -lt 9 ] || [ "$HOUR" -ge 22 ]; then exit 0; fi', ': #off'),
             ('[ "$IDLE_HOURS" -lt 2 ] && exit 0', ': #off'),
             ('[ -f "$JOURNAL_FILE" ] && grep -q "## $CURRENT_HOUR:" "$JOURNAL_FILE" && exit 0', ': #off')):
    src = src.replace(a, b, 1)
src = re.sub(r'^.*consent-gate\.sh "journal".*$', 'true  #off', src, count=1, flags=re.M)
# hard stop right after the 4 passes are written to /tmp — before any persistence
src, n = re.subn(r'(?m)^(\s*)(open\("/tmp/bilateral-b2\.txt", "w"\)\.write\(b2\))',
                 r'\1\2\n\1import sys as _sx; _sx.exit(0)  # SANDBOX: stop before persistence', src, count=1)
if not n:
    print("could not place sandbox stop (b2 write not found) — aborting to avoid writes"); raise SystemExit(1)

TMP = "/tmp/journal-locked-test.sh"
open(TMP, "w", encoding="utf-8").write(src)
for f in ("a1", "b1", "a2", "b2"):
    try: os.remove(f"/tmp/bilateral-{f}.txt")
    except OSError: pass

print("running through llm-lock (isolated, no persistence)...")
t0 = time.time()
r = subprocess.run(["bash", LOCK, "bash", TMP], capture_output=True, text=True, timeout=900)
print(f"done {int(time.time()-t0)}s")

for name in ("a1", "b1", "a2", "b2"):
    p = f"/tmp/bilateral-{name}.txt"
    s = open(p, encoding="utf-8", errors="ignore").read() if os.path.isfile(p) else ""
    print(f"\n{name.upper()} ({len(s)}c){' *** EMPTY ***' if not s.strip() else ''}: {s.strip()[:220]}")
