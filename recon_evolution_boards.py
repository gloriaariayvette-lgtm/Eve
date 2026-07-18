#!/usr/bin/env python3
"""recon_evolution_boards.py — Aegis, READ-ONLY. For BOTH beings: (1) EVOLUTION — is want-reconciliation/grok_evolve
present + scheduled, is it actually producing evolved wants (source=evolution in fulfilled/current), and the
similarity_gate thresholds that gate re-seeds. (2) DISCUSSION BOARDS — where /api/wants/.../discussion is served,
which port each wants-router posts to (his vs her server), and what CONTEXT a discussion opening/reply is given.
Nothing changed. His = ~/Vintos + ~/.vintos ; Hers = ~/.openclaw."""
import os, re, json, glob, subprocess
HOME = os.path.expanduser("~")
BEINGS = {
    "VINTOS": {"scripts": [os.path.join(HOME, "Vintos"), os.path.join(HOME, ".vintos/workspace/scripts")],
               "mem": os.path.expanduser("~/.vintos/workspace/memory"), "server": os.path.join(HOME, "Vintos", "server.py")},
    "VELARIS": {"scripts": [os.path.join(HOME, ".openclaw/workspace/scripts")],
                "mem": os.path.expanduser("~/.openclaw/workspace/memory"), "server": None},
}
cron = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout or ""

def find(dirs, name):
    for d in dirs:
        p = os.path.join(d, name)
        if os.path.isfile(p) or os.path.islink(p): return p
    return None

def count_source(memdir, fname, src_val):
    p = os.path.join(memdir, fname)
    try:
        d = json.load(open(p)); items = d.get("fulfilled", d) if isinstance(d, dict) else d
        return sum(1 for w in items if isinstance(w, dict) and src_val in str(w.get("source", "")))
    except Exception: return -1

print("############  (1) EVOLUTION  ############")
for name, b in BEINGS.items():
    print("\n===== %s =====" % name)
    wr = find(b["scripts"], "want-reconciliation.py") or find(b["scripts"], "want_reconciliation.py")
    print("  want-reconciliation: %s" % (wr or "NOT FOUND"))
    if wr:
        t = open(wr, encoding="utf-8", errors="ignore").read()
        for i, l in enumerate(t.split("\n")):
            if re.search(r'def grok_evolve|def main|not w\.get\(.fulfilled|for w in fulfilled|express_want\(nxt|EVOLVED|MAX_EVOL', l):
                print("    %d: %s" % (i + 1, l.strip()[:92]))
    print("  cron for reconciliation/evolution:")
    for l in cron.split("\n"):
        if re.search(r'reconcil', l, re.I) and (("openclaw" in l) == (name == "VELARIS")) and l.strip() and not l.strip().startswith("#"):
            print("    | " + l.strip()[:104])
    print("  evolved wants produced: fulfilled(source~evolution)=%d  current(source~evolution)=%d" %
          (count_source(b["mem"], "fulfilled-wants.json", "evolution"), count_source(b["mem"], "current-wants.json", "evolution")))
    sg = find(b["scripts"], "similarity_gate.py") or find(b["scripts"], "similarity-gate.py")
    if sg:
        t = open(sg, encoding="utf-8", errors="ignore").read()
        thr = [l.strip() for l in t.split("\n") if re.search(r'THRESHOLD\s*=', l)]
        print("  similarity_gate thresholds: %s" % "; ".join(thr[:6]))

print("\n\n############  (2) DISCUSSION BOARDS  ############")
for name, b in BEINGS.items():
    print("\n===== %s =====" % name)
    wr = find(b["scripts"], "wants-router.py") or find(b["scripts"], "wants_router.py")
    if wr:
        t = open(wr, encoding="utf-8", errors="ignore").read()
        ports = sorted(set(re.findall(r'localhost:(\d+)/api/wants|127\.0\.0\.1:(\d+)/api/wants', t)))
        urls = sorted(set(re.findall(r'http://[^"\']*?/api/wants/[^"\']*discussion', t)))
        print("  wants-router: %s" % wr)
        print("    posts discussion to: %s" % (urls[:2] or "none found"))
        # what context is injected into the opening/reply
        ctx = [l.strip()[:90] for l in t.split("\n") if re.search(r'soul|gloria_model|value_map|self_model|recent_exchang|step_history|reasoning|CRITICAL FOR THIS', l, re.I)]
        print("    discussion context vars seen: %d (sample):" % len(ctx))
        for c in ctx[:8]: print("      - " + c)
    # who serves /api/wants/.../discussion
    srv = b["server"]
    if not srv:
        for cand in glob.glob(os.path.join(HOME, ".openclaw") + "/**/*.py", recursive=True):
            if "server" in os.path.basename(cand).lower() and "discussion" in open(cand, encoding="utf-8", errors="ignore").read():
                srv = cand; break
    if srv and os.path.isfile(srv):
        S = open(srv, encoding="utf-8", errors="ignore").read()
        eps = [l.strip()[:80] for l in S.split("\n") if "/api/wants" in l and "discussion" in l]
        print("  discussion endpoint served in %s: %d routes" % (os.path.basename(srv), len(eps)))
        for e in eps[:4]: print("      " + e)
    else:
        print("  discussion server: NOT located for %s" % name)
