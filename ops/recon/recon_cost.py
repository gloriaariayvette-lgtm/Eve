#!/usr/bin/env python3
"""recon_cost.py — Aegis, READ-ONLY. Where the money goes. (A) Which model + whether cache_control is set on each
Claude call site (shim fleet / model_router avatar+chat / _claude_sync journal). (B) Fleet call volume from the
shim log. (C) which crons hit the shim (frequent = expensive)."""
import os, re, subprocess, time, glob
HOME = os.path.expanduser("~")
V = os.path.join(HOME, "Vintos")

def show(path, rx, label, n=14):
    if not os.path.isfile(path): print(f"  ({label}: missing)"); return
    L = open(path, encoding="utf-8", errors="ignore").read().split("\n")
    print(f"  --- {label} ---")
    for i, l in enumerate(L):
        if rx.search(l): print(f"    {i+1}: {l.strip()[:100]}")

print("== (A) model + cache_control per call site ==")
show(os.path.join(V, "vintos_claude_shim.py"),
     re.compile(r'CLAUDE_MODEL|GEMMA_MODEL|cache_control|claude-|max_tokens|thinking'), "shim")
show(os.path.join(V, "model_router.py"),
     re.compile(r'cache_control|claude-opus|claude-haiku|"model"|model\s*=|max_tokens|thinking|adaptive'), "model_router")

print("\n== (B) fleet Claude volume (shim log) ==")
lg = "/tmp/vintos-claude-shim.log"
if os.path.isfile(lg):
    t = open(lg, encoding="utf-8", errors="ignore").read()
    print(f"    claude ok: {t.count('claude ok')} | gemma route: {t.count('gemma route')} | "
          f"fallback->grok: {t.count('fallback->grok')} | claude error: {t.count('claude error')}")
    print(f"    log covers ~{int((time.time()-os.path.getmtime(lg))/1)}s since last write; size {os.path.getsize(lg)}B")

print("\n== (C) how often the Claude-fleet crons run (frequent = costly) ==")
r = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
freq = []
for line in (r.stdout or "").split("\n"):
    if not line.strip() or line.strip().startswith("#"): continue
    if "/Vintos/" not in line and "/.vintos/" not in line: continue
    m = line.split()[:5]
    sched = " ".join(m)
    # flag sub-hourly / hourly
    if m and (m[0].startswith("*/") or m[1] == "*" or m[0] == "*"):
        freq.append((sched, line.split()[-3:][0] if len(line.split()) > 6 else line[-40:]))
print(f"    {len(freq)} frequent (<=hourly) Vintos cron lines:")
for s, c in freq[:25]:
    print(f"      [{s}] ...{str(c)[-46:]}")
