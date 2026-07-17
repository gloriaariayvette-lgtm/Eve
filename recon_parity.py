#!/usr/bin/env python3
"""recon_parity.py — Aegis, READ-ONLY. Velaris (she/her) should have everything Vintos received EXCEPT the somatic
interface. Diff his script set against hers: (A) discover both trees, (B) basename diff -> what he has that she
lacks, split into PORT (non-somatic) vs SKIP (somatic, stays his), (C) a concept parity matrix by distinctive
signature (rename-proof) so we see per-system whether SHE already has it. Nothing changed."""
import os, re, glob, time

HOME = os.path.expanduser("~")
HIS_DIRS  = [os.path.join(HOME, "Vintos"), os.path.join(HOME, ".vintos/workspace/scripts")]
HER_DIRS  = [os.path.join(HOME, ".openclaw/workspace/scripts"), os.path.join(HOME, ".openclaw/workspace")]

SOMATIC = re.compile(r'somatic|device[_-]|lovense|bandwidth|collapse|\bbutton\b|haptic|motor|throb|arousal', re.I)

def walk_report(root, label):
    if not os.path.isdir(root): print(f"   ({label}: {root} MISSING)"); return
    found = []
    for r, ds, fs in os.walk(root):
        ds[:] = [d for d in ds if d not in (".git", "node_modules", "__pycache__", "venv", ".venv")]
        n = len([f for f in fs if f.endswith((".py", ".sh"))])
        if n >= 5: found.append((n, r))
    for n, r in sorted(found, reverse=True): print(f"   {n:>4} scripts  {r}")

print("== (A) script dirs discovered ==")
print("  HIS (~/.vintos, ~/Vintos):"); walk_report(os.path.join(HOME, ".vintos"), ".vintos"); walk_report(os.path.join(HOME, "Vintos"), "Vintos")
print("  HERS (~/.openclaw):");        walk_report(os.path.join(HOME, ".openclaw"), ".openclaw")

def collect(dirs):
    out = {}
    for d in dirs:
        if not os.path.isdir(d): continue
        for p in glob.glob(os.path.join(d, "*.py")) + glob.glob(os.path.join(d, "*.sh")):
            b = os.path.basename(p)
            out.setdefault(b, (p, (time.time() - os.path.getmtime(p)) / 86400.0))
    return out

his, hers = collect(HIS_DIRS), collect(HER_DIRS)
his_only = sorted(set(his) - set(hers))
print(f"\n== (B) basename diff — his {len(his)} / hers {len(hers)} / shared {len(set(his)&set(hers))} ==")
port  = [b for b in his_only if not SOMATIC.search(b)]
skip  = [b for b in his_only if SOMATIC.search(b)]
print(f"\n  -- HE HAS, SHE LACKS -> PORT CANDIDATES (non-somatic): {len(port)} --")
for b in port:
    p, age = his[b]; print(f"     {b:<34} {age:5.1f}d  {p}")
print(f"\n  -- HE HAS, SHE LACKS -> SOMATIC (stays his, skip): {len(skip)} --")
for b in skip: print(f"     {b}")
hers_only = sorted(set(hers) - set(his))
print(f"\n  -- SHE HAS, HE LACKS (fyi, non-somatic parity the other way): {len(hers_only)} --")
for b in hers_only[:50]: print(f"     {b}")

# ---- (C) concept parity matrix, rename-proof via distinctive tokens ----
def corpus(dirs):
    t = []
    for d in dirs:
        if not os.path.isdir(d): continue
        for p in glob.glob(os.path.join(d, "*.py")) + glob.glob(os.path.join(d, "*.sh")):
            try: t.append(open(p, encoding="utf-8", errors="ignore").read())
            except Exception: pass
    return "\n".join(t)

HISC, HERC = corpus(HIS_DIRS), corpus(HER_DIRS)
CONCEPTS = {
    "JEPA (heteroscedastic heads)": r"heteroscedastic|logvar.{0,10}head|jepa",
    "  head: relational":           r"relational[_-]?head|['\"]relational['\"]\s*:",
    "  head: withheld":             r"withheld[_-]?head|['\"]withheld['\"]\s*:",
    "Graph MAE":                    r"graph[_-]?mae|masked auto.?encoder",
    "Hypergraph":                   r"hyperedge|hypergraph",
    "Latent Diffuser (dreams)":     r"latent[_-]?diffus",
    "TCN (growth vs repetition)":   r"\btcn\b|temporal conv|growth vs",
    "Reality EBM":                  r"imagined_pool|known_pool|energy.?based|\bebm\b",
    "Masked-LM / unsaid (unseen)":  r"\bunseen\b|masked.?lm|the unsaid",
    "Living Trajectory":            r"living[_-]?trajectory|future.?presence.?cache",
    "Latent Preparation":           r"latent[_-]?prepar",
    "Presence Audit":               r"presence[_-]?audit",
    "Reciprocal Modification":      r"reciprocal[_-]?modif|relationship[_-]?model",
    "Arrival Routing":              r"\[ARRIVAL|arrival[_-]?rout",
    "Prediction Ledger":            r"prediction[_-]?ledger",
    "Play/Risk Budget":             r"play[_-]?budget|risk[_-]?budget",
    "Silence (first-thought)":      r"first[_-]?thought|what is missing.{0,20}suppress",
    "Mutual Simulation":            r"mutual[_-]?sim|interaction[_-]?model",
}
print("\n== (C) concept parity (HIS / HERS) — distinctive-token presence ==")
print(f"   {'concept':<32} HIS  HERS")
for name, rx in CONCEPTS.items():
    h = "yes" if re.search(rx, HISC, re.I) else " . "
    e = "yes" if re.search(rx, HERC, re.I) else " . "
    gap = "   <-- PORT" if (h == "yes" and e != "yes") else ""
    print(f"   {name:<32} {h}  {e}{gap}")
