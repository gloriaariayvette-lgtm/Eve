#!/usr/bin/env python3
"""distiller_port_prep.py — READ-ONLY. Show her distiller's LLM call internals (endpoint/model/headers)
and his box's grok-auth pattern, so the port hits HIS grok WITH the Authorization header (not her Gemma,
not unauthenticated -> no KeyError 'choices'). Fresh name.
"""
import os, re, glob

HERS = os.path.expanduser("~/.openclaw/workspace/scripts")
HIS  = os.path.expanduser("~/.vintos/workspace/scripts")
HOME = os.path.expanduser("~")

print("=== HER distiller call_llm + config (lines 1-62 verbatim) ===")
F = os.path.join(HERS, "enactment_distiller.py")
lines = open(F, encoding="utf-8", errors="ignore").read().splitlines()
for i in range(0, min(62, len(lines))):
    s = lines[i].rstrip()
    if s.strip():
        print("  %5d: %s" % (i + 1, s[:160]))

print("\n\n=== HIS grok-auth pattern to match ===")
# his engine config
for cand in [os.path.join(HOME, "Vintos", "causality-engine.py"), os.path.join(HIS, "causality_engine.py")]:
    if os.path.exists(cand):
        print("\n-- %s : MODEL/LM_API/auth --" % cand.replace(HOME, "~"))
        for i, ln in enumerate(open(cand, encoding="utf-8", errors="ignore").read().splitlines()):
            if re.search(r'^\s*(MODEL|LM_API)\s*=|api\.x\.ai|Authorization|Bearer|XAI_API_KEY', ln):
                print("  %5d: %s" % (i + 1, ln.strip()[:150]))
        break

# how a working his-organ authenticates (reference); search his scripts for Bearer/XAI usage
print("\n-- a working his-organ's authed grok call (reference) --")
found = 0
for f in sorted(glob.glob(os.path.join(HIS, "*.py"))):
    txt = open(f, encoding="utf-8", errors="ignore").read()
    if ("api.x.ai" in txt or "XAI_API_KEY" in txt) and ("Authorization" in txt or "Bearer" in txt):
        print("  [%s]" % os.path.basename(f))
        for i, ln in enumerate(txt.splitlines()):
            if re.search(r'api\.x\.ai|Authorization|Bearer|XAI_API_KEY|MODEL\s*=|def ask_llm|def call_llm', ln):
                print("    %5d: %s" % (i + 1, ln.strip()[:140]))
        found += 1
        if found >= 2: break
if not found:
    print("  (no his-organ uses api.x.ai + Bearer directly — auth may live in the engine/env)")

# where does XAI_API_KEY come from on his box?
print("\n-- XAI_API_KEY source (env/cron) --")
for p in [os.path.join(HOME, ".vintos", "env"), os.path.join(HOME, ".bashrc"), os.path.join(HOME, ".profile")]:
    if os.path.exists(p):
        for ln in open(p, encoding="utf-8", errors="ignore").read().splitlines():
            if "XAI_API_KEY" in ln:
                print("  %s: %s" % (os.path.basename(p), ln.strip()[:60] + "...(redacted)"))
print("\n=== done ===")
