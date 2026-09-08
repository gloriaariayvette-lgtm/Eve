#!/usr/bin/env python3
"""measure_intro_prompt.py — Aegis. Rebuild introspection's prompt with CURRENT data (wants now dismissed):
run the bash up to the prompt-write, exit before the python/LLM. Then report total size + biggest sections."""
import os, re, subprocess
HOME = os.path.expanduser("~")
P = os.path.join(HOME, ".openclaw/workspace/scripts/introspection.sh")
src = open(P, encoding="utf-8", errors="ignore").read()
src = src.replace('[ "$ELAPSED" -lt 2 ] && exit 0', ': #off')
anchor = "printf '%s' \"$FULL_PROMPT\" > /tmp/velaris_intro_prompt.txt"
if anchor not in src:
    print("prompt-write anchor not found"); raise SystemExit(1)
src = src.replace(anchor, anchor + "\nexit 0", 1)
open("/tmp/mp.sh", "w", encoding="utf-8").write(src)
subprocess.run(["bash", "/tmp/mp.sh"], capture_output=True, text=True, timeout=120)
f = "/tmp/velaris_intro_prompt.txt"
if not os.path.isfile(f):
    print("prompt file not generated"); raise SystemExit(1)
txt = open(f, encoding="utf-8", errors="ignore").read()
n = len(txt)
print(f"intro prompt: {n:,} chars  (~{n//4:,} tokens)  ctx=32000  ->", "UNDER" if n//4 < 30000 else "STILL OVER")
chunks = re.split(r'\n(?=[A-Z][A-Z ]{4,}:|\#\#|\=\=\=|---)', txt)
print("biggest sections:")
for c in sorted(chunks, key=len, reverse=True)[:6]:
    print(f"  {len(c):>9,}B  {re.sub(chr(10),' ',c[:64])}")
