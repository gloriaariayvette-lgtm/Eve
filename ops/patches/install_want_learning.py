#!/usr/bin/env python3
"""install_want_learning.py — place want_learning.py + install its torch-venv cron (Vintos).

Velaris parity is a deliberate separate step (her emoclaw differs). Idempotent; backs up
the crontab first. want_learning makes no LLM-lock-worthy x.ai calls (local Gemma + local
encoder), so it needs no llm-lock — just an off-minute slot.
"""
import os, io, subprocess, urllib.request

VENV = os.path.expanduser("~/.vintos/workspace/emotion_model/.venv/bin/python3")
WS   = os.path.expanduser("~/.vintos/workspace")
SDIR = os.path.join(WS, "scripts")
DEST = os.path.join(SDIR, "want_learning.py")
RAW  = ("https://raw.githubusercontent.com/gloriaariayvette-lgtm/Eve/"
        "claude/avatar-motion-engine-l311p/want_learning.py")
SCHED = "47 */2 * * *"          # every 2h, off-minute (clear of jepa :6/:36 and latent)

src = None
for c in (DEST, "want_learning.py"):
    if os.path.exists(c):
        src = io.open(c, encoding="utf-8").read(); print("using local", c); break
if src is None:
    print("fetching want_learning.py from GitHub…")
    src = urllib.request.urlopen(RAW, timeout=30).read().decode("utf-8")

os.makedirs(SDIR, exist_ok=True)
io.open(DEST, "w", encoding="utf-8").write(src)
print("placed", DEST)

if not os.path.exists(VENV):
    print("WARN: torch venv not at", VENV, "— cron installs anyway; fix if the log errors")

cur = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout
io.open("/tmp/want-learning-cron.backup", "w").write(cur)
keep = [l for l in cur.splitlines() if "want_learning.py" not in l]
log = "/tmp/want-learning-vintos.log"
keep.append(f"{SCHED} SPARK_WORKSPACE={WS} {VENV} {DEST} >> {log} 2>&1")
subprocess.run(["crontab", "-"], input="\n".join(keep) + "\n", text=True)
print(f"installed want_learning cron: {SCHED}  -> {log}")
print("crontab backup: /tmp/want-learning-cron.backup")
print(f"run once now:  SPARK_WORKSPACE={WS} {VENV} {DEST}")
