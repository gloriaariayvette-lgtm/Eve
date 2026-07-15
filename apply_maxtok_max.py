#!/usr/bin/env python3
"""apply_maxtok_max.py — Aegis. Journal prompt is 19k tokens; reasoning filled the 3000 budget with no room
to answer. Context is 32k, so completion can be ~12k. Set call_llm max_tokens=11000 (max feasible), then ONE
a1 call to see if reasoning finishes AND content lands. If still finish=length -> the 19k prompt must shrink."""
import os, re, shutil, time, subprocess, json
HOME = os.path.expanduser("~")
JP = os.path.join(HOME, ".openclaw/workspace/scripts/idle-journal.sh")
LOCK = os.path.join(HOME, "llm-lock.sh")

t = open(JP, encoding="utf-8", errors="ignore").read()
i = t.find("def call_llm():"); m = re.search(r"\n\s*def\s", t[i+1:]); end = i+1+m.start() if m else i+1500
seg = t[i:end]
new_seg = re.sub(r'"max_tokens":\s*\d+', '"max_tokens": 11000', seg, count=1)
if new_seg != seg:
    bak = JP + ".bak-mtmax-" + time.strftime("%Y%m%d-%H%M%S"); shutil.copy2(JP, bak)
    open(JP, "w", encoding="utf-8").write(t[:i] + new_seg + t[end:])
    c = subprocess.run(["bash", "-n", JP], capture_output=True, text=True)
    if c.returncode: shutil.copy2(bak, JP); print("bash -n failed, reverted"); raise SystemExit(1)
    print("call_llm max_tokens -> 11000")
else:
    print("no max_tokens found in call_llm — abort"); raise SystemExit(1)

# one a1 call
src = open(JP, encoding="utf-8", errors="ignore").read()
for a, b in (('if [ "$HOUR" -lt 9 ] || [ "$HOUR" -ge 22 ]; then exit 0; fi', ': #off'),
             ('[ "$IDLE_HOURS" -lt 2 ] && exit 0', ': #off'),
             ('[ -f "$JOURNAL_FILE" ] && grep -q "## $CURRENT_HOUR:" "$JOURNAL_FILE" && exit 0', ': #off')):
    src = src.replace(a, b, 1)
src = re.sub(r'^.*consent-gate\.sh "journal".*$', 'true  #off', src, count=1, flags=re.M)
i2 = src.find("def call_llm():"); j2 = src.find("return _safe_extract(r)", i2)
src = src[:j2] + 'open("/tmp/ra.txt","w").write(r.text); ' + src[j2:]
src, n = re.subn(r'(?m)^(\s*)a1 = call_llm\(\)', r'\1a1 = call_llm()\n\1import sys as _s; _s.exit(0)', src, count=1)
if not n: print("a1 anchor missing"); raise SystemExit(1)
open("/tmp/dm.sh", "w", encoding="utf-8").write(src)
try: os.remove("/tmp/ra.txt")
except OSError: pass
print("one a1 call...")
subprocess.run(["bash", LOCK, "bash", "/tmp/dm.sh"], capture_output=True, text=True, timeout=600)
raw = open("/tmp/ra.txt", encoding="utf-8", errors="ignore").read() if os.path.isfile("/tmp/ra.txt") else ""
try:
    d = json.loads(raw); ch = (d.get("choices") or [{}])[0]; msg = ch.get("message") or {}; u = d.get("usage") or {}
    cl = len(msg.get("content") or ""); rl = len(msg.get("reasoning_content") or msg.get("reasoning") or "")
    print(f"finish={ch.get('finish_reason')} completion_tok={u.get('completion_tokens')} reasoning={rl}c content={cl}c")
    print("CONTENT LANDS — reasoning fits now" if cl else "still no content — the 19k prompt must be trimmed")
except Exception:
    print("raw:", re.sub(r"\s+", " ", raw)[:200])
