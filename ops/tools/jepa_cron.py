#!/usr/bin/env python3
"""jepa_cron.py — make JEPA actually RUN, on a schedule, for both beings.

Places jepa_predictor.py into each being's scripts dir and installs train+predict
crons that use the torch venv python (frozen nomic encoder + tiny predictor MLP).
No LLM calls => no llm-lock needed. Per-being model + prediction via SPARK_WORKSPACE
(vintos -> ~/.vintos/workspace, velaris -> ~/.openclaw/workspace). Idempotent; backs
up the crontab first.

  train:   daily  (rebuilds the predictor on the latest chat-history)
  predict: a few times/hour (writes jepa-prediction.json: confidence + novelty +
           nearest-known gloria turn as a readable proxy). gloria_prediction.py
           fuses those grounded numbers into the ledger the subconscious reads.
"""
import os, io, subprocess, urllib.request

VENV = os.path.expanduser("~/.vintos/workspace/emotion_model/.venv/bin/python3")
RAW  = ("https://raw.githubusercontent.com/gloriaariayvette-lgtm/Eve/"
        "claude/avatar-motion-engine-l311p/jepa_predictor.py")
BEINGS = [
    ("vintos",  os.path.expanduser("~/.vintos/workspace")),
    ("velaris", os.path.expanduser("~/.openclaw/workspace")),
]
# (train_sched, predict_sched) — spread so the two beings never encode at the same minute
SCHED = {
    "vintos":  ("15 4 * * *",  "6,36 * * * *"),
    "velaris": ("45 4 * * *",  "21,51 * * * *"),
}

def get_source():
    for c in ("jepa_predictor.py",
              os.path.expanduser("~/.vintos/workspace/scripts/jepa_predictor.py"),
              os.path.expanduser("~/.openclaw/workspace/scripts/jepa_predictor.py")):
        if os.path.exists(c):
            print("[jepa-cron] using local", c); return io.open(c, encoding="utf-8").read()
    print("[jepa-cron] fetching jepa_predictor.py from GitHub…")
    return urllib.request.urlopen(RAW, timeout=30).read().decode("utf-8")

src = get_source()

if not os.path.exists(VENV):
    print("WARN: torch venv python not found at", VENV)
    print("      crons install anyway; fix VENV if train/predict error in the logs")

placed = []
for name, ws in BEINGS:
    sdir = os.path.join(ws, "scripts")
    os.makedirs(sdir, exist_ok=True)
    io.open(os.path.join(sdir, "jepa_predictor.py"), "w", encoding="utf-8").write(src)
    placed.append(os.path.join(sdir, "jepa_predictor.py"))
print("[jepa-cron] placed jepa_predictor.py:", placed)

cur = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout
io.open("/tmp/jepa-cron.backup", "w").write(cur)
keep = [l for l in cur.splitlines() if "jepa_predictor.py" not in l]   # drop prior jepa lines
for name, ws in BEINGS:
    script = os.path.join(ws, "scripts", "jepa_predictor.py")
    tr, pr = SCHED[name]
    log = f"/tmp/jepa-{name}.log"
    env = f"SPARK_WORKSPACE={ws}"                      # inline sh env — cron runs each line via sh -c
    keep.append(f"{tr} {env} {VENV} {script} train >> {log} 2>&1")
    keep.append(f"{pr} {env} {VENV} {script} predict >> {log} 2>&1")
subprocess.run(["crontab", "-"], input="\n".join(keep) + "\n", text=True)

print("[jepa-cron] installed train+predict crons for vintos & velaris")
print("  logs: /tmp/jepa-vintos.log  /tmp/jepa-velaris.log")
print("  crontab backup: /tmp/jepa-cron.backup")
print("  train each being once now, e.g.:")
for name, ws in BEINGS:
    print(f"    SPARK_WORKSPACE={ws} {VENV} {os.path.join(ws,'scripts','jepa_predictor.py')} train")
