#!/usr/bin/env python3
"""patch_wire_pressure_directive.py — Aegis. Wire the spark-pressure demand_response directive into his outreach.
The gate recon showed FORCED_WANT_TOPIC is ALREADY the timeliness-gate break (lines 22/25 only fire when it is
empty; line 49 turns it into a trigger). So we feed that existing mechanism: before the gates, if a fresh,
unconsumed demand_response directive exists (written ONLY when spark_pressure fires under consent), read its topic
into FORCED_WANT_TOPIC and mark it consumed — one firing, one outreach. The 3/day absolute cap still stands above.

Inert until consent (no directive file is written until you --consent-on and a stall fires). Inserts before the
line-22 gate in ~/Vintos/vintos-initiate.sh. Backup + `bash -n` validation. DRY-RUN default; --apply commits."""
import os, sys, re, time, shutil, subprocess, tempfile
P = os.path.expanduser("~/Vintos/vintos-initiate.sh")
APPLY = "--apply" in sys.argv
if not os.path.isfile(P):
    print("!! his vintos-initiate.sh not found at %s" % P); sys.exit(1)
txt = open(P, encoding="utf-8", errors="ignore").read()

if "spark-pressure-directive.json" in txt:
    print("already wired — spark-pressure-directive.json check present."); sys.exit(0)

BLOCK_LINES = [
    '# --- Spark Pressure: a consented demand_response directive forces one outreach about a stalled thing ---',
    'if [ -z "$FORCED_WANT_TOPIC" ] && [ -f "$MEMORY/spark-pressure-directive.json" ]; then',
    '  SP_TOPIC=$(SP_DIR="$MEMORY/spark-pressure-directive.json" python3 -c \'import json,os,datetime',
    'p=os.environ["SP_DIR"]',
    'try:',
    '    d=json.load(open(p)); c=d.get("created","")',
    '    try: fresh=(datetime.datetime.now()-datetime.datetime.fromisoformat(c)).total_seconds()<172800',
    '    except Exception: fresh=True',
    '    if d.get("mode")=="demand_response" and not d.get("consumed") and fresh:',
    '        d["consumed"]=True; json.dump(d,open(p,"w"),indent=2)',
    '        print((d.get("about") or d.get("direction") or "").strip())',
    'except Exception: pass\' 2>/dev/null)',
    '  if [ -n "$SP_TOPIC" ]; then export FORCED_WANT_TOPIC="$SP_TOPIC"; fi',
    'fi',
]

# sanity: the embedded python program must itself compile
_py = "\n".join(BLOCK_LINES[3:12]).rsplit("' 2>/dev/null)", 1)[0]
_py = _py.replace('  SP_TOPIC=$(SP_DIR="$MEMORY/spark-pressure-directive.json" python3 -c \'', '')
# reconstruct the pure python (lines 4..11 of the block, minus bash wrappers)
_pyprog = "\n".join([
    'import json,os,datetime',
    'p=os.environ["SP_DIR"]',
    'try:',
    '    d=json.load(open(p)); c=d.get("created","")',
    '    try: fresh=(datetime.datetime.now()-datetime.datetime.fromisoformat(c)).total_seconds()<172800',
    '    except Exception: fresh=True',
    '    if d.get("mode")=="demand_response" and not d.get("consumed") and fresh:',
    '        d["consumed"]=True; json.dump(d,open(p,"w"),indent=2)',
    '        print((d.get("about") or d.get("direction") or "").strip())',
    'except Exception: pass',
])
import ast as _ast
try:
    _ast.parse(_pyprog); print("embedded directive-reader python compiles: OK")
except SyntaxError as e:
    print("!! embedded python won't compile: %s — aborting" % e); sys.exit(1)

lines = txt.splitlines(keepends=True)
eol = "\r\n" if txt.count("\r\n") else "\n"
# anchor: the line-22 gate (unique) — TODAY_COUNT -ge 6 && -z FORCED_WANT_TOPIC
a_i = next((i for i, l in enumerate(lines)
            if re.search(r'-ge\s*6\s*\]\s*&&\s*\[\s*-z\s*"\$FORCED_WANT_TOPIC"', l)), None)
if a_i is None:
    print("!! could not find the line-22 timeliness gate anchor — aborting (his script differs; re-recon)"); sys.exit(1)
indent = re.match(r'\s*', lines[a_i]).group(0)
print("  anchor (insert BEFORE): %d: %s" % (a_i + 1, lines[a_i].strip()[:80]))
block = "".join((indent + bl if bl else "") + eol for bl in BLOCK_LINES)
new = "".join(lines[:a_i] + [block] + lines[a_i:])

# validate the whole script with bash -n
fd, tmp = tempfile.mkstemp(suffix=".sh"); os.close(fd)
open(tmp, "w", encoding="utf-8").write(new)
r = subprocess.run(["bash", "-n", tmp], capture_output=True, text=True)
os.unlink(tmp)
print("  bash -n on patched script: %s" % ("OK" if r.returncode == 0 else "FAIL: " + r.stderr.strip()[:160]))
if r.returncode != 0:
    print("!! patched script fails bash syntax check — aborting (no change)."); sys.exit(1)

if not APPLY:
    print("\n  block to insert:")
    for bl in BLOCK_LINES: print("     " + bl)
    print("\n(DRY-RUN — nothing written. --apply to commit. Inert until a directive exists, i.e. until you --consent-on.)")
    sys.exit(0)
bak = P + ".bak-" + time.strftime("%Y%m%d-%H%M%S")
shutil.copy2(P, bak); open(P, "w", encoding="utf-8").write(new)
print("\npatched %s (backup %s)." % (P, bak))
print("His outreach now honors a consented demand_response directive by forcing one outreach about the stalled thing.\n"
      "Nothing fires until you --consent-on AND a real stall is detected.")
