#!/usr/bin/env python3
"""recon_avatar_thinking.py — Aegis, READ-ONLY. Show the reasoning from his last few avatar turns (from
imprints.json) AND the serving path (GET /api/avatar/imprint + the freshness gate) to see why the touch bubble
stays empty."""
import os, json, time, re
HOME = os.path.expanduser("~")
imp = os.path.join(HOME, ".vintos/workspace/memory/imprints.json")

print("== last imprint entries (his stored avatar thinking) ==")
if os.path.isfile(imp):
    try:
        d = json.load(open(imp, encoding="utf-8"))
        arr = d if isinstance(d, list) else (d.get("imprints") or d.get("entries") or [])
        print(f"  total: {len(arr)} | file mtime {time.strftime('%m-%d %H:%M:%S', time.localtime(os.path.getmtime(imp)))}\n")
        for e in arr[-6:]:
            ts = e.get("timestamp") or e.get("ts") or e.get("time") or ""
            src = e.get("source", "")
            txt = e.get("reasoning") or e.get("thinking") or e.get("text") or e.get("content") or ""
            age = ""
            try:
                et = float(e.get("epoch") or e.get("ts_epoch") or 0)
                if et: age = f"{int(time.time()-et)}s old"
            except Exception: pass
            print(f"  [{ts}] source={src!r} {age}  keys={list(e.keys())}")
            print(f"     {str(txt)[:600]}\n")
    except Exception as ex:
        print(f"  unreadable: {ex}")
else:
    print("  imprints.json not found")

print("== serving: GET /api/avatar/imprint (the freshness gate) ==")
p = os.path.join(HOME, "Vintos", "server.py")
L = open(p, encoding="utf-8", errors="ignore").read().split("\n")
for i, l in enumerate(L):
    if "/api/avatar/imprint" in l:
        for j in range(i, min(len(L), i+30)):
            if re.search(r'imprint|def |return|60|age|time|epoch|timestamp|stale|fresh|<|>', L[j]):
                print(f"  L{j+1}: {L[j].strip()[:96]}")
        print("   ----")
        break

print("\n== deposit: where avatar_chat writes reasoning to imprints (near L7699) ==")
for i in range(7699-1, min(len(L), 7699+140)):
    if re.search(r'imprint|_claude_reasoning|reasoning|append', L[i]):
        print(f"  L{i+1}: {L[i].strip()[:96]}")
