#!/usr/bin/env python3
"""patch_shim_fleet.py — Aegis. Stop billing utility work at Opus prices.

Today claude_complete() ignores the model the caller sends and forces the global Opus model for EVERY text call,
so the high-frequency chore jobs (somatic_narrate ~144x/day, voice_session_ledger ~144x/day, avatar-choice
~48x/day) all silently run on Opus. That is the bulk of the daily spend.

After this patch the shim text path is model-aware:
  - caller sends a Claude model id (starts with 'claude-')  -> honored as-is
        (idle-journal + introspection already send the Opus id, so they stay on Opus untouched)
  - caller sends a grok id / empty / anything else          -> falls to FLEET_DEFAULT (Sonnet 5), not Opus
Grok fallback path is untouched. model_router (avatar + both chats) is untouched. Backed up + compile-checked."""
import os, time, shutil

FLEET_DEFAULT = "claude-sonnet-5"   # important-utility tier; chore jobs get moved to the /gemma path in a later step

P = os.path.expanduser("~/Vintos/vintos_claude_shim.py")
if not os.path.isfile(P):
    print("shim not found:", P); raise SystemExit(1)
txt = open(P, encoding="utf-8").read()

if "FLEET_DEFAULT" in txt:
    print("already patched."); raise SystemExit(0)

edits = [
    # 1. define the fleet default (anchored on the log-path constant so we never write the Opus id here)
    ('LOG = "/tmp/vintos-claude-shim.log"',
     'FLEET_DEFAULT = "%s"\nLOG = "/tmp/vintos-claude-shim.log"' % FLEET_DEFAULT),
    # 2. let claude_complete accept a per-call model
    ('def claude_complete(messages, max_tokens):',
     'def claude_complete(messages, max_tokens, model=None):'),
    # 3. honor a caller-supplied Claude model, else fleet default (never silently Opus again)
    ('body = {"model": CLAUDE_MODEL, "max_tokens": int(max_tokens or 1024),',
     'body = {"model": (model if str(model or "").startswith("claude-") else FLEET_DEFAULT), '
     '"max_tokens": int(max_tokens or 1024),'),
    # 4. pass the caller's requested model through
    ('text = claude_complete(j.get("messages", []), j.get("max_tokens"))',
     'text = claude_complete(j.get("messages", []), j.get("max_tokens"), j.get("model"))'),
]

for old, _new in edits:
    n = txt.count(old)
    if n != 1:
        print(f"anchor x{n} (want 1): {old[:58]!r} -- aborting, no change made."); raise SystemExit(1)
for old, new in edits:
    txt = txt.replace(old, new)

try:
    compile(txt, P, "exec")
except SyntaxError as e:
    print(f"would not compile ({e}) -- aborting."); raise SystemExit(1)

bak = P + ".bak-" + time.strftime("%Y%m%d-%H%M%S")
shutil.copy2(P, bak)
open(P, "w", encoding="utf-8").write(txt)
print("OK. shim text path is now model-aware.")
print("  - a caller sending a claude-* model keeps it (idle-journal / introspection stay on Opus)")
print(f"  - every other text call now defaults to {FLEET_DEFAULT} instead of Opus")
print(f"  backup: {bak}")
print("  ACTIVATE:  systemctl --user restart vintos-claude-shim")
