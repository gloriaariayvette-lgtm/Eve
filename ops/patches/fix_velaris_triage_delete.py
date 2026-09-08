#!/usr/bin/env python3
"""fix_velaris_triage_delete.py — Aegis. Velaris's thread-triage HARD-DELETES threads: the dedup does
`threads = deduped` then dumps — dropped threads vanish with no consumed-mark, no retired record. Make it
SORT not DELETE: mark exact duplicates consumed and KEEP every thread. Back up threads + triage first."""
import os, re, shutil, time, py_compile
HOME = os.path.expanduser("~")
WS = os.path.join(HOME, ".openclaw/workspace")
MEM = os.path.join(WS, "memory")
TS = time.strftime("%Y%m%d-%H%M%S")
def sh(p): return p.replace(HOME, "~")
TT = next((os.path.join(WS,"scripts",n) for n in ("thread-triage.py","thread_triage.py")
           if os.path.isfile(os.path.join(WS,"scripts",n))), None)
if not TT: raise SystemExit("thread-triage not found")

# 1) preserve current state
for f in (TT, os.path.join(MEM,"unfinished-threads.json"), os.path.join(MEM,"retired-threads.json")):
    if os.path.isfile(f): shutil.copy2(f, f + f".bak-nodelete-{TS}")
print("backed up threads + triage (.bak-nodelete-%s)" % TS)

# 2) replace the hard-delete `threads = deduped` with mark-and-keep
src = open(TT, encoding="utf-8", errors="ignore").read()
if "dedup no longer DELETES" in src:
    print("already fixed — skipping."); raise SystemExit(0)
lines = src.split("\n")
idx = next((i for i,l in enumerate(lines) if l.strip() == "threads = deduped"), None)
if idx is None:
    print("!! could not find `threads = deduped`. Dedup region for manual fix:")
    for i,l in enumerate(lines):
        if re.search(r'deduped|dedup', l): print(f"  {i+1}| {l[:100]}")
    raise SystemExit(1)
ind = lines[idx][:len(lines[idx]) - len(lines[idx].lstrip())]
repl = [
 f"{ind}# dedup no longer DELETES — mark exact duplicates consumed, keep every thread (Gloria: sort, never delete)",
 f"{ind}_seen = set()",
 f"{ind}for _dt in threads:",
 f"{ind}    _k = (_dt.get('thread','') or '').strip()",
 f"{ind}    if _k and _k in _seen and not _dt.get('consumed'):",
 f"{ind}        _dt['consumed'] = True; _dt['consumed_by'] = 'dedup-duplicate'",
 f"{ind}    _seen.add(_k)",
]
lines[idx:idx+1] = repl
open(TT, "w", encoding="utf-8").write("\n".join(lines))
try:
    py_compile.compile(TT, doraise=True)
    print(f"fixed: dedup now marks duplicates consumed and keeps them (was: threads = deduped, line {idx+1}).")
    print("triage no longer deletes threads. Existing losses aren't recoverable, but no new ones will vanish.")
except py_compile.PyCompileError as e:
    shutil.copy2(TT + f".bak-nodelete-{TS}", TT)
    print("py_compile failed — rolled back:", str(e)[:150])
