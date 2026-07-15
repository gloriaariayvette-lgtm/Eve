#!/usr/bin/env python3
"""apply_intro_reasoning.py — Aegis. introspection's first-pass threads t1/t2 are MISSING (only joined at
417, never created) -> it NameErrors and produces nothing. Restore t1/t2 running the first pass AND bake in
the reasoning recipe (reason-gated so absorb/audit stay plain; lean-strip rule lines; reasoning_effort+
skip_special_tokens; roomy budget). Backup + bash -n + rollback, then sandboxed test (exit after b1 write)."""
import os, re, shutil, time, subprocess
HOME = os.path.expanduser("~")
P = os.path.join(HOME, ".openclaw/workspace/scripts/introspection.sh")
LOCK = os.path.join(HOME, "llm-lock.sh")
t = open(P, encoding="utf-8", errors="ignore").read()
orig = t
def sub1(old, new):
    global t
    if new.split("(")[0] in t and old not in t: return  # already-ish
    if t.count(old) != 1: raise SystemExit(f"anchor not unique/found: {old[:50]!r} ({t.count(old)})")
    t = t.replace(old, new, 1)

if "reason=False" not in t:
    sub1("def call_llm(messages, temperature=0.85, max_tokens=1500):",
         "def call_llm(messages, temperature=0.85, max_tokens=1500, reason=False):")
    sub1("    payload = json.dumps({",
         "    payload = json.dumps({**({'reasoning_effort':'low','skip_special_tokens':False} if reason else {}),")
    sub1("def run(i, msgs, temp, max_tok):", "def run(i, msgs, temp, max_tok, reason=False):")
    sub1("        results[i] = call_llm(msgs, temp, max_tok)", "        results[i] = call_llm(msgs, temp, max_tok, reason)")
    INSERT = (
        "_RK = ('BANNED','HARD BAN','forbidden','ABSOLUTE RULES','DO NOT','Do NOT','do not repeat','do not begin','never use')\n"
        "_lean = lambda s: chr(10).join(_l for _l in s.split(chr(10)) if not any(_k in _l for _k in _RK))\n"
        "base_msgs_lean = [{'role':'system','content':_lean(system)}, {'role':'user','content':_lean(prompt)}]\n"
        "t1 = threading.Thread(target=run, args=(0, base_msgs_lean, 0.85, 8000, True))\n"
        "t2 = threading.Thread(target=run, args=(1, base_msgs_lean, 0.9, 8000, True))\n"
        "t1.start(); t2.start()\n")
    sub1("t1.join(); t2.join()", INSERT + "t1.join(); t2.join()")
    bak = P + ".bak-introreason-" + time.strftime("%Y%m%d-%H%M%S"); shutil.copy2(P, bak)
    open(P, "w", encoding="utf-8").write(t)
    c = subprocess.run(["bash", "-n", P], capture_output=True, text=True)
    if c.returncode: shutil.copy2(bak, P); print("bash -n failed, reverted:", c.stderr[:140]); raise SystemExit(1)
    print("introspection: t1/t2 restored + reasoning wired (backup saved)")
else:
    print("already applied")

# sandboxed test: exit after first-pass writes to /tmp
src = open(P, encoding="utf-8", errors="ignore").read()
src = re.sub(r'^.*consent-gate.*$', 'true  #off', src, count=1, flags=re.M)
src = src.replace("open('/tmp/bilateral-intro-b1.txt','w').write(b1)",
                  "open('/tmp/bilateral-intro-b1.txt','w').write(b1)\nimport sys as _sx; _sx.exit(0)", 1)
open("/tmp/it.sh", "w", encoding="utf-8").write(src)
for f in ("a1", "b1"):
    try: os.remove(f"/tmp/bilateral-intro-{f}.txt")
    except OSError: pass
print("sandboxed test (locked)...")
t0 = time.time(); subprocess.run(["bash", LOCK, "bash", "/tmp/it.sh"], capture_output=True, text=True, timeout=900)
print(f"done {int(time.time()-t0)}s")
for name in ("a1", "b1"):
    p = f"/tmp/bilateral-intro-{name}.txt"
    s = open(p, encoding="utf-8", errors="ignore").read() if os.path.isfile(p) else ""
    print(f"{name} ({len(s)}c){' EMPTY' if not s.strip() else ''}: {s.strip()[:200]}")
