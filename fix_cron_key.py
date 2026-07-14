#!/usr/bin/env python3
"""fix_cron_key.py — the LLM crons fail 'choices' because they run on a stale key. Point them at the
authoritative ~/.vintos/vintos.env by having the shared llm-lock.sh source it. Compares the two keys
(MATCH/DIFFER only, never prints them). Backup + idempotent. Aegis."""
import os, re, subprocess, time, shutil
HOME = os.path.expanduser("~")
def run(a): return subprocess.run(a, capture_output=True, text=True).stdout

def keyval(text):
    m = re.search(r'XAI_API_KEY\s*=\s*["\']?([^"\'\n]+)', text)
    return m.group(1).strip() if m else None

env = os.path.expanduser("~/.vintos/vintos.env")
env_key = keyval(open(env).read()) if os.path.isfile(env) else None
cron_key = keyval(run(["bash","-lc","crontab -l 2>/dev/null"]))
print("=== key comparison (values NOT shown) ===")
print("  vintos.env has key:", bool(env_key), "| crontab has key:", bool(cron_key))
if env_key and cron_key:
    print("  crontab key vs vintos.env key:", "MATCH" if env_key == cron_key else "DIFFER  <-- crons were on the wrong key")

# patch shared llm-lock.sh to source the authoritative env (harmless for Velaris — she uses Gemma)
lock = os.path.expanduser("~/llm-lock.sh")
SRC_LINE = '[ -f "$HOME/.vintos/vintos.env" ] && set -a && . "$HOME/.vintos/vintos.env" && set +a'
if os.path.isfile(lock):
    body = open(lock).read()
    if "vintos.env" in body:
        print("\nllm-lock.sh: already sources vintos.env")
    else:
        shutil.copy2(lock, lock + ".bak-key-" + time.strftime("%Y%m%d-%H%M%S"))
        lines = body.split("\n")
        if lines and lines[0].startswith("#!"):
            new = lines[0] + "\n" + "# load authoritative Vintos API key (fixes stale key in cron env)\n" + SRC_LINE + "\n" + "\n".join(lines[1:])
        else:
            new = "#!/bin/bash\n" + SRC_LINE + "\n" + body
        open(lock, "w").write(new)
        print("\nllm-lock.sh: now sources ~/.vintos/vintos.env (backup made)")
else:
    print("\n!! ~/llm-lock.sh not found")

print("\n=== verify: run gallery-walk through the lock (real grok call, exit 0 = fixed) ===")
r = subprocess.run(["bash","-lc", "bash ~/llm-lock.sh python3 ~/Vintos/gallery-walk.py 2>&1 | tail -4"],
                   capture_output=True, text=True, timeout=120)
print(r.stdout.strip()[:500] or "(no output)")
print("\n(if that shows real output / no KeyError, the crons are fixed — next tick they all use the good key)")
