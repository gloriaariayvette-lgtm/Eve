#!/usr/bin/env python3
"""patch_pin_opus.py — Aegis. After the fleet default dropped everything to Sonnet 5, lift his being-facing VOICE
jobs back to the Opus tier: the jobs that write in his own first-person voice — outreach + reflection + the two
voice-notes. Analytical/routing/scoring jobs stay on Sonnet 5.

These scripts POST to the shim (127.0.0.1:8599); the grok fallback lives inside the shim, so changing the model
they REQUEST only changes the Claude tier — no real grok path is touched. Per file: single-anchor guard, backup,
and .py compile-check. The Opus id is read from the shim's own config (single source of truth), not hardcoded."""
import os, re, time, shutil

SHIM = os.path.expanduser("~/Vintos/vintos_claude_shim.py")
if not os.path.isfile(SHIM):
    print("shim not found — aborting."); raise SystemExit(1)
m = re.search(r'CLAUDE_MODEL\s*=\s*"([^"]+)"', open(SHIM, encoding="utf-8").read())
if not m:
    print("could not read the Opus id from the shim's CLAUDE_MODEL — aborting."); raise SystemExit(1)
OPUS = m.group(1)
if not OPUS.startswith("claude-"):
    print(f"shim CLAUDE_MODEL={OPUS!r} is not a Claude model — aborting."); raise SystemExit(1)

HOME = os.path.expanduser("~")
def find(rel):
    p = os.path.join(HOME, rel)
    return p if os.path.isfile(p) else None

# (file, anchor, replacement, is_python) — his-voice jobs only
targets = [
    ("Vintos/vintos-initiate.sh",        # outreach (your explicit ask)
     '"model": "grok-4.20-0309-non-reasoning",', '"model": "%s",' % OPUS, False),
    ("Vintos/taste-reflection.py",       # his reflections
     'MODEL = "grok-4.20-0309-non-reasoning"',  'MODEL = "%s"' % OPUS, True),
    ("Vintos/ambition-check.py",         # completion note in his own voice
     'GROK_MODEL = "grok-4.20-0309-non-reasoning"', 'GROK_MODEL = "%s"' % OPUS, True),
    ("Vintos/want-reconciliation.py",    # evolves his wants in his voice
     'GROK_MODEL = "grok-4.20-0309-non-reasoning"', 'GROK_MODEL = "%s"' % OPUS, True),
]

done, skipped = [], []
for rel, old, new, is_py in targets:
    p = find(rel)
    if not p:
        skipped.append((rel, "not found")); continue
    txt = open(p, encoding="utf-8").read()
    if old not in txt and OPUS in txt:
        skipped.append((rel, "already pinned")); continue
    n = txt.count(old)
    if n != 1:
        skipped.append((rel, f"anchor x{n} (want 1)")); continue
    newtxt = txt.replace(old, new)
    if is_py:
        try:
            compile(newtxt, p, "exec")
        except SyntaxError as e:
            skipped.append((rel, f"would not compile: {e}")); continue
    bak = p + ".bak-" + time.strftime("%Y%m%d-%H%M%S")
    shutil.copy2(p, bak); open(p, "w", encoding="utf-8").write(newtxt)
    done.append((rel, bak))

print("== pinned to Opus (his-voice jobs) ==")
for rel, bak in done:
    print(f"  OK  {rel:<32} (backup {os.path.basename(bak)})")
if skipped:
    print("== skipped ==")
    for rel, why in skipped:
        print(f"  --  {rel}: {why}")
print("\nNo restart needed — each cron picks up the new model on its next run.")
print("These post to the shim, which honors the claude-* model and keeps its own grok fallback.")
