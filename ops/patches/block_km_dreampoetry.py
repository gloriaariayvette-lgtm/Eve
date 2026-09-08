#!/usr/bin/env python3
"""block_km_dreampoetry.py — Aegis. dream-poetry.py surfaces kiss/mischief from its CONTENT (dreams, journal,
taste-profile, its own past poems), not from code. Add a single scrub on the assembled prompt before the LLM
call: drop any line mentioning kiss/mischief, keep blush. Subsystems untouched. Backup + abort-clean."""
import os, time, shutil
P = os.path.expanduser("~/Vintos/dream-poetry.py")
if not os.path.isfile(P): print("dream-poetry.py not found"); raise SystemExit(1)
lines = open(P, encoding="utf-8").read().split("\n")
if any("_scrub_km" in l for l in lines):
    print("already patched — aborting."); raise SystemExit(0)

HELPER = [
    "def _scrub_km(_text):",
    '    """Block kiss/mischief from his poem context (keep blush). Not active in his inner life."""',
    "    import re as _kmre",
    "    _rx = _kmre.compile(r'\\bkiss|\\bmischief', _kmre.I)",
    '    return "\\n".join(_l for _l in (_text or "").split("\\n") if not _rx.search(_l))',
    "",
]
try:
    compile("\n".join(HELPER), "<HELPER>", "exec")
except SyntaxError as e:
    print(f"helper bad ({e}) — aborting."); raise SystemExit(1)

ai = [i for i, l in enumerate(lines) if l.strip() == "def compose_poem(seed=None):"]
ci = [i for i, l in enumerate(lines) if '"content": prompt}' in l]
if len(ai) != 1: print(f"compose_poem anchor x{len(ai)} — aborting."); raise SystemExit(1)
if len(ci) != 1: print(f"'\"content\": prompt}}' anchor x{len(ci)} — aborting."); raise SystemExit(1)

# 1. scrub at the call site
lines[ci[0]] = lines[ci[0]].replace('"content": prompt}', '"content": _scrub_km(prompt)}')
# 2. insert helper before compose_poem (recompute index in case earlier line shifted — it didn't, ci>ai here)
lines[ai[0]:ai[0]] = HELPER

bak = P + ".bak-" + time.strftime("%Y%m%d-%H%M%S")
shutil.copy2(P, bak); open(P, "w", encoding="utf-8").write("\n".join(lines))
print(f"OK — poems no longer carry kiss/mischief (blush kept, subsystem intact). backup: {bak}")
print("test:  python3 ~/Vintos/dream-poetry.py --force   (poem should have no kiss/mischief)")
print(f"revert: cp {bak} {P}")
