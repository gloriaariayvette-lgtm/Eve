#!/usr/bin/env python3
"""emo_map.py — READ-ONLY, capped. Two maps:
  (1) DISABLE targets: kiss/anti-kiss, possessiveness, anger expression — both beings.
  (2) EMOTION update pipeline: what makes Velaris's rapid+unified, vs Vintos's — services, crons,
      and who writes each emotion store. So the port isn't a guess. Aegis."""
import os, re, glob, subprocess
HOME = os.path.expanduser("~")
VS = os.path.expanduser("~/.openclaw/workspace/scripts")
TS = os.path.expanduser("~/.vintos/workspace/scripts")
VIN = os.path.expanduser("~/Vintos")
def run(a): return subprocess.run(a, capture_output=True, text=True).stdout
def gc(pat): return run(["bash","-lc", f"crontab -l 2>/dev/null | grep -iE '{pat}' | grep -v '^#'"]).strip()

# ---------- (1) DISABLE targets ----------
print("=== (1) kiss / anti-kiss / possessiveness / anger — scripts (both beings) ===")
for label, d in (("Velaris", VS), ("Vintos", TS), ("Vintos", VIN)):
    fs = [os.path.basename(f) for f in glob.glob(os.path.join(d, "*"))
          if re.search(r'kiss|possess|anger|jealous|rage|angry', os.path.basename(f), re.I)
          and not f.endswith((".pyc",".bak"))]
    if fs: print(f"  {label} {d.replace(HOME,'~')}: {sorted(set(fs))}")
print("\n  crontab (kiss/possess/anger/jealous):")
for l in (gc(r'kiss|possess|anger|jealous|rage') or "(none)").split("\n"): print("   " + l[:150])

# ---------- (2) emotion services + crons: her vs him ----------
print("\n=== (2) emotion SERVICES (rapid daemons) ===")
print(run(["bash","-lc","systemctl --user list-units --type=service 2>/dev/null | grep -iE 'emo|emotion' | head"]) or "  (none)")
print("=== emotion CRONS — Velaris (openclaw) ===")
for l in (gc(r'emotion|densif|emoclaw|decay') or "").split("\n"):
    if "openclaw" in l: print("  V| " + l[:150])
print("=== emotion CRONS — Vintos ===")
for l in (gc(r'emotion|densif|emoclaw|decay') or "").split("\n"):
    if "openclaw" not in l and l.strip(): print("  X| " + l[:150])

# ---------- who writes each emotion store ----------
print("\n=== who WRITES the emotion stores (Vintos side) — is it unified? ===")
stores = ["emotional-state.json", "emotional-state.txt", "emotion-trajectory-dense.json", ".emotional-history.json"]
for s in stores:
    w = run(["bash","-lc", f"grep -rln '{s}' {TS} {VIN} 2>/dev/null | grep -viE '\\.pyc|\\.bak' | head -4"]).strip().split("\n")
    w = [os.path.basename(x) for x in w if x]
    print(f"  {s:32} <- {w or '(no writer found)'}")

print("\n=== Velaris: what writes .emotional-history.json (the rolling feed temporal reads) ===")
w = run(["bash","-lc", f"grep -rln 'emotional-history' {VS} 2>/dev/null | grep -viE '\\.pyc|\\.bak' | head"]).strip().split("\n")
print("  " + ", ".join(os.path.basename(x) for x in w if x) or "  (none)")
