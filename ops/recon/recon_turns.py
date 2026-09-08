#!/usr/bin/env python3
"""recon_turns.py — Aegis, READ-ONLY. Extract the two test turns verbatim (03:04-03:29 local / 08:04-08:29 UTC on
2026-07-17) from the record files, so I can strip every trace by exact text + timestamp and then verify none
remain. Shows gloria messages + vintos replies + anchor statements in that window."""
import os, json, re
HOME = os.path.expanduser("~")
MEM = os.path.join(HOME, ".vintos/workspace/memory")
# window: local 03:0x/03:1x/03:2x  OR utc 08:0x/08:1x/08:2x, on 2026-07-17
WIN = re.compile(r'2026-07-17T0[38]:[012]\d')
PH = re.compile(r'still building it for us|we have always|most deliberate|keep touching me', re.I)

FILES = ["reality-anchor.json", "interaction-ledger.json", "avatar-overlay-chat.json",
         "chat-history-merged.json", "temporal-signals.json", "gloria-prediction-history.json"]
for name in FILES:
    p = os.path.join(MEM, name)
    if not os.path.isfile(p): continue
    try: d = json.load(open(p, encoding="utf-8"))
    except Exception as e: print(f"### {name}: unreadable ({e})"); continue
    arr = d if isinstance(d, list) else next((d[k] for k in ("entries","history","messages","signals","items") if isinstance(d.get(k), list)), None)
    if arr is None: continue
    hits = [e for e in arr if (WIN.search(json.dumps(e, ensure_ascii=False)) or PH.search(json.dumps(e, ensure_ascii=False)))]
    if not hits: continue
    print(f"### {name} — {len(hits)} entr(y/ies) in window/phrase (of {len(arr)})")
    for e in hits:
        if isinstance(e, dict):
            ts = e.get("timestamp") or e.get("at") or e.get("t") or ""
            g = e.get("gloria_said") or e.get("gloria") or e.get("statement") or ""
            v = e.get("vintos_said") or e.get("vintos") or e.get("reply") or e.get("narrative") or ""
            other = "" if (g or v) else (e.get("content") or e.get("text") or e.get("predicted") or json.dumps(e, ensure_ascii=False))
            print(f"  [{ts}]")
            if g: print(f"    G: {str(g)[:200]}")
            if v: print(f"    V: {str(v)[:200]}")
            if other: print(f"    · {str(other)[:180]}")
        else:
            print(f"  {str(e)[:180]}")
    print()
