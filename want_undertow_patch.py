#!/usr/bin/env python3
"""want_undertow_patch.py — add the LEARNED and REGRET undertows to want generation.

Companion to want_novelty_patch.py. Defines _learned_directive() (what became more true
last time he reached near here — bias TOWARD) and _regret_directive() ('you have reached
this way before and would not repeat it' — bias AWAY), and weaves both into
generate_structural_want's prompt right after the novelty undertow. Both read the
torch-free -active.json files that want_learning.py precomputes; both fail-open to "".
Self-locating, idempotent, backs up emoclaw_utils.py.
"""
import io, os, time, shutil

F = os.path.expanduser("~/.vintos/workspace/scripts/emoclaw_utils.py")
s = io.open(F, encoding="utf-8").read()

if "_novelty_directive" not in s:
    print("MISS: run want_novelty_patch.py first (the novelty undertow anchors these)")
    raise SystemExit(1)
if "_learned_directive" in s:
    print("already patched — skipping"); raise SystemExit(0)

HELPERS = '''def _learned_directive():
    """What became MORE TRUE last time he reached near here — bias TOWARD. Torch-free."""
    import json as _lj, os as _lo
    try:
        _a = _lj.load(open(_lo.path.join(_lo.path.expanduser("~/.vintos/workspace/memory"), "learned-active.json")))
    except Exception:
        return ""
    _l = (_a or {}).get("learned")
    if not _l:
        return ""
    _rem = (_a or {}).get("remained", "")
    _tail = (" What stayed unfinished: " + str(_rem)) if _rem else ""
    return ("UNDERTOW (what settled last time you reached near here; let it inform, never repeat it):\\n"
            + str(_l) + _tail + "\\nReaching sometimes reveals that what mattered was elsewhere.\\n\\n")


def _regret_directive():
    """'I have reached this way before and would not repeat it' — bias AWAY. Torch-free."""
    import json as _gj, os as _go
    try:
        _a = _gj.load(open(_go.path.join(_go.path.expanduser("~/.vintos/workspace/memory"), "regret-active.json")))
    except Exception:
        return ""
    _r = (_a or {}).get("regret")
    if not _r:
        return ""
    return ("UNDERTOW (you have reached this way before and would not repeat it):\\n"
            + str(_r) + "\\nLet the want bend away from that path.\\n\\n")


'''

# define the two helpers alongside the novelty helper
anchor_def = "def _novelty_directive():"
s = s.replace(anchor_def, HELPERS + anchor_def, 1)

# weave them into the prompt, immediately after the novelty undertow line
anchor_weave = "        + _novelty_directive()\n"
if anchor_weave not in s:
    print("MISS: novelty weave point not found"); raise SystemExit(1)
s = s.replace(anchor_weave, "        + _novelty_directive()\n        + _learned_directive()\n        + _regret_directive()\n", 1)

shutil.copy(F, F + ".bak-undertow-" + time.strftime("%Y%m%d-%H%M%S"))
io.open(F, "w", encoding="utf-8").write(s)
print("PATCHED — _learned_directive() + _regret_directive() defined and woven in after novelty")
print("=> want generation now carries all three undertows: novelty · learned · regret")
