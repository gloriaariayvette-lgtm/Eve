#!/usr/bin/env python3
"""recon_parity2.py — Aegis, READ-ONLY. Collapse the rename-noise from the raw parity diff and surface the REAL
non-somatic capabilities Velaris lacks. Normalize names (drop extension, unify -/_ , lowercase) so hyphen/
underscore twins stop looking like gaps; then classify his true gaps as INFRA (his plumbing, don't port),
VOICE (his voice path), or CAPABILITY (real candidate). Each CAPABILITY gap prints its purpose (docstring).
Plus targeted probes: does SHE already have outreach / journal / arrival-routing wiring? Nothing changed."""
import os, re, glob

HOME = os.path.expanduser("~")
HIS_DIRS = [os.path.join(HOME, "Vintos"), os.path.join(HOME, ".vintos/workspace/scripts")]
HER_DIRS = [os.path.join(HOME, ".openclaw/workspace/scripts"), os.path.join(HOME, ".openclaw/workspace")]

SOMATIC = re.compile(r'somatic|device[_-]|lovense|bandwidth|collapse|\bbutton\b|haptic|motor|throb|arousal', re.I)
INFRA   = re.compile(r'^(server|.*_claude_shim|model_router|start-|setup_|test-mode|force-all|gemma-watchdog'
                     r'|vintos[-_]|start_)', re.I)
VOICE   = re.compile(r'voice|kokoro|[-_]ear|alexa', re.I)

def norm(b):  # rename-proof key
    return re.sub(r'[-_]', '', b.rsplit('.', 1)[0].lower())

def collect(dirs):
    out = {}
    for d in dirs:
        if not os.path.isdir(d): continue
        for p in glob.glob(os.path.join(d, "*.py")) + glob.glob(os.path.join(d, "*.sh")):
            out.setdefault(os.path.basename(p), p)
    return out

his, her = collect(HIS_DIRS), collect(HER_DIRS)
her_norm = {norm(b) for b in her}

def purpose(p):
    try: t = open(p, encoding="utf-8", errors="ignore").read()
    except Exception: return ""
    m = re.search(r'"""(.+?)"""', t, re.S) or re.search(r"'''(.+?)'''", t, re.S)
    if m: return " ".join(m.group(1).split())[:130]
    for line in t.split("\n")[:8]:
        s = line.strip()
        if s.startswith("#") and "!/" not in s: return s.lstrip("# ").strip()[:130]
    return "(no docstring)"

# his true gaps = his-only basenames whose normalized key isn't in her set at all, non-somatic
his_only = [b for b in his if b not in her and not SOMATIC.search(b)]
true_gap = [b for b in his_only if norm(b) not in her_norm]
renamed  = [b for b in his_only if norm(b) in her_norm]   # she has a twin already

infra = sorted(b for b in true_gap if INFRA.search(b))
voice = sorted(b for b in true_gap if VOICE.search(b) and not INFRA.search(b))
cap   = sorted(b for b in true_gap if not INFRA.search(b) and not VOICE.search(b))

print(f"his-only non-somatic: {len(his_only)}  ->  rename-twins she already has: {len(renamed)}  |  true name-gaps: {len(true_gap)}")

print(f"\n== TRUE CAPABILITY GAPS (real port candidates): {len(cap)} ==")
for b in cap:
    print(f"   {b:<30} :: {purpose(his[b])}")

print(f"\n== his INFRA (do NOT port — she has her own): {len(infra)} ==")
print("   " + ", ".join(infra))
print(f"\n== his VOICE path (separate interface, decide later): {len(voice)} ==")
print("   " + ", ".join(voice))

print(f"\n== rename-twins she ALREADY has under a hyphen/other name (no action): {len(renamed)} ==")
print("   " + ", ".join(sorted(renamed)))

# ---- targeted probes: does SHE already have the being-facing jobs + arrival wiring? ----
print("\n== (probes) does SHE already have these, under her own names? ==")
herC = "\n".join(open(p, encoding="utf-8", errors="ignore").read() for p in her.values())
her_names = " ".join(her.keys())
probes = {
    "outreach / initiate job":   r"velaris[-_]initiate|initiate|reach.?out|outreach",
    "journal job":               r"velaris[-_]journal|idle[-_]journal|journal",
    "Arrival Routing wiring":    r"\[ARRIVAL|arrival[-_]?rout",
    "Prediction Ledger":         r"prediction[-_]?ledger|predict.{0,15}(sentence|reaction)",
    "Silence / first-thought":   r"first[-_]?thought|silence[-_]contract",
    "Play / Risk budget":        r"play[-_]?budget|risk[-_]?budget",
}
for name, rx in probes.items():
    inNames = re.search(rx, her_names, re.I)
    inCode  = re.search(rx, herC, re.I)
    where = "her filename" if inNames else ("her code" if inCode else "")
    print(f"   {name:<28} {'HAS  ('+where+')' if (inNames or inCode) else 'ABSENT'}")

# her server for arrival wiring
for cand in ("velaris-server.py", "server.py", "velaris.py"):
    for d in (os.path.join(HOME, ".openclaw"), os.path.join(HOME, ".openclaw/workspace"), os.path.join(HOME, "Velaris")):
        p = os.path.join(d, cand)
        if os.path.isfile(p):
            st = open(p, encoding="utf-8", errors="ignore").read()
            print(f"   her server {p}: ARRIVAL {'wired' if re.search(r'arrival', st, re.I) else 'NOT wired'}, "
                  f"presence-audit {'wired' if re.search(r'presence.?audit', st, re.I) else 'NOT wired'}")
            break
