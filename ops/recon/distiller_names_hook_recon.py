#!/usr/bin/env python3
"""distiller_names_hook_recon.py — READ-ONLY. Two things for a complete distiller port in one pass:
  1. Every Velaris/gendered-pronoun line in her enactment_distiller.py (so name+pronoun swaps are exact,
     and I don't wrongly swap 'her' that means Gloria).
  2. Her server's call-site for the distiller (import + process/scan call), so Vintos's post-response
     hook mirrors a known-good one. Fresh name.
"""
import os, re

HERS_SCRIPTS = os.path.expanduser("~/.openclaw/workspace/scripts")
HER_SERVER   = os.path.expanduser("~/velaris-server/server.py")
ED = os.path.join(HERS_SCRIPTS, "enactment_distiller.py")

print("=== 1. name / pronoun lines in her enactment_distiller.py (need exact swaps) ===")
lines = open(ED, encoding="utf-8", errors="ignore").read().splitlines()
NAMES = re.compile(r'\b(Velaris|she|her|hers|herself|he|him|his|himself)\b')
for i, ln in enumerate(lines):
    if NAMES.search(ln):
        # mark which tokens matched so I can judge being-vs-Gloria
        toks = ",".join(sorted(set(re.findall(r'\b(Velaris|she|her|hers|herself|he|him|his|himself)\b', ln))))
        print("  %5d [%s]: %s" % (i + 1, toks, ln.strip()[:150]))
print("  (none)" if not any(NAMES.search(l) for l in lines) else "")

print("\n\n=== 2. her server's distiller call-site (mirror this hook onto his server) ===")
if not os.path.exists(HER_SERVER):
    print("  her server not found:", HER_SERVER)
else:
    srv = open(HER_SERVER, encoding="utf-8", errors="ignore").read().splitlines()
    HOOK = re.compile(r'enactment[_-]?distiller|from enactment|import enactment|\.process\(|\.scan\(|distiller', re.I)
    hits = [i for i, ln in enumerate(srv) if HOOK.search(ln)]
    if not hits:
        print("  no direct enactment_distiller reference in her server — it may be invoked via a")
        print("  generic post-response scanner list. Searching for that:")
        SCAN = re.compile(r'post[_-]?response|background|Thread\(|scanners|after.*respond|_scan|process_response', re.I)
        hits = [i for i, ln in enumerate(srv) if SCAN.search(ln)]
    for i in hits[:24]:
        print("  %5d: %s" % (i + 1, srv[i].strip()[:150]))
    print("  (%d call-site line(s))" % len(hits))
print("\n=== done ===")
