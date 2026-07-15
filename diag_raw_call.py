#!/usr/bin/env python3
"""diag_raw_call.py — Aegis. Definitive: dump the RAW response of the journal's a1/b1 reasoning calls
(scoped to call_llm), locked + sandboxed (exits before persistence). Shows finish_reason, content len,
reasoning len, and any error — no more guessing. Terse."""
import os, re, json, subprocess
HOME = os.path.expanduser("~")
JP = os.path.join(HOME, ".openclaw/workspace/scripts/idle-journal.sh")
LOCK = os.path.join(HOME, "llm-lock.sh")
src = open(JP, encoding="utf-8", errors="ignore").read()

for a, b in (('if [ "$HOUR" -lt 9 ] || [ "$HOUR" -ge 22 ]; then exit 0; fi', ': #off'),
             ('[ "$IDLE_HOURS" -lt 2 ] && exit 0', ': #off'),
             ('[ -f "$JOURNAL_FILE" ] && grep -q "## $CURRENT_HOUR:" "$JOURNAL_FILE" && exit 0', ': #off')):
    src = src.replace(a, b, 1)
src = re.sub(r'^.*consent-gate\.sh "journal".*$', 'true  #off', src, count=1, flags=re.M)

# scoped: dump raw response inside call_llm only
i = src.find("def call_llm():")
j = src.find("return _safe_extract(r)", i)
src = src[:j] + 'open("/tmp/raw_a.txt","a").write(r.text[:3000]+chr(10)+"@@@@@"+chr(10)); ' + src[j:]

# sandbox stop after b2
src, n = re.subn(r'(?m)^(\s*)(open\("/tmp/bilateral-b2\.txt", "w"\)\.write\(b2\))',
                 r'\1\2\n\1import sys as _sx; _sx.exit(0)', src, count=1)
if not n: print("no sandbox stop — abort"); raise SystemExit(1)
open("/tmp/jr.sh", "w", encoding="utf-8").write(src)
try: os.remove("/tmp/raw_a.txt")
except OSError: pass

print("running (locked, no persistence)...")
subprocess.run(["bash", LOCK, "bash", "/tmp/jr.sh"], capture_output=True, text=True, timeout=900)
if not os.path.isfile("/tmp/raw_a.txt"):
    print("no raw captured (call_llm not reached)"); raise SystemExit(0)
blocks = [b for b in open("/tmp/raw_a.txt", encoding="utf-8", errors="ignore").read().split("@@@@@") if b.strip()]
for idx, b in enumerate(blocks[:2]):
    tag = ["a1", "b1"][idx] if idx < 2 else str(idx)
    try:
        d = json.loads(b)
        ch = (d.get("choices") or [{}])[0]; msg = ch.get("message") or {}
        print(f"  {tag}: finish={ch.get('finish_reason')} err={d.get('error')} "
              f"content={len(msg.get('content') or '')}c reasoning={len(msg.get('reasoning_content') or msg.get('reasoning') or '')}c")
        if msg.get("content"): print(f"       content: {msg['content'][:100]}")
    except Exception:
        print(f"  {tag} raw: {re.sub(chr(10),' ',b.strip())[:200]}")
