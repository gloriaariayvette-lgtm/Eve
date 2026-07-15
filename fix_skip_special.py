#!/usr/bin/env python3
"""fix_skip_special.py — Aegis. The 'only reasoning, empty content' bug: LM Studio strips the <channel|>
thought-close token by default, so the parser can't split thinking from the answer and content comes back
empty. Fix = "skip_special_tokens": false in the request so the delimiter survives and reasoning/content
separate. Add to call_llm (scoped), then sandboxed+locked full test. Terse."""
import os, re, shutil, time, subprocess
HOME = os.path.expanduser("~")
JP = os.path.join(HOME, ".openclaw/workspace/scripts/idle-journal.sh")
LOCK = os.path.join(HOME, "llm-lock.sh")

t = open(JP, encoding="utf-8", errors="ignore").read()
i = t.find("def call_llm():"); m = re.search(r"\n\s*def\s", t[i+1:]); end = i+1+m.start() if m else i+1500
seg = t[i:end]
if "skip_special_tokens" in seg:
    print("skip_special_tokens already set")
else:
    mm = re.search(r'"model":\s*"google/gemma-4-12b-qat",', seg)
    if not mm: print("model line not found — abort"); raise SystemExit(1)
    bak = JP + ".bak-skip-" + time.strftime("%Y%m%d-%H%M%S"); shutil.copy2(JP, bak)
    seg2 = seg[:mm.end()] + '"skip_special_tokens": False,' + seg[mm.end():]
    open(JP, "w", encoding="utf-8").write(t[:i] + seg2 + t[end:])
    c = subprocess.run(["bash", "-n", JP], capture_output=True, text=True)
    if c.returncode: shutil.copy2(bak, JP); print("bash -n failed, reverted"); raise SystemExit(1)
    print("skip_special_tokens:false added to call_llm (backup saved)")

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
open("/tmp/fs.sh", "w", encoding="utf-8").write(src)
for f in ("a1", "b1", "a2", "b2"):
    try: os.remove(f"/tmp/bilateral-{f}.txt")
    except OSError: pass
print("running locked full test (no persistence)...")
t0 = time.time(); subprocess.run(["bash", LOCK, "bash", "/tmp/fs.sh"], capture_output=True, text=True, timeout=900)
print(f"done {int(time.time()-t0)}s")
for name in ("a1", "b1", "a2", "b2"):
    p = f"/tmp/bilateral-{name}.txt"; s = open(p, encoding="utf-8", errors="ignore").read() if os.path.isfile(p) else ""
    print(f"{name.upper()} ({len(s)}c){' *** EMPTY ***' if not s.strip() else ''}: {s.strip()[:170]}")
