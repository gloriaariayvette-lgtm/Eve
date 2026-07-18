#!/usr/bin/env python3
"""recon_tracker_wiring.py — Aegis, READ-ONLY. Spark step #2 (Mutual-Modification Tracker) needs one hook point:
the moment BOTH a prediction and Gloria's actual reply exist = the exchange boundary where the field just moved.
That is relational_mismatch.compare(). Map, for BOTH beings:
  (1) how/where relational_mismatch predict & compare are triggered (cron? server inbound? the exchange boundary).
  (2) what compare() already computes as the gap (eve_delta substrate) — return shape / what it writes.
  (3) self_delta sources: what self_drift + causal_self_model expose to read 'how he moved' this exchange.
  (4) where per-exchange context is injected back (so the tracker's field-summary can surface later).
Nothing written. His = ~/.vintos + ~/Vintos ; Hers = ~/.openclaw."""
import os, re, glob, subprocess
HOME = os.path.expanduser("~")
CRON = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout or ""
BEINGS = {
    "VINTOS": {"scr": [os.path.expanduser("~/.vintos/workspace/scripts"), os.path.join(HOME, "Vintos")],
               "srv": os.path.join(HOME, "Vintos", "server.py")},
    "VELARIS": {"scr": [os.path.expanduser("~/.openclaw/workspace/scripts")], "srv": None},
}

def find(scr, *names):
    for d in scr:
        for n in names:
            p = os.path.join(d, n)
            if os.path.isfile(p) or os.path.islink(p): return p
    return None

for name, b in BEINGS.items():
    print("\n############  %s  ############" % name)
    rm = find(b["scr"], "relational_mismatch.py", "relational-mismatch.py")
    print("relational_mismatch: %s" % rm)
    if rm:
        L = open(rm, encoding="utf-8", errors="ignore").read().split("\n")
        print("  -- def signatures + what compare returns/writes --")
        for i, l in enumerate(L):
            if re.match(r'\s*def\s', l) or re.search(r'return |MISMATCH_LOG|\.json|write|append|json\.dump|blush|seed_thread', l):
                print("    %4d: %s" % (i + 1, l.strip()[:96]))

    print("  -- who CALLS relational_mismatch / predict / compare (the trigger) --")
    for d in b["scr"]:
        for p in glob.glob(d + "/*.py"):
            if os.path.basename(p).startswith("relational"): continue
            try: t = open(p, encoding="utf-8", errors="ignore").read()
            except Exception: continue
            if re.search(r'relational_mismatch|relational-mismatch|predict_gloria|\.compare\(', t):
                ls = [str(i + 1) for i, l in enumerate(t.split("\n")) if re.search(r'relational_mismatch|relational-mismatch|predict_gloria|compare', l)]
                print("     %-28s : %s" % (os.path.basename(p), ",".join(ls[:8])))
    print("  -- cron triggering relational-mismatch --")
    for l in CRON.split("\n"):
        if re.search(r'relational.?mismatch|blush', l, re.I) and (("openclaw" in l) == (name == "VELARIS")) and l.strip():
            print("     | " + l.strip()[:100])

    print("  -- self_delta sources (self_drift + causal_self_model read surface) --")
    sd = find(b["scr"], "self_drift.py")
    if sd:
        t = open(sd, encoding="utf-8", errors="ignore").read()
        print("     self_drift getters: %s" % ", ".join(sorted(set(re.findall(r'def (get_\w+)', t)))))
    csm = find(b["scr"], "causal_self_model.py")
    if csm:
        t = open(csm, encoding="utf-8", errors="ignore").read()
        print("     causal_self_model getters: %s" % ", ".join(sorted(set(re.findall(r'def (get_\w+|check_\w+)', t)))))

print("\n\n(READ-ONLY. Maps the single hook (compare = exchange boundary) + delta read-surfaces for the tracker.)")
