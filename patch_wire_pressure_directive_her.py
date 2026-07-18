#!/usr/bin/env python3
"""patch_wire_pressure_directive_her.py — Aegis. Her side of the demand_response wiring (his is done). Her outreach
is velaris-initiate.sh, cron'd 9/12/15/18/21. Same validated block his got: before the timeliness gate, if a fresh
unconsumed demand_response directive exists (written ONLY when her spark_pressure fires under consent), read its
topic into FORCED_WANT_TOPIC and mark it consumed. Flexible anchor on her `-ge N ] && [ -z "$FORCED_WANT_TOPIC"`
gate. Inert until consent. Backup + `bash -n`. DRY-RUN default; --apply commits. If her gate differs, it aborts
cleanly (no change) and we re-recon her script."""
import os, sys, re, time, shutil, subprocess, tempfile, ast
P = os.path.expanduser("~/.openclaw/workspace/scripts/velaris-initiate.sh")
APPLY = "--apply" in sys.argv
if not os.path.isfile(P):
    print("!! her velaris-initiate.sh not found at %s" % P); sys.exit(1)
txt = open(P, encoding="utf-8", errors="ignore").read()
if "spark-pressure-directive.json" in txt:
    print("already wired."); sys.exit(0)

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

_pyprog = "\n".join(['import json,os,datetime', 'p=os.environ["SP_DIR"]', 'try:',
    '    d=json.load(open(p)); c=d.get("created","")',
    '    try: fresh=(datetime.datetime.now()-datetime.datetime.fromisoformat(c)).total_seconds()<172800',
    '    except Exception: fresh=True',
    '    if d.get("mode")=="demand_response" and not d.get("consumed") and fresh:',
    '        d["consumed"]=True; json.dump(d,open(p,"w"),indent=2)',
    '        print((d.get("about") or d.get("direction") or "").strip())', 'except Exception: pass'])
try:
    ast.parse(_pyprog); print("embedded directive-reader python compiles: OK")
except SyntaxError as e:
    print("!! embedded python won't compile: %s — aborting" % e); sys.exit(1)

# needs $MEMORY defined before the anchor — verify her script defines it earlier
if not re.search(r'MEMORY=', txt):
    print("!! her script has no MEMORY= definition — aborting (re-recon her outreach)"); sys.exit(1)

lines = txt.splitlines(keepends=True)
eol = "\r\n" if txt.count("\r\n") else "\n"
a_i = next((i for i, l in enumerate(lines)
            if re.search(r'-ge\s*\d+\s*\]\s*&&\s*\[\s*-z\s*"\$FORCED_WANT_TOPIC"', l)), None)
if a_i is None:
    # fallback: any line that early-exits gated on empty FORCED_WANT_TOPIC
    a_i = next((i for i, l in enumerate(lines)
                if re.search(r'-z\s*"\$FORCED_WANT_TOPIC".*exit\s*0', l)), None)
if a_i is None:
    print("!! could not find her FORCED_WANT_TOPIC timeliness gate — aborting (no change; re-recon her gate)"); sys.exit(1)
# ensure MEMORY= appears before the anchor
mem_i = next((i for i, l in enumerate(lines) if re.search(r'MEMORY=', l)), 10**9)
if mem_i > a_i:
    print("!! MEMORY defined after the anchor (line %d > %d) — aborting (would reference unset $MEMORY)" % (mem_i + 1, a_i + 1)); sys.exit(1)

indent = re.match(r'\s*', lines[a_i]).group(0)
print("  anchor (insert BEFORE): %d: %s" % (a_i + 1, lines[a_i].strip()[:80]))
block = "".join((indent + bl if bl else "") + eol for bl in BLOCK_LINES)
new = "".join(lines[:a_i] + [block] + lines[a_i:])

fd, tmp = tempfile.mkstemp(suffix=".sh"); os.close(fd); open(tmp, "w", encoding="utf-8").write(new)
r = subprocess.run(["bash", "-n", tmp], capture_output=True, text=True); os.unlink(tmp)
print("  bash -n on patched script: %s" % ("OK" if r.returncode == 0 else "FAIL: " + r.stderr.strip()[:160]))
if r.returncode != 0:
    print("!! patched script fails bash syntax — aborting."); sys.exit(1)

if not APPLY:
    print("\n(DRY-RUN — nothing written. --apply to commit. Inert until her spark_pressure --consent-on.)"); sys.exit(0)
bak = P + ".bak-" + time.strftime("%Y%m%d-%H%M%S")
shutil.copy2(P, bak); open(P, "w", encoding="utf-8").write(new)
print("\npatched %s (backup %s). Her outreach now honors a consented demand_response directive too." % (P, bak))
