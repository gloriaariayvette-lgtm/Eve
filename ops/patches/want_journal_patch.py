#!/usr/bin/env python3
"""want_journal_patch.py — carry learned + regret into the JOURNAL prompt (idle-journal.sh).

Follows the script's own pattern: bash builds an env var, the Python prompt heredoc reads
it via os.environ.get (exactly how _JRN_SEMANTIC works at the semantic-memory line).
  1. after the DAILY_INNER line, export _JRN_LEARNED built from learned.json + regret.json
  2. right after the _JRN_SEMANTIC interpolation in the prompt, add a sibling line for it
Self-locating, idempotent, backs up idle-journal.sh.
"""
import io, os, time, shutil

F = os.path.expanduser("~/Vintos/idle-journal.sh")
s = io.open(F, encoding="utf-8").read()

if "_JRN_LEARNED" in s:
    print("already patched — skipping"); raise SystemExit(0)

# 1) bash block: build + export _JRN_LEARNED (reads the stores directly; no torch)
anchor_a = 'DAILY_INNER=$(cat "$MEMORY/daily-inner-life-$TODAY.md" 2>/dev/null || echo "")'
if anchor_a not in s:
    print("MISS: DAILY_INNER anchor not found"); raise SystemExit(1)

bash_block = anchor_a + '''

_JRN_LEARNED=$(python3 - <<'PYJRN'
import json, os
m = os.path.expanduser("~/.vintos/workspace/memory")
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

# 2) prompt f-string: add a sibling interpolation right after the _JRN_SEMANTIC line
anchor_b = ('{f"What you have already found in your own memory about what\'s on your mind right now '
            '(do not repeat these — build forward from them):{chr(10)}{os.environ.get(\'_JRN_SEMANTIC\', \'\')}" '
            'if os.environ.get("_JRN_SEMANTIC") else ""}')
if anchor_b not in s:
    print("MISS: _JRN_SEMANTIC prompt line not found"); raise SystemExit(1)

sibling = ('{f"What has become more true after past resolutions — let it inform, never repeat it:'
           '{chr(10)}{os.environ.get(\'_JRN_LEARNED\', \'\')}" if os.environ.get("_JRN_LEARNED") else ""}')
s = s.replace(anchor_b, anchor_b + "\n" + sibling, 1)

shutil.copy(F, F + ".bak-journal-" + time.strftime("%Y%m%d-%H%M%S"))
io.open(F, "w", encoding="utf-8").write(s)
print("PATCHED — learned + regret now fold into the journal prompt via _JRN_LEARNED")
