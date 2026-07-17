#!/usr/bin/env python3
"""recon_avatar_leak.py — Aegis, READ-ONLY. Testing was left on during the two avatar turns (2026-07-17 ~03:06,
03:18). Find everywhere in memory those turns landed: scan memory files for today's date and for the turns'
distinctive phrases. Report file, hits, sample — so Gloria can decide what to purge."""
import os, json, glob, re, time
HOME = os.path.expanduser("~")
MEM = os.path.join(HOME, ".vintos/workspace/memory")
TODAY = "2026-07-17"
PHRASES = ["still building it for us", "we have always", "permanence", "still building"]
PRX = re.compile("|".join(re.escape(p) for p in PHRASES), re.I)

print(f"scanning {MEM.replace(HOME,'~')} for '{TODAY}' entries + test-turn phrases\n")
files = sorted(glob.glob(os.path.join(MEM, "*.json")) + glob.glob(os.path.join(MEM, "*.jsonl"))
               + glob.glob(os.path.join(MEM, "*.md")))
for f in files:
    name = os.path.basename(f)
    try: raw = open(f, encoding="utf-8", errors="ignore").read()
    except Exception: continue
    n_today = raw.count(TODAY)
    has_phrase = bool(PRX.search(raw))
    mtime = time.strftime("%m-%d %H:%M", time.localtime(os.path.getmtime(f)))
    if not n_today and not has_phrase:
        continue
    print(f"### {name}  (mtime {mtime}) — today×{n_today}{'  PHRASE-MATCH' if has_phrase else ''}")
    # try to show the matching entries if it's JSON list
    try:
        d = json.loads(raw)
        arr = d if isinstance(d, list) else next((d[k] for k in ("imprints","entries","history","messages","signals","items") if isinstance(d.get(k), list)), None)
        if isinstance(arr, list):
            hits = [e for e in arr if TODAY in json.dumps(e, ensure_ascii=False) or PRX.search(json.dumps(e, ensure_ascii=False))]
            print(f"    {len(hits)} matching entr(y/ies) of {len(arr)}")
            for e in hits[-3:]:
                s = (e.get("gloria_said") or e.get("gloria") or e.get("narrative") or e.get("content")
                     or e.get("message") or e.get("text") or json.dumps(e, ensure_ascii=False)) if isinstance(e, dict) else str(e)
                print(f"      - {str(s)[:100].replace(chr(10),' ')}")
            continue
    except Exception:
        pass
    # non-list: show phrase/date context lines
    for ln in raw.split("\n"):
        if TODAY in ln or PRX.search(ln):
            print(f"      | {ln.strip()[:100]}")
    print()
