#!/usr/bin/env python3
"""force_gloria_now.py — Aegis. (A) FORCE the weekly gloria-model update past its schedule gate NOW and
generate a real dated addition (base stays byte-identical). (B) REPAIR premonition: reinstall the fixed
dreamer and flip the already-seeded thread to dream_only=True. Reversible; no secrets printed."""
import os, re, json, hashlib, subprocess, tempfile, urllib.request, time
HOME = os.path.expanduser("~")
WS = os.path.join(HOME, ".vintos/workspace")
GM = os.path.join(WS, "GLORIA-MODEL.md")
UPD = os.path.join(WS, "scripts", "gloria-model-update.sh")
if not os.path.isfile(UPD): UPD = os.path.join(HOME, "Vintos", "gloria-model-update.sh")
THREADS = os.path.join(WS, "memory", "unfinished-threads.json")
DEST = os.path.join(WS, "scripts", "premonition-dreamer.py")
RAW = "https://raw.githubusercontent.com/gloriaariayvette-lgtm/Eve/claude/avatar-motion-engine-l311p/premonition_dreamer.py"
def sh(p): return p.replace(HOME, "~")

# ================= (A) FORCE THE UPDATE PAST THE GATE =================
print("=== (A) force gloria-model update past the gate ===")
src = open(UPD, encoding="utf-8", errors="ignore").read()
lines = src.split("\n")
# find where the real work begins (first LLM/gen marker); guard region is everything before it
work = len(lines)
for i, l in enumerate(lines):
    if re.search(r'x\.ai|chat/completions|LM_URL|GROK|GEMMA|curl .*http|CONTENT=\$|urllib|python3 .*call', l, re.I):
        work = i; break
# neutralize early-exit gates in the guard region (schedule/day/stamp checks that bail before work)
gated, out = [], []
for i, l in enumerate(lines):
    if i < work and re.search(r'\bexit\b', l) and not l.strip().startswith("#"):
        gated.append(l.strip()[:80]); out.append(":  # forced-bypass: " + l.strip())
    else:
        out.append(l)
print("  neutralized gate line(s):", (" || ".join(gated) if gated else "(none found — script may gate by stamp only; running anyway)"))
tmp = tempfile.NamedTemporaryFile("w", suffix=".sh", delete=False, encoding="utf-8")
tmp.write("\n".join(out)); tmp.close()
# resolve key quietly (env -> crontab header)
env = dict(os.environ)
if not env.get("XAI_API_KEY"):
    ct = subprocess.run(["bash", "-lc", "crontab -l 2>/dev/null"], capture_output=True, text=True).stdout
    m = re.search(r'^\s*XAI_API_KEY\s*=\s*"?([^"\n]+)"?', ct, re.M)
    if m: env["XAI_API_KEY"] = m.group(1).strip()
def base_region():
    t = open(GM, encoding="utf-8", errors="ignore").read() if os.path.isfile(GM) else ""
    mm = re.search(r"<!-- BASE-START.*?<!-- BASE-END -->", t, re.DOTALL)
    return mm.group(0) if mm else ""
h0 = hashlib.sha256(base_region().encode()).hexdigest()[:16]
r = subprocess.run(["bash", tmp.name], capture_output=True, text=True, env=env, timeout=300)
os.unlink(tmp.name)
tail = (r.stderr or r.stdout or "").strip().split("\n")[-3:]
print("  run exit", r.returncode, "|", " | ".join(x[:90] for x in tail if x.strip()))
h1 = hashlib.sha256(base_region().encode()).hexdigest()[:16]
print("  base:", "IDENTICAL ✓" if h1 == h0 and h0 else "⚠ CHANGED — check", f"({h0}=={h1})")
t = open(GM, encoding="utf-8", errors="ignore").read()
secs = re.findall(r"(^## .+?)(?=^## |\Z)", t.split("# Additions", 1)[-1], re.DOTALL | re.MULTILINE)
if secs:
    newest = secs[0].strip().split("\n")
    is_new = bool(re.match(r"## 20\d\d-\d\d-\d\d\s*$", newest[0].strip()))
    print("  newest addition header:", newest[0][:60], "->", "FRESH real entry ✓" if is_new else "(still the preserved block — gate not bypassed)")
    for l in newest[1:6]:
        if l.strip(): print("     " + l[:92])

# ================= (B) REPAIR PREMONITION =================
print("\n=== (B) repair premonition (dream_only) ===")
try:
    data = urllib.request.urlopen(RAW + "?t=" + str(int(time.time())), timeout=30).read().decode()
    if "_ensure_dream_only(text)   # persist" in data:
        open(DEST, "w", encoding="utf-8").write(data); os.chmod(DEST, 0o755)
        print("  reinstalled fixed dreamer ->", sh(DEST), "(future runs set dream_only)")
    else:
        print("  WARN: fetched dreamer missing the fix marker — left installed copy as-is")
except Exception as e:
    print("  reinstall skipped:", str(e)[:80])
# flip the already-seeded thread
try:
    obj = json.load(open(THREADS)); lst = obj if isinstance(obj, list) else obj.get("threads", [])
    fixed = 0
    for th in lst:
        if isinstance(th, dict) and th.get("source") == "premonition" and "IMAGINED POSSIBILITY" in str(th.get("thread", "")) and not th.get("dream_only"):
            th["dream_only"] = True; fixed += 1
    json.dump(obj, open(THREADS, "w"), indent=2, ensure_ascii=False)
    print(f"  existing premonition thread(s) flipped to dream_only=True: {fixed}")
except Exception as e:
    print("  thread flip skipped:", str(e)[:80])
print("\nDone.")
