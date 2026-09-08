#!/usr/bin/env python3
"""verify_runtime2.py — Aegis. ONE call, done right. Journal-sized prompt from her memory (read-only),
reasoning ON, max_tokens=2500 (room for reasoning AND content). Fixed = content non-empty, reasoning not
ballooned (<4000c), no 'context exceeded'. This is the actual failing case, not a starved tiny budget."""
import os, glob, json, urllib.request
HOME = os.path.expanduser("~"); MEM = os.path.join(HOME, ".openclaw/workspace/memory")
LM = "http://172.18.16.1:1234/v1/chat/completions"
def rd(p, n=4000):
    try: return open(p, encoding="utf-8", errors="ignore").read()[:n]
    except Exception: return ""
chunks = [f"[{n}]\n{rd(os.path.join(MEM,n))}" for n in
          ("emotional-state.txt", "gloria-model.md", "value-map.txt", "self-model.md", "chat-history-merged.json") if rd(os.path.join(MEM,n))]
for pf in sorted(glob.glob(os.path.join(MEM, "pearls", "pearl_*.md")), key=os.path.getmtime, reverse=True)[:4]:
    chunks.append("[pearl]\n" + rd(pf, 1500))
SYS = ("You are Velaris writing an idle journal entry. Your inner context:\n\n" + "\n\n".join(chunks))[:24000]
body = {"model": "google/gemma-4-12b-qat", "reasoning_effort": "low", "temperature": 0.65, "max_tokens": 2500,
        "messages": [{"role": "system", "content": SYS},
                     {"role": "user", "content": "Write one honest paragraph about what you feel right now."}]}
try:
    r = json.loads(urllib.request.urlopen(urllib.request.Request(
        LM, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}), timeout=180).read())
    ch = (r.get("choices") or [{}])[0]; msg = ch.get("message") or {}
    rl = len(msg.get("reasoning_content") or msg.get("reasoning") or ""); cl = len(msg.get("content") or "")
    print(f"prompt~{len(SYS)//4}tok  reasoning={rl}c  content={cl}c  finish={ch.get('finish_reason')}  err={r.get('error')}")
    print("FIXED — reasoning bounded, content lands" if cl and rl < 4000 and not r.get("error")
          else "NOT fixed (reload model, or runtime still 2.24/2.25)")
except Exception as e:
    print("ERROR", str(e)[:100])
