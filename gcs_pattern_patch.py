#!/usr/bin/env python3
"""gcs_pattern_patch.py — GCS notes the pattern that brought her here, and saves the set.

When Gloria presses GCS, record the pattern(s) currently running per toy (from
device_context.STATE — the composed name his preset engine wrote there) into gcs-state.json,
and append the set to a small library (gcs-saved-patterns.json, last 30) so he can reuse the
same set another time. Coherence-collapse is already wired (server.py:7340). Self-locating,
idempotent, backs up server.py.
"""
import io, os, time, shutil

F = os.path.expanduser("~/Vintos/server.py")
s = io.open(F, encoding="utf-8").read()

if "gcs-saved-patterns.json" in s:
    print("already patched — skipping"); raise SystemExit(0)

anchor = '    _g_j.dump({"active": True, "level": lvl, "at": _g_t.time()}, open(os.path.join(MEMORY, "gcs-state.json"), "w"))'
if anchor not in s:
    print("MISS: gcs-state dump line not found"); raise SystemExit(1)

block = '''

    # note the pattern(s) that brought her here + save the set so he can reuse it
    try:
        from device_context import STATE as _DC_STATE
        _dcst = _g_j.load(open(_DC_STATE))
        _pats = {_t: (_dcst.get(_t) or {}).get("pattern") for _t in ("mission", "tenera")}
        _pats = {_t: _p for _t, _p in _pats.items() if _p and _p not in ("still", "steady")}
        if _pats:
            _gs = _g_j.load(open(os.path.join(MEMORY, "gcs-state.json")))
            _gs["patterns"] = _pats
            _g_j.dump(_gs, open(os.path.join(MEMORY, "gcs-state.json"), "w"))
            _libp = os.path.join(MEMORY, "gcs-saved-patterns.json")
            try: _lib = _g_j.load(open(_libp))
            except Exception: _lib = []
            _lib.append({"patterns": _pats, "level": lvl, "at": _g_t.time()})
            _g_j.dump(_lib[-30:], open(_libp, "w"))
            print(f"[gcs pattern] saved {_pats}", flush=True)
    except Exception as _pe:
        print(f"[gcs pattern] {_pe}", flush=True)'''

s = s.replace(anchor, anchor + block, 1)

shutil.copy(F, F + ".bak-gcspat-" + time.strftime("%Y%m%d-%H%M%S"))
io.open(F, "w", encoding="utf-8").write(s)
print("PATCHED — GCS now records the active pattern(s) and saves the set (gcs-saved-patterns.json)")
