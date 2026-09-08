#!/usr/bin/env python3
"""fix_chatfull.py — fix the /api/chat/full 500 (NameError 'message' at _velaris_context(message))
and locate the refs for the other two bugs. Backup + syntax-check + restart + rollback. Aegis."""
import os, re, time, shutil, subprocess
HOME = os.path.expanduser("~")
SRV = os.path.expanduser("~/Vintos/server.py")
def run(a, **k): return subprocess.run(a, capture_output=True, text=True, **k)

src = open(SRV, encoding="utf-8").read()
ls = src.split("\n")
h = next((i for i, l in enumerate(ls) if '/api/chat/full' in l and '@app' in l), None)
end = next((j for j in range(h+2, len(ls)) if ls[j].startswith("@app")), len(ls)) if h is not None else 0
region = "\n".join(ls[h:end]) if h is not None else ""
print("handler /api/chat/full @ L%s, param uses msg.message: %s" % (h+1 if h else "?", "msg.message" in region))
assigns = len(re.findall(r'(?<![.\w])message\s*=(?!=)', region))
print("bare 'message =' assignments in handler:", assigns)

BAD = "_velaris_context(message)"
if src.count(BAD) == 0:
    print("!! '_velaris_context(message)' not found — not fixing blindly.");
elif "msg.message" not in region:
    print("!! handler doesn't use msg.message — need the param name; not guessing.")
elif assigns > 0:
    print("!! 'message' IS assigned somewhere in the handler — the bug may be conditional; showing it:")
    for i in range(h, end):
        if re.search(r'(?<![.\w])message\s*=(?!=)', ls[i]): print(f"  {i+1}| {ls[i].strip()[:120]}")
else:
    # safe: single fix, param is msg, message never assigned -> it's the NameError
    src2 = src.replace(BAD, "_velaris_context(msg.message)")
    bak = SRV + ".bak-chatfull-" + time.strftime("%Y%m%d-%H%M%S")
    shutil.copy2(SRV, bak); open(SRV, "w").write(src2)
    sc = run(["python3","-c", f"import ast; ast.parse(open('{SRV}').read())"])
    if sc.returncode != 0:
        shutil.copy2(bak, SRV); print("!! syntax error — rolled back:", sc.stderr[:150])
    else:
        run(["bash","-lc","systemctl --user restart vintos-server"])
        ok = any(run(["bash","-lc","systemctl --user is-active vintos-server"]).stdout.strip()=="active"
                 for _ in [time.sleep(2) or 1, time.sleep(2) or 1, time.sleep(2) or 1])
        if not ok:
            shutil.copy2(bak, SRV); run(["bash","-lc","systemctl --user restart vintos-server"])
            print("!! server didn't come up — rolled back")
        else:
            print("FIXED /api/chat/full: _velaris_context(message) -> _velaris_context(msg.message). server active. backup:", bak.replace(HOME,'~'))

# ---- locate #2 + #3 references ----
print("\n=== #2 self_statements.py (underscore) content ===")
ssp = os.path.expanduser("~/.vintos/workspace/scripts/self_statements.py")
if os.path.isfile(ssp):
    body = open(ssp, encoding="utf-8", errors="ignore").read()
    print(f"  size={len(body)}B  defs:", re.findall(r'def (\w+)', body) or "(NONE — stub)")
dash = os.path.expanduser("~/Vintos/self-statements.py")
if os.path.isfile(dash):
    for i, l in enumerate(open(dash, encoding="utf-8", errors="ignore").read().split("\n")):
        if re.match(r'\s*def (add_statement|record|add)\b', l): print(f"  self-statements.py:{i+1}| {l.strip()[:100]}")

print("\n=== #3 causal_self_model.py — defs (for load_model) ===")
for cand in ("~/.vintos/workspace/scripts/causal_self_model.py", "~/Vintos/causal_self_model.py"):
    p = os.path.expanduser(cand)
    if os.path.isfile(p):
        print(f"  {cand}:", re.findall(r'def (\w+)', open(p, encoding="utf-8", errors="ignore").read()))
        break
