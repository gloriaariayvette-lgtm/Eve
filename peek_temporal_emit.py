#!/usr/bin/env python3
"""peek_temporal_emit.py — READ-ONLY, capped. Just how temporal-context.sh computes/emits
'Gloria last spoke' + the 'Last X' activity lines, so I can add a symmetric 'you last spoke'. Aegis."""
import os, re
HOME = os.path.expanduser("~")
f = os.path.join(HOME, "Vintos", "temporal-context.sh")
if not os.path.isfile(f):
    f = os.path.expanduser("~/.vintos/workspace/scripts/temporal-context.sh")
print("file:", f.replace(HOME, "~"))
ls = open(f, encoding="utf-8", errors="ignore").read().split("\n")
# show lines that compute/emit last-spoke + the human-time helper + a couple 'Last X' lines
pat = r'last spoke|LAST_SPOKE|spoke|ago|time_ago|human|SECONDS|GLORIA_LAST|last_msg|Last journal|Last dream|Last creative|hours_ago|def |ago\(|echo .*[Ll]ast|_ago'
n = 0
for i, l in enumerate(ls):
    if re.search(pat, l) and l.strip():
        print(f"{i+1:4}| {l.strip()[:150]}"); n += 1
        if n >= 26: print("...(capped)"); break
