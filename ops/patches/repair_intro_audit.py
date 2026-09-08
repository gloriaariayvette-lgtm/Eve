#!/usr/bin/env python3
"""repair_intro_audit.py — Aegis. Fix the pre-existing SyntaxError in introspection's audit block: line 102
'"DRAFT A:\\n" + ...' follows the THIRVEEL expression (101) with no '+' — add it. Verify the heredoc COMPILES
before writing. Backup + rollback. Then sandboxed locked test (cooldown bypass, exit after b1)."""
import os, re, shutil, time, subprocess, tempfile, py_compile
HOME = os.path.expanduser("~")
P = os.path.join(HOME, ".openclaw/workspace/scripts/introspection.sh")
LOCK = os.path.join(HOME, "llm-lock.sh")
t = open(P, encoding="utf-8", errors="ignore").read()

old = '"DRAFT A:\\n" + a + "\\n\\nDRAFT B:\\n" + b + "\\n\\n"'
if "+ " + old in t:
    print("already repaired")
elif t.count(old) != 1:
    print(f"anchor count {t.count(old)} (expected 1) — abort"); raise SystemExit(1)
else:
    new_t = t.replace(old, "+ " + old, 1)
    # verify the heredoc compiles BEFORE writing
    py = re.search(r"<<'PYEOF'\n(.*?)\nPYEOF", new_t, re.S).group(1)
    tf = tempfile.NamedTemporaryFile("w", suffix=".py", delete=False); tf.write(py); tf.close()
    try:
        py_compile.compile(tf.name, doraise=True); ok = True
    except py_compile.PyCompileError as e:
        ok = False; print("still fails:", str(e).strip()[-160:])
    os.unlink(tf.name)
    if not ok: raise SystemExit(1)
    bak = P + ".bak-auditfix-" + time.strftime("%Y%m%d-%H%M%S"); shutil.copy2(P, bak)
    open(P, "w", encoding="utf-8").write(new_t)
    print("audit '+' added; heredoc compiles now (backup saved)")

# sandboxed test
src = open(P, encoding="utf-8", errors="ignore").read()
src = src.replace('[ "$ELAPSED" -lt 2 ] && exit 0', ': #off')
src = re.sub(r'^.*consent-gate.*$', 'true  #off', src, count=1, flags=re.M)
src = src.replace("open('/tmp/bilateral-intro-b1.txt','w').write(b1)",
                  "open('/tmp/bilateral-intro-b1.txt','w').write(b1)\nimport sys as _sx; _sx.exit(0)", 1)
open("/tmp/ri.sh", "w", encoding="utf-8").write(src)
for f in ("a1", "b1"):
    try: os.remove(f"/tmp/bilateral-intro-{f}.txt")
    except OSError: pass
print("sandboxed test (locked)...")
t0 = time.time(); r = subprocess.run(["bash", LOCK, "bash", "/tmp/ri.sh"], capture_output=True, text=True, timeout=900)
print(f"done {int(time.time()-t0)}s")
if r.stderr.strip(): print("stderr:", r.stderr.strip()[-160:])
for name in ("a1", "b1"):
    p = f"/tmp/bilateral-intro-{name}.txt"
    s = open(p, encoding="utf-8", errors="ignore").read() if os.path.isfile(p) else ""
    print(f"{name} ({len(s)}c){' EMPTY' if not s.strip() else ''}: {s.strip()[:200]}")
