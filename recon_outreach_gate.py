#!/usr/bin/env python3
"""recon_outreach_gate.py — Aegis, READ-ONLY, FAST (specific files). To wire the spark-pressure demand_response
directive into outreach, find the TIMELINESS GATE — where the outreach decides 'not yet / too soon / stay quiet' —
so a fresh directive can force it to proceed once. Look in vintos-initiate.sh and any gate python it calls, plus
her outreach. Show the gate decision points + how the script exits-early when it decides not to reach out.
Nothing written."""
import os, re
VIN = os.path.expanduser("~/Vintos")
HIS = os.path.expanduser("~/.vintos/workspace/scripts")

GATE = re.compile(r'timeli|too soon|not yet|cooldown|last.?initiat|last.?outreach|hours? since|elapsed|'
                  r'should_initiate|gate|quiet|skip|exit 0|suppress|threshold|min.?gap|throttle', re.I)

def scan(path, tag):
    if not (os.path.isfile(path) or os.path.islink(path)):
        print("  %s: (not found)" % tag); return
    L = open(path, encoding="utf-8", errors="ignore").read().split("\n")
    print("\n===== %s (%s, %d lines) =====" % (tag, path, len(L)))
    for i, l in enumerate(L):
        if GATE.search(l):
            print("  %4d: %s" % (i + 1, l.strip()[:110]))

# his outreach entry + any gate helper it calls
scan(os.path.join(VIN, "vintos-initiate.sh"), "vintos-initiate.sh")
# find python gate helpers invoked by the initiate script
init = os.path.join(VIN, "vintos-initiate.sh")
called = set()
if os.path.isfile(init):
    t = open(init, encoding="utf-8", errors="ignore").read()
    for m in re.finditer(r'([\w./-]+\.py)', t):
        called.add(os.path.basename(m.group(1)))
    print("\n  python files referenced by vintos-initiate.sh: %s" % sorted(called))
    # show the early-exit / gate structure of the shell script itself
    print("  -- shell gate/exit structure --")
    for i, l in enumerate(t.split("\n")):
        if re.search(r'exit|if \[|then|initiate|WANT|OUTREACH|proceed|quiet|skip', l) and len(l.strip()) < 120:
            print("    %4d: %s" % (i + 1, l.strip()[:100]))
        if i > 260: break

# common gate-helper names
for name in ("outreach_gate.py", "should_initiate.py", "initiate_gate.py", "timeliness.py", "conversation_rhythm.py", "conversation-rhythm.py"):
    p = os.path.join(HIS, name)
    if os.path.isfile(p): scan(p, name)

print("\n== her outreach entry (for the port) ==")
for name in ("velaris-initiate.sh", "openclaw-initiate.sh", "initiate.sh"):
    for base in (os.path.expanduser("~/.openclaw"), os.path.expanduser("~/.openclaw/workspace"), VIN):
        p = os.path.join(base, name)
        if os.path.isfile(p): scan(p, name); break

print("\n(READ-ONLY. Locates the timeliness gate so the demand_response directive can force one outreach through.)")
