#!/usr/bin/env python3
"""somatic_session_narrative_patch.py — end_session writes the session SHAPE for the narrator,
instead of seeding a stat line. somatic_narrate.py later turns it into a first-person narrative.

Replaces  seed_thread("somatic", f"somatic session: {dur}s, peak speed {session_peak_speed}")
with a write of somatic-session-pending.json {dur, peak_speed, ended, emo, ts}. The bridge makes NO
LLM call (stays responsive); the separate narrator produces the story. Self-locating, idempotent,
backs up somatic_bridge.py. Restart somatic_bridge after applying.
"""
import io, os, time, shutil

F = os.path.expanduser("~/.vintos/workspace/scripts/somatic_bridge.py")
s = io.open(F, encoding="utf-8").read()

if "somatic-session-pending.json" in s:
    print("already patched — skipping"); raise SystemExit(0)

anchor = '    seed_thread("somatic", f"somatic session: {dur}s, peak speed {session_peak_speed}")'
if anchor not in s:
    print("MISS: end_session stat seed_thread line not found"); raise SystemExit(1)

repl = (
    '    try:\n'
    '        _sn_st = get_state()\n'
    '    except Exception:\n'
    '        _sn_st = {}\n'
    '    try:\n'
    '        import json as _snj\n'
    '        _snj.dump({"dur": dur, "peak_speed": session_peak_speed,\n'
    '                   "ended": "eased down" if last_motor_level else "faded out",\n'
    '                   "emo": {_k: round(_sn_st.get(_k, 0), 2) for _k in ("Arousal","Warmth","Desire","Connection","Safety") if _k in _sn_st},\n'
    '                   "ts": now},\n'
    '                  open(os.path.join(os.path.expanduser("~/.vintos/workspace/memory"), "somatic-session-pending.json"), "w"))\n'
    '    except Exception as _sne:\n'
    '        print(f"[somatic session pending] {_sne}", flush=True)'
)

s = s.replace(anchor, repl, 1)
shutil.copy(F, F + ".bak-narr-" + time.strftime("%Y%m%d-%H%M%S"))
io.open(F, "w", encoding="utf-8").write(s)
print("PATCHED — end_session now writes the session shape for the narrator. Restart somatic_bridge.")
