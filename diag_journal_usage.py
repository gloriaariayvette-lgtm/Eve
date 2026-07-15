#!/usr/bin/env python3
"""diag_journal_usage.py — Aegis. Capture WHY a1/b1 empty: the real journal call's prompt_tokens +
finish_reason vs the model's loaded context length. Instruments _safe_extract to log usage, runs the journal
sandboxed+locked (exits before persistence). Terse."""
import os, re, json, subprocess, urllib.request
HOME = os.path.expanduser("~")
JP = os.path.join(HOME, ".openclaw/workspace/scripts/idle-journal.sh")
LOCK = os.path.join(HOME, "llm-lock.sh")

# model context length (LM Studio native api)
nctx = "unknown"
try:
    d = json.loads(urllib.request.urlopen("http://172.18.16.1:1234/api/v0/models", timeout=8).read())
    for m in d.get("data", []):
        if "gemma-4-12b" in m.get("id", ""):
            nctx = f"loaded={m.get('loaded_context_length')} max={m.get('max_context_length')}"
except Exception as e:
    nctx = "api/v0 failed: " + str(e)[:40]

src = open(JP, encoding="utf-8", errors="ignore").read()
for a, b in (('if [ "$HOUR" -lt 9 ] || [ "$HOUR" -ge 22 ]; then exit 0; fi', ': #off'),
             ('[ "$IDLE_HOURS" -lt 2 ] && exit 0', ': #off'),
             ('[ -f "$JOURNAL_FILE" ] && grep -q "## $CURRENT_HOUR:" "$JOURNAL_FILE" && exit 0', ': #off')):
    src = src.replace(a, b, 1)
src = re.sub(r'^.*consent-gate\.sh "journal".*$', 'true  #off', src, count=1, flags=re.M)
# log usage inside _safe_extract
LOGLINE = ('\\n        try: open("/tmp/cu.txt","a").write(str(data.get("usage"))+" finish="'
           '+str((data.get("choices") or [{}])[0].get("finish_reason"))+" clen="'
           '+str(len(((data.get("choices") or [{}])[0].get("message") or {}).get("content") or ""))+"\\n")'
           '\\n        except Exception: pass')
src = src.replace("        data = r.json()", "        data = r.json()" + LOGLINE.replace("\\n", "\n"), 1)
# sandbox stop after b2
src, n = re.subn(r'(?m)^(\s*)(open\("/tmp/bilateral-b2\.txt", "w"\)\.write\(b2\))',
                 r'\1\2\n\1import sys as _sx; _sx.exit(0)', src, count=1)
if not n:
    print("sandbox stop not placed — abort"); raise SystemExit(1)
open("/tmp/ju.sh", "w", encoding="utf-8").write(src)
try: os.remove("/tmp/cu.txt")
except OSError: pass

print("n_ctx:", nctx)
print("running (locked, no persistence)...")
subprocess.run(["bash", LOCK, "bash", "/tmp/ju.sh"], capture_output=True, text=True, timeout=900)
if os.path.isfile("/tmp/cu.txt"):
    for i, l in enumerate(open("/tmp/cu.txt").read().strip().split("\n")):
        tag = ["a1", "b1", "audit1", "a2", "b2"][i] if i < 5 else str(i)
        print(f"  {tag}: {l[:110]}")
else:
    print("  (no usage captured)")
