#!/usr/bin/env python3
"""fix_vintos_crons.py — lock + spread Vintos's LLM cron jobs to mirror Velaris.

Wraps every Vintos cron whose script makes an LLM call (and runs on a single-minute
schedule) in the shared /home/gloria/llm-lock.sh, and scatters its minute off the
:37/:7 herd so the shared lock never backs up past its 15-min timeout. Leaves
untouched: Velaris (openclaw) jobs, env lines, @reboot, frequent/lightweight jobs
(minute contains * , */ or a comma), already-locked jobs, and a small exclude set.

Read-only until you install: writes /tmp/vintos-cron.new (review it, then
`crontab /tmp/vintos-cron.new`) and /tmp/vintos-cron.backup (the current crontab).
"""
import os, re, glob, subprocess

VINTOS_DIR = "/home/gloria/Vintos"
LOCK = "bash /home/gloria/llm-lock.sh "
EXCLUDE = {"living_trajectory.py", "latent_preparation.py", "gemma-watchdog.sh",
           "somatic-feedback.py", "somatic_bridge.py"}
LLM_PAT = re.compile(r"api\.x\.ai|x\.ai/v1|chat/completions|GROK|GEMMA|requests\.post|172\.18\.16\.1|:1234")

def llm_scripts():
    s = set()
    for f in glob.glob(VINTOS_DIR + "/*.py") + glob.glob(VINTOS_DIR + "/*.sh"):
        try:
            if LLM_PAT.search(open(f, errors="ignore").read()):
                s.add(os.path.basename(f))
        except Exception:
            pass
    return s

def main():
    cron = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout
    open("/tmp/vintos-cron.backup", "w").write(cron)
    LLM = llm_scripts()
    out, changes, counter = [], [], 0
    for line in cron.splitlines():
        if (not line.strip()) or line.lstrip().startswith("#") or line.lstrip().startswith("@") or re.match(r"^\s*\w+=", line):
            out.append(line); continue
        parts = line.split(None, 5)
        if len(parts) < 6:
            out.append(line); continue
        minute, hour, dom, mon, dow, cmd = parts
        is_vintos = ("/home/gloria/Vintos/" in cmd) or ("/.vintos/workspace/scripts/" in cmd)
        single_min = re.fullmatch(r"\d+", minute) is not None
        m = re.search(r"/([\w.\-]+\.(?:py|sh))\b", cmd)
        script = m.group(1) if m else None
        if (is_vintos and single_min and script in LLM and script not in EXCLUDE
                and "llm-lock.sh" not in cmd):
            new_min = str((counter * 13 + 2) % 60); counter += 1
            new_line = f"{new_min} {hour} {dom} {mon} {dow} {LOCK}{cmd}"
            out.append(new_line)
            changes.append((script, f"{minute} {hour}", f"{new_min} {hour}"))
        else:
            out.append(line)
    open("/tmp/vintos-cron.new", "w").write("\n".join(out) + "\n")
    print(f"Locked + spread {len(changes)} Vintos LLM jobs.")
    print("wrote  /tmp/vintos-cron.new   (review, then: crontab /tmp/vintos-cron.new)")
    print("backup /tmp/vintos-cron.backup")
    print("--- changes (script : old min/hr -> new min/hr, +shared lock) ---")
    for sc, old, new in changes:
        print(f"  {sc:34s} {old:>10s}  ->  {new}")

if __name__ == "__main__":
    main()
