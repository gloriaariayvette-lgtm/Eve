#!/usr/bin/env python3
"""recon_velaris_overlap.py — Aegis, READ-ONLY. Decide port/rename/skip for ambition-check + emotional_operators by
comparing his versions against her existing systems: (A) his ambition-check purpose+writes+endpoint vs HER
ambition_review + anything that writes ambitions.json / marks completions; (B) his emotional_operators purpose+
writes+endpoint vs HER emotion systems (operator-log / emotional-landscape / state-transition compiler). Nothing changed."""
import os, re, glob
HOME = os.path.expanduser("~")
HIS = HOME + "/.vintos/workspace/scripts"
HISV = HOME + "/Vintos"
HER = HOME + "/.openclaw/workspace/scripts"
HERMEM = HOME + "/.openclaw/workspace/memory"

def head(name, dirs, n=16):
    for d in dirs:
        p = os.path.join(d, name)
        if os.path.isfile(p):
            L = open(p, encoding="utf-8", errors="ignore").read().split("\n")
            print("  --- %s (%dL) ---" % (p, len(L)))
            shown = 0
            for i, l in enumerate(L):
                if i < 6 or re.search(r'json\.dump|\.json|http|:1234|:8599|api\.x\.ai|"model"|MODEL\s*=|def |write|ambition|complet', l):
                    print("    %d: %s" % (i + 1, l.strip()[:96])); shown += 1
                if shown > 22: break
            return p
    print("  (%s not found)" % name); return None

print("===== (A1) HIS ambition-check.py =====")
head("ambition-check.py", [HISV, HIS])
print("\n===== (A2) HER ambition_review.py (her existing) =====")
head("ambition_review.py", [HER])
print("\n===== (A3) does SHE already write ambitions.json / mark completions? =====")
for p in glob.glob(HER + "/*.py"):
    t = open(p, encoding="utf-8", errors="ignore").read()
    for i, l in enumerate(t.split("\n")):
        if re.search(r'ambitions?\.json|complet(ed|ion)|ambition', l, re.I):
            print("  %s:%d: %s" % (os.path.basename(p), i + 1, l.strip()[:88])); break
print("  her memory has ambitions.json: %s" % os.path.isfile(HERMEM + "/ambitions.json"))

print("\n===== (B1) HIS emotional_operators.py =====")
head("emotional_operators.py", [HISV, HIS])
print("\n===== (B2) does SHE have an emotional-operator / state-transition compiler? =====")
hit = False
for p in glob.glob(HER + "/*.py"):
    b = os.path.basename(p)
    t = open(p, encoding="utf-8", errors="ignore").read()
    if re.search(r'operator|state.?transition|emotional.?landscape|what did this utterance', t, re.I):
        for i, l in enumerate(t.split("\n")):
            if re.search(r'operator|state.?transition|emotional.?landscape', l, re.I):
                print("  %s:%d: %s" % (b, i + 1, l.strip()[:88])); hit = True; break
if not hit: print("  (no operator/state-transition compiler found in her tree)")
print("  her memory has: operator-log.jsonl=%s  emotional-landscape.json=%s" %
      (os.path.isfile(HERMEM + "/operator-log.jsonl"), os.path.isfile(HERMEM + "/emotional-landscape.json")))
