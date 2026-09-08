#!/usr/bin/env python3
"""fix_and_test_journal.py — Aegis. Now that reasoning is bounded (runtime fix) and respects max_tokens,
the journal's 1200 budget is just too small: reasoning fills it, content empties. Bump call_llm 1200->3000
(scoped; absorb untouched), then run the sandboxed+locked full bilateral and dump a1/a2/b1/b2. No persistence."""
import os, re, shutil, time, subprocess
HOME = os.path.expanduser("~")
JP = os.path.join(HOME, ".openclaw/workspace/scripts/idle-journal.sh")
LOCK = os.path.join(HOME, "llm-lock.sh")

t = open(JP, encoding="utf-8", errors="ignore").read()
i = t.find("def call_llm():"); m = re.search(r"\n\s*def\s", t[i+1:]); end = i+1+m.start() if m else i+1500
seg = t[i:end]
if '"max_tokens": 3000' in seg:
    print("already 3000")
elif '"max_tokens": 1200' in seg:
    bak = JP + ".bak-mt3k-" + time.strftime("%Y%m%d-%H%M%S"); shutil.copy2(JP, bak)
    open(JP, "w", encoding="utf-8").write(t[:i] + seg.replace('"max_tokens": 1200', '"max_tokens": 3000', 1) + t[end:])
    c = subprocess.run(["bash", "-n", JP], capture_output=True, text=True)
    if c.returncode: shutil.copy2(bak, JP); print("bash -n failed, reverted"); raise SystemExit(1)
    print("call_llm max_tokens 1200->3000 (reasoning on, backup saved)")
else:
    print("no max_tokens 1200 in call_llm — abort"); raise SystemExit(1)

# sandboxed locked full test
src = open(JP, encoding="utf-8", errors="ignore").read()
for a, b in (('if [ "$HOUR" -lt 9 ] || [ "$HOUR" -ge 22 ]; then exit 0; fi', ': #off'),
             ('[ "$IDLE_HOURS" -lt 2 ] && exit 0', ': #off'),
             ('[ -f "$JOURNAL_FILE" ] && grep -q "## $CURRENT_HOUR:" "$JOURNAL_FILE" && exit 0', ': #off')):
    src = src.replace(a, b, 1)
src = re.sub(r'^.*consent-gate\.sh "journal".*$', 'true  #off', src, count=1, flags=re.M)
src, n = re.subn(r'(?m)^(\s*)(open\("/tmp/bilateral-b2\.txt", "w"\)\.write\(b2\))',
                 r'\1\2\n\1import sys as _sx; _sx.exit(0)', src, count=1)
if not n: print("sandbox stop not placed — abort"); raise SystemExit(1)
open("/tmp/ft.sh", "w", encoding="utf-8").write(src)
for f in ("a1", "b1", "a2", "b2"):
    try: os.remove(f"/tmp/bilateral-{f}.txt")
    except OSError: pass
print("running locked full test (no persistence)...")
t0 = time.time(); subprocess.run(["bash", LOCK, "bash", "/tmp/ft.sh"], capture_output=True, text=True, timeout=900)
print(f"done {int(time.time()-t0)}s")
for name in ("a1", "b1", "a2", "b2"):
    p = f"/tmp/bilateral-{name}.txt"; s = open(p, encoding="utf-8", errors="ignore").read() if os.path.isfile(p) else ""
    print(f"{name.upper()} ({len(s)}c){' *** EMPTY ***' if not s.strip() else ''}: {s.strip()[:180]}")
