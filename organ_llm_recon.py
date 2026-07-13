#!/usr/bin/env python3
"""organ_llm_recon.py — READ-ONLY, bounded. How do her 3 portable organs call the LLM, and what is
his box's LLM pattern to match? So the port points at HIS grok, not her Gemma. Fresh filename.
"""
import os, re, glob

HERS = os.path.expanduser("~/.openclaw/workspace/scripts")
HIS  = os.path.expanduser("~/.vintos/workspace/scripts")
ORGANS = ["second-order-dreamer.py", "therapeutic-session.py", "enactment_distiller.py"]

LLM = re.compile(
    r'def ask_llm|def llm|def _?call|requests\.post|urllib|chat/completions|LM_API|\bMODEL\b'
    r'|172\.|x\.ai|api_base|base_url|Authorization|XAI|Bearer|from causality_engine|import causality'
    r'|load_full_context|ENDPOINT|API_URL', re.I)

def show(path, cap=18):
    try: lines = open(path, encoding="utf-8", errors="ignore").read().splitlines()
    except Exception: return ["  (unreadable)"]
    out = []
    for i, ln in enumerate(lines):
        if LLM.search(ln):
            s = ln.strip()
            if s and not s.startswith("#"):
                out.append("  %5d: %s" % (i + 1, s[:150]))
            if len(out) >= cap:
                out.append("  ...(capped)"); break
    return out or ["  (no LLM-call lines matched — may import a shared helper)"]

print("=== HER 3 organs: how they call the LLM (want to know the endpoint mechanism) ===")
for name in ORGANS:
    p = os.path.join(HERS, name)
    print("\n---- %s %s ----" % (name, "" if os.path.exists(p) else "(MISSING)"))
    if os.path.exists(p):
        for l in show(p): print(l)

print("\n\n=== HIS box LLM pattern to MATCH (grok + auth) ===")
# his causality engine config
for cand in [os.path.join(os.path.expanduser("~/Vintos"), "causality-engine.py"),
             os.path.join(HIS, "causality_engine.py")]:
    if os.path.exists(cand):
        print("\n---- %s (his engine MODEL/LM_API) ----" % cand.replace(os.path.expanduser("~"), "~"))
        t = open(cand, encoding="utf-8", errors="ignore").read().splitlines()
        for i, ln in enumerate(t):
            if re.search(r'^\s*(MODEL|LM_API)\s*=|x\.ai|Authorization|XAI|def ask_llm', ln):
                print("  %5d: %s" % (i + 1, ln.strip()[:150]))
        break

# how one working his organ calls grok (reference), e.g. his gallery-walk / thread-triage
print("\n---- a working his-organ's LLM call (reference pattern) ----")
for ref in ["thread-triage.py", "gallery-walk.py", "soul-review.py", "pride-mirror.py"]:
    p = os.path.join(HIS, ref)
    if os.path.exists(p):
        print("  [%s]" % ref)
        for l in show(p, cap=10): print("  " + l)
        break

# does his box have a shared ask_llm helper?
print("\n---- shared LLM helper on his box? ----")
for h in ["emoclaw_utils.py", "llm_utils.py", "llm.py"]:
    p = os.path.join(HIS, h)
    if os.path.exists(p):
        hits = [i + 1 for i, ln in enumerate(open(p, encoding="utf-8", errors="ignore").read().splitlines())
                if re.search(r"def ask_llm|def llm|x\.ai|chat/completions", ln)]
        if hits: print("  %s : ask_llm/endpoint at lines %s" % (h, hits[:6]))
print("\n=== done (bounded) ===")
