#!/usr/bin/env python3
"""Edit only, no LLM call. Add forward-progress framing to the journal writing prompt: name what you made
today + one concrete next step (forward motion). Backup + bash -n."""
import os, shutil, time, subprocess
HOME = os.path.expanduser("~")
P = os.path.join(HOME, ".openclaw/workspace/scripts/idle-journal.sh")
t = open(P, encoding="utf-8", errors="ignore").read()
anchor = 'user_msg = _topic_prefix + _concrete_header + """'
inject = ('user_msg = _topic_prefix + _concrete_header + """\n'
          'WHAT YOU MADE / WHAT\'S NEXT: Name concretely what you actually made or did today. '
          'Then end by naming ONE specific thing you want to DO next — a real next step you can take, '
          'an action, not a feeling to sit with. Forward motion, not stillness.\n')
if "WHAT YOU MADE / WHAT'S NEXT" in t:
    print("forward-progress framing already present")
elif t.count(anchor) == 1:
    bak = P + ".bak-fwd-" + time.strftime("%Y%m%d-%H%M%S"); shutil.copy2(P, bak)
    open(P, "w", encoding="utf-8").write(t.replace(anchor, inject, 1))
    if subprocess.run(["bash", "-n", P], capture_output=True, text=True).returncode:
        shutil.copy2(bak, P); print("bash -n failed, reverted"); raise SystemExit(1)
    print("journal now prompts: what you made today + one concrete next step (backup saved)")
else:
    print(f"anchor found {t.count(anchor)}x — not editing; tell me and I'll re-anchor")
