#!/usr/bin/env python3
"""fix_server_key.py — the vintos-server systemd unit has no XAI_API_KEY, so all grok calls get
'bad-credentials'. Write the key (from the shell env where it's valid) into a 0600 EnvironmentFile and
wire the unit to load it, then reload+restart. Verifies the key is in the new process env. Key is never
printed. Run on Aegis in your normal shell (so XAI_API_KEY is set):  python3 fix_server_key.py
"""
import os, subprocess

def sh(c): return subprocess.run(c, shell=True, capture_output=True, text=True)

key = os.environ.get("XAI_API_KEY", "")
if not key:
    print("ABORT: XAI_API_KEY not in this shell. Run it in the shell where `echo ${#XAI_API_KEY}` is >0."); raise SystemExit(1)

ENVFILE = os.path.expanduser("~/.vintos/vintos.env")
os.makedirs(os.path.dirname(ENVFILE), exist_ok=True)
# write/refresh the env file (key + anything else the server needs), lock it down
with open(ENVFILE, "w") as f:
    f.write("XAI_API_KEY=%s\n" % key)
os.chmod(ENVFILE, 0o600)
print("wrote key -> %s (chmod 600, len %d)" % (ENVFILE, len(key)))

unit = sh("systemctl --user show -p FragmentPath --value vintos-server").stdout.strip()
if not unit or not os.path.exists(unit):
    print("ABORT: could not find the unit file (FragmentPath empty)."); raise SystemExit(1)
print("unit:", unit)
txt = open(unit).read()

ef_line = "EnvironmentFile=%h/.vintos/vintos.env"
if "vintos.env" in txt:
    print("EnvironmentFile already wired in unit.")
else:
    lines = txt.splitlines()
    out, inserted = [], False
    for ln in lines:
        out.append(ln)
        if ln.strip() == "[Service]" and not inserted:
            out.append(ef_line); inserted = True
    if not inserted:  # no [Service]? fall back to appending under it
        out.append(ef_line)
    open(unit, "w").write("\n".join(out) + "\n")
    print("added:", ef_line)

sh("systemctl --user daemon-reload")
r = sh("systemctl --user restart vintos-server")
if r.returncode != 0:
    print("restart error:", r.stderr[:200])

# wait for it to come up, then verify the key is in the new process env
import time
pid = ""
for _ in range(30):
    pid = sh("systemctl --user show -p MainPID --value vintos-server").stdout.strip()
    if pid.isdigit() and int(pid) > 0 and os.path.exists("/proc/%s" % pid):
        # is the port answering yet?
        c = sh('curl -s -o /dev/null -w "%%{http_code}" http://localhost:8500/api/voice/chat').stdout.strip()
        if c and c != "000": break
    time.sleep(1)
env = sh("tr '\\0' '\\n' < /proc/%s/environ 2>/dev/null | grep -c '^XAI_API_KEY='" % pid).stdout.strip()
print("\nserver PID:", pid, "| XAI_API_KEY in server env now:", "YES" if env == "1" else "NO")
print("done — his grok calls should authenticate now (chat, TTS, and the voice token mint).")
