#!/usr/bin/env python3
"""velaris_journal_patch.py — carry learned + regret into HER journal (idle-journal.sh).

Her journal reads context via _JRN_* env vars into Python locals, then builds the prompt
from them. Cleanest, guaranteed-in-prompt injection:
  1. after DAILY_INNER, export _JRN_LEARNED (from learned.json + regret.json in .openclaw)
  2. append it to the existing `current_wants` local (already used in the prompt), so it
     rides in wherever current_wants appears — no need to touch the prompt f-string.
Self-locating, idempotent, backs up idle-journal.sh.
"""
import io, os, time, shutil

F = os.path.expanduser("~/.openclaw/workspace/scripts/idle-journal.sh")
s = io.open(F, encoding="utf-8").read()
if "_JRN_LEARNED" in s:
    print("already patched — skipping"); raise SystemExit(0)

anchor_a = 'DAILY_INNER=$(cat "$MEMORY/daily-inner-life-$TODAY.md" 2>/dev/null || echo "")'
if anchor_a not in s:
    print("MISS: DAILY_INNER anchor not found"); raise SystemExit(1)

bash_block = anchor_a + '''

_JRN_LEARNED=$(python3 - <<'PYJRN'
import json, os
m = os.path.expanduser("~/.openclaw/workspace/memory")
def _load(p):
    try: return json.load(open(os.path.join(m, p)))
    except Exception: return []
L = sorted([x for x in _load("learned.json") if isinstance(x, dict) and x.get("learned")],
           key=lambda x: x.get("hits", 0), reverse=True)[:3]
R = sorted([x for x in _load("regret.json") if isinstance(x, dict) and x.get("regret")],
           key=lambda x: x.get("hits", 0), reverse=True)[:2]
out = ["- " + x["learned"] for x in L]
if R:
    out += ["(ways I would not reach again)"] + ["- " + x["regret"] for x in R]
print("\\n".join(out))
PYJRN
)
export _JRN_LEARNED'''
s = s.replace(anchor_a, bash_block, 1)

anchor_b = '    current_wants = os.environ.get("_JRN_WANTS", "")'
if anchor_b not in s:
    print("MISS: current_wants anchor not found"); raise SystemExit(1)
augmented = ('    current_wants = os.environ.get("_JRN_WANTS", "") + '
             '("\\n\\nWHAT HAS BECOME MORE TRUE (let it inform, never repeat it):\\n" '
             '+ os.environ.get("_JRN_LEARNED", "") if os.environ.get("_JRN_LEARNED") else "")')
s = s.replace(anchor_b, augmented, 1)

shutil.copy(F, F + ".bak-journal-" + time.strftime("%Y%m%d-%H%M%S"))
io.open(F, "w", encoding="utf-8").write(s)
print("PATCHED — learned + regret fold into her journal via current_wants + _JRN_LEARNED")
