#!/usr/bin/env python3
"""fix_chatfull_copy.py — the LIVE /api/chat/full copy (last-registered, L~11014) uses 'message'
without assigning it -> 500 NameError. Insert 'message = msg.message' at the top of that handler,
mirroring the working copy. Backup + syntax-check + restart + rollback. Aegis."""
import os, re, time, shutil, subprocess
HOME = os.path.expanduser("~")
SRV = os.path.expanduser("~/Vintos/server.py")
def run(a, **k): return subprocess.run(a, capture_output=True, text=True, **k)

src = open(SRV, encoding="utf-8").read()
ls = src.split("\n")
handlers = [i for i, l in enumerate(ls) if '/api/chat/full' in l and '@app' in l]
if len(handlers) < 2:
    print("expected 2 copies, found", [h+1 for h in handlers]); raise SystemExit(1)
target = max(handlers)                       # the live one (last registered)
end = next((j for j in range(target+2, len(ls)) if ls[j].startswith("@app")), len(ls))

# already fixed?
if any(re.search(r'(?<![.\w])message\s*=\s*msg\.message', ls[k]) for k in range(target, end)):
    print("copy @ L%d already assigns message = msg.message — nothing to do" % (target+1)); raise SystemExit(0)

# locate the async def + end of its signature
di = next((i for i in range(target, min(target+6, len(ls))) if re.search(r'\bdef \w+\(', ls[i])), None)
if di is None: print("could not find def"); raise SystemExit(1)
sig, si = "", di
while si < len(ls):
    sig += ls[si]
    if ls[si].rstrip().endswith(":"): break
    si += 1
if "msg" not in sig:
    print("handler param isn't 'msg' — not guessing. signature:", sig[:120]); raise SystemExit(1)

# insertion point: after signature, skipping a docstring if present
ins = si + 1
s0 = ls[ins].strip()
if s0[:3] in ('"""', "'''"):
    q = s0[:3]
    if len(s0) > 5 and s0.endswith(q):
        ins += 1
    else:
        j = ins + 1
        while j < len(ls) and q not in ls[j]:
            j += 1
        ins = j + 1

ls.insert(ins, "    message = msg.message")
print("inserting at L%d (handler @ L%d)" % (ins+1, target+1))
new = "\n".join(ls)

bak = SRV + ".bak-chatfull2-" + time.strftime("%Y%m%d-%H%M%S")
shutil.copy2(SRV, bak); open(SRV, "w").write(new)
sc = run(["python3","-c", f"import ast; ast.parse(open('{SRV}').read())"])
if sc.returncode != 0:
    shutil.copy2(bak, SRV); print("!! syntax error — rolled back:", sc.stderr[:160]); raise SystemExit(2)
run(["bash","-lc","systemctl --user restart vintos-server"])
ok = False
for _ in range(8):
    time.sleep(1.5)
    if run(["bash","-lc","systemctl --user is-active vintos-server"]).stdout.strip() == "active":
        ok = True; break
if not ok:
    shutil.copy2(bak, SRV); run(["bash","-lc","systemctl --user restart vintos-server"])
    print("!! server didn't come up — rolled back")
else:
    print("FIXED. /api/chat/full live copy now defines message. server active. backup:", bak.replace(HOME,'~'))
