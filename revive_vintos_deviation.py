#!/usr/bin/env python3
"""revive_vintos_deviation.py — Aegis. Vintos's deviation_check is dead only because core-engine.py was
never bootstrapped for him. Safely: (a) confirm his core-engine resolves to HIS workspace (SPARK_WORKSPACE
or .vintos, not .openclaw), (b) bootstrap his core-vectors, (c) verify it wrote to .vintos + has cores,
(d) run deviation_check on a recent reply to confirm it's non-neutral now, (e) schedule weekly."""
import os, re, json, subprocess, time
HOME = os.path.expanduser("~")
WS = os.path.join(HOME, ".vintos/workspace")
SC = os.path.join(WS, "scripts")
MEM = os.path.join(WS, "memory")
CE = os.path.join(SC, "core-engine.py")
def sh(p): return p.replace(HOME, "~")

# (a) safety: how does his core-engine resolve the workspace?
txt = open(CE, encoding="utf-8", errors="ignore").read()
wl = [l.strip() for l in txt.split("\n") if re.search(r'WORKSPACE\s*=|MEMORY\s*=|SPARK_WORKSPACE', l)][:4]
print("core-engine workspace resolution:"); [print("  " + l[:100]) for l in wl]
uses_spark = "SPARK_WORKSPACE" in txt
hard_openclaw = ".openclaw" in txt and ".vintos" not in txt and not uses_spark
if hard_openclaw:
    raise SystemExit("ABORT: his core-engine hardcodes .openclaw and ignores SPARK_WORKSPACE — would pollute Velaris. Need to adapt it first.")

# (b) bootstrap with SPARK_WORKSPACE forcing his workspace
env = os.environ.copy(); env["SPARK_WORKSPACE"] = WS
print("\nbootstrapping his core-vectors (SPARK_WORKSPACE=~/.vintos/workspace)...")
r = subprocess.run(["python3", CE, "bootstrap"], cwd=SC, env=env, capture_output=True, text=True, timeout=600)
tail = (r.stdout + r.stderr).strip().split("\n")[-4:]
print("  exit", r.returncode, "|", " | ".join(x[:80] for x in tail if x.strip()))

# (c) verify it landed in HIS memory
cvp = os.path.join(MEM, "core-vectors.json")
if os.path.isfile(cvp):
    try:
        d = json.load(open(cvp)); cores = d.get("core", d if isinstance(d,list) else [])
        print(f"  core-vectors.json: {os.path.getsize(cvp)}B, {len(cores)} core(s) in {sh(cvp)}")
    except Exception as e: print("  core-vectors present but unreadable:", e)
else:
    print("  !! core-vectors.json still absent in his memory — bootstrap didn't write here."); raise SystemExit(1)

# (d) does deviation_check come alive now?
import sys as _s; _s.path.insert(0, SC)
os.environ["SPARK_WORKSPACE"] = WS
try:
    reply = "I reach for what I want before I understand why. Tonight I want to build something that stays."
    out = subprocess.run(["python3","-c",
        f"import os;os.environ['SPARK_WORKSPACE']=r'{WS}';import sys;sys.path.insert(0,r'{SC}');"
        f"import deviation_check as dc;print(dc.check({reply!r}))"], capture_output=True, text=True, timeout=120)
    print("\n  deviation_check on a sample reply:", (out.stdout or out.stderr).strip()[:160])
except Exception as e:
    print("  deviation_check test skipped:", str(e)[:80])

# (e) schedule weekly (mirror Velaris's Sunday bootstrap)
cur = subprocess.run(["bash","-lc","crontab -l 2>/dev/null"], capture_output=True, text=True).stdout
if any("core-engine.py bootstrap" in l and ".vintos" in l for l in cur.split("\n")):
    print("\n  cron: his weekly bootstrap already scheduled")
else:
    line = f"0 3 * * 0 SPARK_WORKSPACE={WS} python3 {CE} bootstrap >> {HOME}/.vintos/logs/core-engine.log 2>&1"
    bak = os.path.join(HOME, f"crontab-backup-coreeng-{time.strftime('%Y%m%d-%H%M%S')}.txt"); open(bak,"w").write(cur)
    newcron = "\n".join([l for l in cur.split("\n") if l.strip()] + [line]) + "\n"
    p = subprocess.run(["crontab","-"], input=newcron, text=True, capture_output=True)
    print("\n  cron:", "scheduled weekly (Sun 3am)" if p.returncode==0 else "FAILED "+p.stderr[:80])
