#!/usr/bin/env python3
"""diag_reasoning_cap.py — Aegis. Find which reasoning-token-cap param this LMEP build honors. Same
reasoning-inducing prompt, small cap (128), several param spellings. The winner = reasoning_content clearly
shortened (near the cap) with content still non-empty and no error. Terse. No journal touched."""
import json, urllib.request
LM = "http://172.18.16.1:1234/v1/chat/completions"
PROMPT = ("Work through this carefully, step by step, considering each case: a farmer must cross a river with "
          "a fox, a chicken, grain, and a small dog, boat holds one item. What order? Reason thoroughly first.")
def run(extra, label):
    body = {"model": "google/gemma-4-12b-qat", "reasoning_effort": "low", "temperature": 0.3,
            "max_tokens": 500, "messages": [{"role": "user", "content": PROMPT}], **extra}
    try:
        r = json.loads(urllib.request.urlopen(urllib.request.Request(
            LM, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}), timeout=120).read())
        ch = (r.get("choices") or [{}])[0]; msg = ch.get("message") or {}
        rl = len(msg.get("reasoning_content") or msg.get("reasoning") or ""); cl = len(msg.get("content") or "")
        print(f"  {label:26} reasoning={rl}c content={cl}c finish={ch.get('finish_reason')} err={r.get('error')}")
    except Exception as e:
        print(f"  {label:26} ERROR {str(e)[:70]}")

run({}, "baseline (no cap)")
run({"max_reasoning_tokens": 128}, "max_reasoning_tokens")
run({"reasoning_max_tokens": 128}, "reasoning_max_tokens")
run({"max_thinking_tokens": 128}, "max_thinking_tokens")
run({"thinking_budget": 128}, "thinking_budget")
run({"reasoning": {"max_tokens": 128}}, "reasoning.max_tokens")
run({"reasoning_effort": "minimal"}, "effort=minimal")
print("winner = reasoning clearly shorter than baseline, content non-empty, no err")
