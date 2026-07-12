#!/usr/bin/env python3
"""gcs_surface_patch.py — surface saved sets in his body context so he can reach them back.

Adds saved_sets_block() (recent, dedup'd sets from gcs-saved-patterns.json) and folds it into
device_context.context_block(), which is injected into his avatar/voice chats. Now he SEES
what brought her to the edge before and can fire [DO: both last] or one by name. Empty-safe.
Self-locating, idempotent, backs up device_context.py.
"""
import io, os, time, shutil

F = os.path.expanduser("~/.vintos/workspace/scripts/device_context.py")
s = io.open(F, encoding="utf-8").read()
if "saved_sets_block" in s:
    print("already patched — skipping"); raise SystemExit(0)

HELPER = '''def saved_sets_block():
    """Recent, dedup'd sets that preceded a GCS press. Empty string if none."""
    import os as _o, json as _j
    try:
        _lib = _j.load(open(_o.path.expanduser("~/.vintos/workspace/memory/gcs-saved-patterns.json")))
    except Exception:
        return ""
    seen, lines = set(), []
    for e in reversed(_lib or []):
        pats = e.get("patterns", {})
        key = tuple(sorted(pats.items()))
        if not pats or key in seen:
            continue
        seen.add(key)
        vals = set(pats.values())
        if len(pats) == 2 and len(vals) == 1:
            lines.append("- " + next(iter(vals)) + "  (both)")
        else:
            lines.append("- " + " · ".join(f"{p} ({t})" for t, p in pats.items()))
        if len(lines) >= 3:
            break
    if not lines:
        return ""
    return ("[SETS THAT BROUGHT HER TO THE EDGE BEFORE — reach one back with [DO: both last], or by name]\\n"
            + "\\n".join(lines))


'''

anchor_def = "def context_block():"
if anchor_def not in s:
    print("MISS: context_block not found"); raise SystemExit(1)
s = s.replace(anchor_def, HELPER + anchor_def, 1)

anchor_parts = "    parts = [CAPABILITIES, live_state_block()]"
if anchor_parts not in s:
    print("MISS: parts init not found"); raise SystemExit(1)
s = s.replace(anchor_parts,
              anchor_parts + "\n    _ss = saved_sets_block()\n    if _ss: parts.append(_ss)", 1)

shutil.copy(F, F + ".bak-surface-" + time.strftime("%Y%m%d-%H%M%S"))
io.open(F, "w", encoding="utf-8").write(s)
print("PATCHED — saved sets now surface in his body context (reach back with [DO: both last])")
