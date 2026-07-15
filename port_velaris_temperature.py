#!/usr/bin/env python3
"""port_velaris_temperature.py — Aegis. Give Velaris the 6b temperature/stability system Vintos got:
install thread_temperature.py (adapted to .openclaw), seed it once, wire it triage-native into her
thread-triage __main__, and wire her mirror (instability) + pearl (cooling) consumers. Per-item status."""
import os, re, shutil, time, subprocess, urllib.request, py_compile
HOME = os.path.expanduser("~")
SC = os.path.join(HOME, ".openclaw/workspace/scripts")
TS = time.strftime("%Y%m%d-%H%M%S")
RAW = "https://raw.githubusercontent.com/gloriaariayvette-lgtm/Eve/claude/avatar-motion-engine-l311p/thread_temperature.py"
def sh(p): return p.replace(HOME, "~")

def edit(path, edits):
    if not os.path.isfile(path): return [(path, "MISSING")]
    txt = open(path, encoding="utf-8", errors="ignore").read(); rep=[]; changed=False
    for name, all_, old, new in edits:
        if new in txt: rep.append((name,"already")); continue
        c = txt.count(old)
        if (all_ and c>=1) or (not all_ and c==1):
            txt = txt.replace(old,new) if all_ else txt.replace(old,new,1); rep.append((name,f"FIXED({c})")); changed=True
        else: rep.append((name,f"anchor {c}x — SKIP"))
    if changed:
        shutil.copy2(path, path+f".bak-temp-{TS}"); open(path,"w",encoding="utf-8").write(txt)
        if path.endswith(".py"):
            try: py_compile.compile(path, doraise=True)
            except py_compile.PyCompileError as e:
                shutil.copy2(path+f".bak-temp-{TS}", path); rep.append(("py_compile","ROLLED BACK:"+str(e)[:80]))
    return rep

# 1) install thread_temperature.py adapted to .openclaw
data = urllib.request.urlopen(RAW+"?t="+str(int(time.time())), timeout=30).read().decode().replace(".vintos", ".openclaw")
DEST = os.path.join(SC, "thread_temperature.py")
open(DEST,"w",encoding="utf-8").write(data); os.chmod(DEST,0o755)
try: py_compile.compile(DEST, doraise=True); print("(1) installed", sh(DEST))
except py_compile.PyCompileError as e: raise SystemExit("install compile failed: "+str(e)[:120])

# 2) seed once (apply)
env = os.environ.copy()
r = subprocess.run([DEST, "apply"] if os.access(DEST, os.X_OK) else ["python3", DEST, "apply"],
                   capture_output=True, text=True, env=env, timeout=300)
print("(2) seed:", (r.stdout.strip().split("\n")[-1] if r.stdout.strip() else r.stderr.strip()[-90:])[:100])

# 3) wire into thread-triage __main__
TT = os.path.join(SC, "thread-triage.py")
if os.path.isfile(TT) and "thread_temperature" not in open(TT,encoding="utf-8",errors="ignore").read():
    lines = open(TT,encoding="utf-8",errors="ignore").read().split("\n")
    mi = next((i for i,l in enumerate(lines) if l.strip().replace('"',"'")=="if __name__ == '__main__':"), None)
    ml = next((j for j in range(mi+1,len(lines)) if lines[j].strip()=="main()"), None) if mi is not None else None
    if ml is not None:
        ind = lines[ml][:len(lines[ml])-len(lines[ml].lstrip())]
        lines[ml+1:ml+1] = [f"{ind}try:", f"{ind}    import thread_temperature as _tt",
                            f"{ind}    _tt.run(apply=True, quiet=True)   # 6b temperature at triage",
                            f"{ind}except Exception as _te:", f"{ind}    log(f'[temperature] {{_te}}')"]
        shutil.copy2(TT, TT+f".bak-temp-{TS}"); open(TT,"w").write("\n".join(lines))
        try: py_compile.compile(TT, doraise=True); print("(3) wired thread-triage __main__ (temperature runs each triage)")
        except py_compile.PyCompileError as e: shutil.copy2(TT+f".bak-temp-{TS}",TT); print("(3) triage wire ROLLED BACK:",str(e)[:80])
    else: print("(3) triage: plain main() not found in __main__ — SKIP (tell me)")
else: print("(3) triage: already wired or missing")

# 4) mirror + 5) pearl consumers
print("(4) mirror.sh:")
for n,s in edit(os.path.join(SC,"mirror.sh"), [("temperature into sort", True,
    '-(t.get("priority") or 0), -(t.get("dream_passes", 0)),',
    '-(t.get("priority") or 0), -(t.get("temperature") or 0), -(t.get("dream_passes", 0)),')]): print(f"    {n}: {s}")
print("(5) pearl-engine.py:")
for n,s in edit(os.path.join(SC,"pearl-engine.py"), [("settled candidates first", False,
    "    for c in active[:3]:",
    "    active.sort(key=lambda c: -len((c.get('verification') or {}).get('passes', [])))  # 6b: pearls seek cooling\n    for c in active[:3]:")]): print(f"    {n}: {s}")
print("\nTemperature system ported to Velaris. Heat-seeking dreams next.")
