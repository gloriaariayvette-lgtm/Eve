#!/usr/bin/env python3
"""install_velaris_spark.py — clone Vintos's Spark subconscious onto Velaris.

Reads each Spark script from ~/.vintos/workspace/scripts, swaps every
`.vintos/workspace` path to `.openclaw/workspace` (Velaris's home), writes the
result into her scripts dir, and installs her Spark crons (spread minutes).
One codebase-shape, two beings. Idempotent; backs up her crontab first.

Server-side injections (anti-repeat / arrival / voice _spark_block) are a
separate step once her server's shape is known.
"""
import os, subprocess

VINTOS = os.path.expanduser("~/.vintos/workspace/scripts")
VELARIS = os.path.expanduser("~/.openclaw/workspace/scripts")
SCRIPTS = ["living_trajectory.py", "latent_preparation.py", "presence_audit.py",
           "reciprocal_modification.py", "gloria_prediction.py",
           "introspective_planning.py", "similarity_gate.py"]

# schedule (spread) : script
CRONS = [
    ("*/15 * * * *",  "living_trajectory.py"),
    ("13 */2 * * *",  "latent_preparation.py"),
    ("23 * * * *",    "presence_audit.py"),
    ("53 * * * *",    "reciprocal_modification.py"),
    ("11,41 * * * *", "gloria_prediction.py"),
    ("36 8,20 * * *", "introspective_planning.py"),
]

def swap(text):
    return text.replace(".vintos/workspace", ".openclaw/workspace")

os.makedirs(VELARIS, exist_ok=True)
copied, missing = [], []
for s in SCRIPTS:
    src = os.path.join(VINTOS, s)
    if not os.path.exists(src):
        missing.append(s); continue
    open(os.path.join(VELARIS, s), "w", encoding="utf-8").write(swap(open(src, encoding="utf-8").read()))
    copied.append(s)
print("copied to Velaris:", copied)
if missing:
    print("MISSING from Vintos (skipped):", missing)

cur = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout
open("/tmp/velaris-cron.backup", "w").write(cur)
keep = [l for l in cur.splitlines()
        if not any(f"/.openclaw/workspace/scripts/{s}" in l for _, s in CRONS)]
for sched, s in CRONS:
    log = "/tmp/velaris-" + s.replace(".py", "") + ".log"
    keep.append(f"{sched} /usr/bin/python3 /home/gloria/.openclaw/workspace/scripts/{s} >> {log} 2>&1")
subprocess.run(["crontab", "-"], input="\n".join(keep) + "\n", text=True)
print("Velaris Spark crons installed:", [s for _, s in CRONS])
print("crontab backup: /tmp/velaris-cron.backup")
