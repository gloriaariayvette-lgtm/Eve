#!/usr/bin/env python3
"""recon_thinking_default.py — Aegis, READ-ONLY (inference only, no writes). Decide the whole a1/b1
approach with one fact: does gemma-4-12b-qat THINK BY DEFAULT (no reasoning param)? Sends a reasoning-bait
prompt three ways and reports whether visible/'<think>'/reasoning_content thinking appears:
  (A) no param at all      -> the current behavior of all 144 unedited scripts
  (B) enable_thinking:false / reasoning_effort minimal
  (C) enable_thinking:true / reasoning_effort high
If A shows NO thinking, we touch nothing but the 2 a1/b1 scripts."""
import json, urllib.request
LM = "http://172.18.16.1:1234/v1/chat/completions"
MODEL = "google/gemma-4-12b-qat"
BAIT = ("A man has to cross a river with a fox, a chicken and grain. Briefly: what does he take first? "
        "Think it through if you need to.")

def call(extra, label):
    body = {"model": MODEL, "messages": [{"role": "user", "content": BAIT}],
            "temperature": 0.3, "max_tokens": 400, **extra}
    try:
        req = urllib.request.Request(LM, data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json"})
        r = json.loads(urllib.request.urlopen(req, timeout=90).read())
        msg = (r.get("choices") or [{}])[0].get("message") or {}
        content = msg.get("content") or ""
        reasoning = msg.get("reasoning_content") or msg.get("reasoning") or ""
        has_tag = any(t in content for t in ("<think>", "</think>", "channel|>", "|channel>", "<|channel"))
        thinking = bool(reasoning) or has_tag
        print(f"\n===== {label} =====")
        print(f"  reasoning_content field: {'YES ('+str(len(reasoning))+' chars)' if reasoning else 'no'}")
        print(f"  think-tags in content:   {'YES' if has_tag else 'no'}")
        print(f"  >>> THINKING PRESENT:    {'*** YES ***' if thinking else 'NO'}")
        print(f"  content head: {content.strip()[:160].replace(chr(10),' ')}")
        if reasoning:
            print(f"  reasoning head: {reasoning.strip()[:160].replace(chr(10),' ')}")
    except Exception as e:
        print(f"\n===== {label} =====\n  ERROR: {str(e)[:120]}")

call({}, "A) NO PARAM  (what all 144 unedited scripts get right now)")
call({"chat_template_kwargs": {"enable_thinking": False}}, "B1) enable_thinking:false")
call({"reasoning_effort": "low"}, "B2) reasoning_effort:low")
call({"chat_template_kwargs": {"enable_thinking": True}}, "C1) enable_thinking:true")
call({"reasoning_effort": "high"}, "C2) reasoning_effort:high")
print("\n(done — if A says THINKING PRESENT: NO, the other 144 need nothing; we only enable a1/b1.)")
