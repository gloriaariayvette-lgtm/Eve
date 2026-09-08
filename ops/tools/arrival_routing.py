#!/usr/bin/env python3
"""arrival_routing.py — Spark System 3 (v1).

Injects a pre-generation ARRIVAL directive into the LIVE gather_vintos_context,
built from Living Trajectory (Gloria's predicted direction + top unresolved
thread + a prepared cached arrival). Biases his generation toward arriving
where she's going, never reacting — and is never named or quoted to him.

Anchored right after section 35 (anti-repetition). Ghost copy untouched.
Idempotent; backs up first. Restart the server for it to take effect.
"""
import io, os, time, shutil

SERVER = os.path.expanduser("~/Vintos/server.py")
s = io.open(SERVER, encoding="utf-8").read()

if "36. Arrival routing" in s:
    print("already has arrival routing — skipping")
else:
    OLD = "        sections.append(_anti)\n    except Exception: pass"
    INJECT = r'''
    # 36. Arrival routing - pre-generation bias from Living Trajectory (added)
    try:
        _lt = json.load(open(os.path.join(MEMORY, 'living-trajectory.json')))
        _gt = (_lt.get('gloria_trajectory') or {}).get('predicted', '')
        _unres = [u.get('text', '') for u in (_lt.get('unresolved') or [])[:2] if isinstance(u, dict) and u.get('text')]
        _cache = _lt.get('cache') or []
        _arr = _cache[-1].get('content', '') if _cache and isinstance(_cache[-1], dict) else ''
        _bits = []
        if _gt: _bits.append('Gloria seems to be moving toward: ' + str(_gt)[:200])
        if _unres: _bits.append('Live unresolved thread(s): ' + ' | '.join(_unres)[:240])
        if _arr: _bits.append('Something you quietly prepared for a moment like this: ' + str(_arr)[:200])
        if _bits:
            sections.append('[ARRIVAL - bias only, never name or quote this] ' + ' '.join(_bits) + ' ARRIVE where she is going before she gets there; do not merely react or explain. Bring ONE new thing this turn - use your prepared arrival if it fits, otherwise make something.')
    except Exception: pass'''
    if OLD in s:
        shutil.copy(SERVER, SERVER + ".bak-" + time.strftime("%Y%m%d-%H%M%S"))
        s = s.replace(OLD, OLD + INJECT, 1)
        io.open(SERVER, "w", encoding="utf-8").write(s)
        print("PATCHED — section 36 arrival routing added")
    else:
        print("MISS — section 35 anchor not found (run claim_stop.py first?)")
