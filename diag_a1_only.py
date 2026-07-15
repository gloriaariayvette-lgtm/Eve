#!/usr/bin/env python3
"""diag_a1_only.py — Aegis. ONE model call. Dump a1's raw response then exit (no b1/audit/a2/b2). Tells us
finish_reason + reasoning vs content length on the REAL journal prompt. finish=length => reasoning fills the
budget (need smaller prompt or bigger budget); finish=stop+empty => model emits no answer (separation)."""
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
# raw dump inside call_llm
i = src.find("def call_llm():"); j = src.find("return _safe_extract(r)", i)
src = src[:j] + 'open("/tmp/ra.txt","w").write(r.text); ' + src[j:]
# exit right after the FIRST call (a1)
src, n = re.subn(r'(?m)^(\s*)a1 = call_llm\(\)', r'\1a1 = call_llm()\n\1import sys as _s; _s.exit(0)', src, count=1)
if not n: print("a1 anchor not found — abort"); raise SystemExit(1)
open("/tmp/da.sh", "w", encoding="utf-8").write(src)
try: os.remove("/tmp/ra.txt")
except OSError: pass
subprocess.run(["bash", LOCK, "bash", "/tmp/da.sh"], capture_output=True, text=True, timeout=400)
if not os.path.isfile("/tmp/ra.txt"): print("no response captured"); raise SystemExit(0)
raw = open("/tmp/ra.txt", encoding="utf-8", errors="ignore").read()
try:
    d = json.loads(raw); ch = (d.get("choices") or [{}])[0]; msg = ch.get("message") or {}
    u = d.get("usage") or {}
    print(f"finish={ch.get('finish_reason')} err={d.get('error')} prompt_tok={u.get('prompt_tokens')} "
          f"completion_tok={u.get('completion_tokens')} reasoning={len(msg.get('reasoning_content') or msg.get('reasoning') or '')}c content={len(msg.get('content') or '')}c")
except Exception:
    print("raw:", re.sub(r"\s+", " ", raw)[:280])
