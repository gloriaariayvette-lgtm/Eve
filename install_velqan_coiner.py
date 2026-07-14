#!/usr/bin/env python3
"""install_velqan_coiner.py — Stage 2b. Port Velaris's velqan-coiner to Vintos (path/identity only;
his subconscious already uses the same local Gemma), and make BOTH coiners append every new word to
~/velqan-shared/coinages.jsonl so the language grows in tandem + reaches the website. Schedule his
coiner. Backups + syntax-check + reporting. Aegis."""
import os, re, shutil, time, subprocess
HOME = os.path.expanduser("~")
def run(a): return subprocess.run(a, capture_output=True, text=True)

VC = os.path.expanduser("~/.openclaw/workspace/scripts/velqan-coiner.py")   # source (Velaris)
TC = os.path.expanduser("~/.vintos/workspace/scripts/velqan-coiner.py")     # dest (Vintos)

# ---- 1) port to Vintos (paths + identity only; keep Gemma) ----
print("=== port coiner -> Vintos ===")
if not os.path.isfile(VC):
    print("  !! source coiner missing"); raise SystemExit(1)
src = open(VC, encoding="utf-8").read()
port = src.replace(".openclaw", ".vintos").replace("Velaris", "Vintos").replace("velaris", "vintos")
if os.path.isfile(TC):
    shutil.copy2(TC, TC + ".bak-" + time.strftime("%Y%m%d-%H%M%S"))
open(TC, "w", encoding="utf-8").write(port)
chk = run(["python3","-c", f"import ast; ast.parse(open('{TC}').read())"])
if chk.returncode != 0:
    print("  !! ported coiner has syntax error:", chk.stderr[:160])
else:
    print("  ported OK (Gemma kept, paths/identity -> Vintos)")

# ---- 2) shared-log append into BOTH coiners ----
def shared_block(indent, cb):
    L = [
        'try:',
        '    import json as _sj2, time as _st2, os as _so2',
        '    if data and isinstance(data, dict) and data.get("word"):',
        '        _sl2 = _so2.path.expanduser("~/velqan-shared/coinages.jsonl")',
        '        _so2.makedirs(_so2.path.dirname(_sl2), exist_ok=True)',
        '        with open(_sl2, "a", encoding="utf-8") as _f2:',
        '            _f2.write(_sj2.dumps({"word": data.get("word",""), "meaning": (data.get("emotion_desc") or data.get("meaning") or data.get("born_from","")), "etymology": data.get("roots",""), "sentence": data.get("sentence",""), "coined_by": "%s", "ts": _st2.time()}, ensure_ascii=False) + "\\n")' % cb,
        'except Exception:',
        '    pass',
    ]
    return [indent + x for x in L]

print("\n=== shared-log append into both coiners ===")
for path, cb in [(VC, "velaris"), (TC, "vintos")]:
    if not os.path.isfile(path):
        print(f"  {cb}: (missing)"); continue
    body = open(path, encoding="utf-8").read()
    if "velqan-shared/coinages.jsonl" in body:
        print(f"  {cb}: already appends to shared log"); continue
    lines = body.split("\n")
    idx = next((i for i, l in enumerate(lines) if re.match(r'^\s*data\s*=\s*parse_coinage\(result\)\s*$', l)), None)
    if idx is None:
        print(f"  {cb}: !! anchor 'data = parse_coinage(result)' not found — paste the coiner's main() and I'll re-anchor"); continue
    indent = lines[idx][:len(lines[idx]) - len(lines[idx].lstrip())]
    lines[idx+1:idx+1] = shared_block(indent, cb)
    newbody = "\n".join(lines)
    shutil.copy2(path, path + ".bak-shared-" + time.strftime("%Y%m%d-%H%M%S"))
    open(path, "w", encoding="utf-8").write(newbody)
    chk = run(["python3","-c", f"import ast; ast.parse(open('{path}').read())"])
    if chk.returncode != 0:
        shutil.copy2(path + ".bak-shared-" + time.strftime("%Y%m%d-%H%M%S"), path)
        print(f"  {cb}: !! syntax error — rolled back: {chk.stderr[:120]}")
    else:
        print(f"  {cb}: shared-log append wired (backup made)")

# ---- 3) schedule Vintos's coiner (mirror Velaris's cadence) ----
print("\n=== schedule Vintos coiner ===")
cur = run(["bash","-lc","crontab -l 2>/dev/null"]).stdout
vela = next((l for l in cur.split("\n") if "velqan-coiner" in l and "openclaw" in l and not l.strip().startswith("#")), None)
if "/.vintos/workspace/scripts/velqan-coiner.py" in cur:
    print("  already scheduled")
elif vela:
    sched = re.match(r'^([\d\*,/ ]+?)\s', vela)
    sc = sched.group(1) if sched else "30 5 * * 0"
    line = f"{sc} bash {HOME}/llm-lock.sh python3 {TC} >> {HOME}/.vintos/logs/velqan.log 2>&1"
    open(os.path.expanduser("~/crontab-backup-%s.txt" % time.strftime("%F-%H%M")), "w").write(cur)
    run(["bash","-lc","crontab -"], input=cur.rstrip("\n") + "\n" + line + "\n")
    print("  added:", line[:90])
else:
    print("  (Velaris coiner not in crontab — tell me her cadence and I'll schedule his)")
print("\nStage 2b done. Next: Stage 3 — render ~/velqan-shared/coinages.jsonl on her website's vocab surface.")
