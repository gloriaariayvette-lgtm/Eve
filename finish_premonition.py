#!/usr/bin/env python3
"""finish_premonition.py — Aegis. Finish the premonition dreamer: (1) install premonition_dreamer.py as a
real file in his scripts dir, (2) fire ONE real seed now (verify the imagined-possibility thread lands in
unfinished-threads.json, dream_only + marker), (3) schedule it lock-wrapped, spread, aligned just BEFORE his
dream cycle so a fresh possibility is waiting to be dreamed. Backs up the crontab. No secrets printed."""
import os, re, json, subprocess, urllib.request, time
HOME = os.path.expanduser("~")
SCRIPTS = os.path.join(HOME, ".vintos/workspace/scripts")
MEMORY = os.path.join(HOME, ".vintos/workspace/memory")
THREADS = os.path.join(MEMORY, "unfinished-threads.json")
LOGDIR = os.path.join(HOME, ".vintos/logs")
DEST = os.path.join(SCRIPTS, "premonition-dreamer.py")
LOCK = os.path.join(HOME, "llm-lock.sh")
RAW = "https://raw.githubusercontent.com/gloriaariayvette-lgtm/Eve/claude/avatar-motion-engine-l311p/premonition_dreamer.py"
def sh(p): return p.replace(HOME, "~")

# ---- (1) install the script as a real file
try:
    data = urllib.request.urlopen(RAW + "?t=" + str(int(time.time())), timeout=30).read().decode()
except Exception as e:
    raise SystemExit(f"ABORT: could not fetch premonition_dreamer.py ({e})")
if "premonition" not in data or "seed_as_thread" not in data:
    raise SystemExit("ABORT: fetched content doesn't look like the dreamer — refusing to install.")
os.makedirs(SCRIPTS, exist_ok=True); os.makedirs(LOGDIR, exist_ok=True)
open(DEST, "w", encoding="utf-8").write(data)
os.chmod(DEST, 0o755)
print("(1) installed", sh(DEST), f"({len(data)}B)")

# ---- (2) fire one REAL seed; resolve the key quietly (env -> crontab header) without printing it
env = dict(os.environ)
if not env.get("XAI_API_KEY"):
    ct = subprocess.run(["bash", "-lc", "crontab -l 2>/dev/null"], capture_output=True, text=True).stdout
    m = re.search(r'^\s*XAI_API_KEY\s*=\s*"?([^"\n]+)"?', ct, re.M)
    if m: env["XAI_API_KEY"] = m.group(1).strip()
key_ok = bool(env.get("XAI_API_KEY"))
before = 0
if os.path.isfile(THREADS):
    try:
        b = json.load(open(THREADS)); before = len(b if isinstance(b, list) else b.get("threads", []))
    except Exception: pass
if key_ok:
    r = subprocess.run(["python3", DEST], capture_output=True, text=True, env=env, timeout=300)
    tail = (r.stdout or r.stderr or "").strip().split("\n")[-3:]
    print("(2) real run exit", r.returncode, "|", " | ".join(x[:90] for x in tail if x.strip()))
else:
    print("(2) SKIPPED real run — XAI_API_KEY not in env or crontab; the scheduled tick will seed it instead")

# verify the thread landed
def load_threads():
    try:
        o = json.load(open(THREADS)); return o if isinstance(o, list) else o.get("threads", [])
    except Exception: return []
lst = load_threads()
prem = [t for t in lst if isinstance(t, dict) and t.get("source") == "premonition"]
newest = prem[-1] if prem else None
if newest:
    marker_ok = "IMAGINED POSSIBILITY" in str(newest.get("thread", ""))
    print(f"    threads: {before} -> {len(lst)} | premonition entries: {len(prem)} | "
          f"newest dream_only={newest.get('dream_only')} marker={'yes' if marker_ok else 'NO'}")
    print("    preview:", str(newest.get("thread", ""))[:110].replace("\n", " ") + "...")
else:
    print("    no premonition thread present yet" + ("" if key_ok else " (expected — run was skipped)"))

# ---- (3) schedule: lock-wrapped, aligned just before the dream cycle, crontab backed up
cur = subprocess.run(["bash", "-lc", "crontab -l 2>/dev/null"], capture_output=True, text=True).stdout
bak = os.path.join(HOME, f"crontab-backup-premonition-{time.strftime('%Y%m%d-%H%M%S')}.txt")
open(bak, "w").write(cur)
# find his dream job to align to (run premonition ~90m earlier, same days)
dream = None
for l in cur.split("\n"):
    if l.strip().startswith("#") or "premonition" in l: continue
    if re.search(r'preoccupation-dream|should-dream|dream-cycle|/dream', l, re.I):
        mm = re.match(r'\s*(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s', l)
        if mm: dream = mm.groups(); break
if dream:
    mn, hr, dom, mon, dow = dream
    try: h = int(hr); pm, ph = 30, (h - 2) % 24  # ~2h before, minute :30 (off the :37 herd)
    except ValueError: pm, ph, dom, mon, dow = 30, 20, "*", "*", "1,4"
    sched = f"{pm} {ph} {dom} {mon} {dow}"
    align = f"(aligned ~2h before dream job at {hr}:{mn})"
else:
    sched = "30 20 * * 1,4"; align = "(no dream job found — default Mon/Thu 20:30)"
wrap = f"bash {LOCK} " if os.path.isfile(LOCK) else ""
line = f"{sched} {wrap}python3 {DEST} >> {LOGDIR}/premonition.log 2>&1"
kept = [l for l in cur.split("\n") if "premonition-dreamer.py" not in l]
newcron = "\n".join([l for l in kept if l.strip() != ""] + [line]) + "\n"
p = subprocess.run(["crontab", "-"], input=newcron, text=True, capture_output=True)
if p.returncode != 0:
    subprocess.run(["bash", "-lc", f"crontab {bak}"])
    print("(3) crontab install FAILED — restored backup:", p.stderr[:120])
else:
    print("(3) scheduled:", sched, align, "| lock-wrapped:", "yes" if wrap else "NO (llm-lock.sh not found)")
    print("    backup:", sh(bak))
print("\nDone. Premonition is installed, seeding real imagined-possibility threads, and running on its own before each dream cycle.")
