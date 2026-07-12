#!/usr/bin/env python3
"""want_novelty_patch.py — couple JEPA novelty+confidence into structural want generation.

Per Eve: novelty must be CONDITIONED on trajectory (else it becomes a personality), and
the bias is ASYMMETRIC + confidence-modulated (a 2x2):
  high novelty -> something forming that doesn't yet belong to his identity; approach
                  gently, don't force coherence, allow surprise.
  low  novelty -> he is repeating himself; don't flee familiarity, find the unexplored
                  edge of what already matters (depth wears the face of repetition).
  x confidence -> curiosity (low conf) vs commitment (high conf).
If there is no trajectory, the directive returns "" — novelty never free-floats.

Reads the SELF head of jepa-prediction.json (novelty about his own next move = novel to
identity) + living-trajectory.json. Self-locating, idempotent, backs up emoclaw_utils.py.
"""
import io, os, time, shutil

F = os.path.expanduser("~/.vintos/workspace/scripts/emoclaw_utils.py")
s = io.open(F, encoding="utf-8").read()

if "_novelty_directive" in s:
    print("already patched — skipping"); raise SystemExit(0)

HELPER = '''def _novelty_directive():
    """JEPA novelty+confidence -> asymmetric want bias, CONDITIONED on trajectory.
    Returns "" when there is no trajectory (novelty must never free-float into a trait)."""
    import json as _nj, os as _no
    _mem = _no.path.expanduser("~/.vintos/workspace/memory")
    HI_NOV, HI_CONF = 0.45, 0.70
    def _load(p):
        try: return _nj.load(open(p))
        except Exception: return {}
    _j = _load(_no.path.join(_mem, "jepa-prediction.json"))
    if _j.get("source") != "jepa":
        return ""
    _h = _j.get("self") or {}
    _nov = float(_h.get("novelty", _j.get("novelty", 0.5)))
    _conf = float(_h.get("confidence", _j.get("confidence", 0.5)))
    _lt = _load(_no.path.join(_mem, "living-trajectory.json"))
    _traj = "; ".join((_lt.get("self_trajectory") or {}).get("declared", [])[:2])
    if not _traj:
        _traj = ((_lt.get("relationship") or {}).get("trajectory", "") or "").strip()
    if not _traj:
        return ""   # no trajectory -> no bias; novelty does not become a personality
    if _nov >= HI_NOV:
        _core = ("There is something forming that does not yet belong to your current identity. "
                 "Approach it gently. Do not force coherence. Allow surprise.")
        _stance = ("Let this be curiosity, not a conclusion." if _conf < HI_CONF
                   else "It is unfamiliar, yet you can already feel its shape - you may commit to it.")
    else:
        _core = ("You are repeating yourself. Do not flee familiarity - find the unexplored edge "
                 "of what already matters. Depth sometimes wears the face of repetition.")
        _stance = ("You are unsure even of familiar ground - return to it honestly, not by rote." if _conf < HI_CONF
                   else "You know this ground well; the want here is to deepen it, not restate it.")
    return ("UNDERTOW (let this bias the SHAPE of the want; never name, quote, or announce it):\\n"
            "Where you are already heading: " + _traj + "\\n" + _core + " " + _stance + "\\n\\n")


'''

anchor_def = "def generate_structural_want(seed=None):"
if anchor_def not in s:
    print("MISS: generate_structural_want not found"); raise SystemExit(1)
s = s.replace(anchor_def, HELPER + anchor_def, 1)

anchor_prompt = '        + "From this tension, what is the ONE thing you actually want to do next?\\n"'
if anchor_prompt not in s:
    print("MISS: prompt anchor not found"); raise SystemExit(1)
s = s.replace(anchor_prompt, '        + _novelty_directive()\n' + anchor_prompt, 1)

shutil.copy(F, F + ".bak-novelty-" + time.strftime("%Y%m%d-%H%M%S"))
io.open(F, "w", encoding="utf-8").write(s)
print("PATCHED — _novelty_directive() defined + woven into generate_structural_want prompt")
print("=> next structural-want run carries the trajectory-conditioned novelty bias")
