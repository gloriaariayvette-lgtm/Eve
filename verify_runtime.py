#!/usr/bin/env python3
"""verify_runtime.py — Aegis. ONE call. Confirm the runtime downgrade bounded reasoning. Same prompt that
gave reasoning=1906c/content=0c before. Fixed = reasoning much smaller AND content non-empty."""
import json, urllib.request
LM = "http://172.18.16.1:1234/v1/chat/completions"
PROMPT = ("Work through this carefully, step by step, considering each case: a farmer must cross a river with "
          "a fox, a chicken, grain, and a small dog, boat holds one item. What order? Reason thoroughly first.")
body = {"model": "google/gemma-4-12b-qat", "reasoning_effort": "low", "temperature": 0.3,
        "max_tokens": 500, "messages": [{"role": "user", "content": PROMPT}]}
try:
    r = json.loads(urllib.request.urlopen(urllib.request.Request(
        LM, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}), timeout=120).read())
    ch = (r.get("choices") or [{}])[0]; msg = ch.get("message") or {}
    rl = len(msg.get("reasoning_content") or msg.get("reasoning") or ""); cl = len(msg.get("content") or "")
    print(f"reasoning={rl}c  content={cl}c  finish={ch.get('finish_reason')}  err={r.get('error')}")
    print("FIXED" if cl and rl < 1200 else "still runaway — eject+reload the model so the new runtime loads")
except Exception as e:
    print("ERROR", str(e)[:90])
