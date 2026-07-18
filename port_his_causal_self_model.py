#!/usr/bin/env python3
"""port_his_causal_self_model.py — Aegis. His causal_self_model.py is a 3-function stub; hers is the full 15-function
module (learn -> promote -> surface -> shape -> fracture). Ten functions his live scripts call are DEAD against his
stub (get_self_model_context, add_from_mismatch, add_from_avoidance, check_imprint_promotions, ...). Port HER whole
module to HIM: transform paths ~/.openclaw -> ~/.vintos, fix docstring identity (she/her -> he/his; the module makes
NO LLM calls, so identity is cosmetic-only), keep his causal-self-model.json (same filename+schema — his data
survives). His functions are a strict subset of hers, so nothing of his is lost (this supersedes the minimal
promote_to_commitment_imprint we appended earlier with her canonical one).

Refuses to apply unless (a) the 3 lazily-imported sibling modules exist in his tree, and (b) it compiles, and (c)
no residual openclaw/velaris/she/her remains. Backup + DRY-RUN default."""
import os, sys, re, time, shutil
HER = os.path.expanduser("~/.openclaw/workspace/scripts/causal_self_model.py")
HIS = os.path.expanduser("~/.vintos/workspace/scripts/causal_self_model.py")
HIS_SCR = os.path.expanduser("~/.vintos/workspace/scripts")
APPLY = "--apply" in sys.argv
if not os.path.isfile(HER):
    print("!! her causal_self_model.py not found"); sys.exit(1)
src = open(HER, encoding="utf-8", errors="ignore").read()

def tf(t):
    # paths
    t = t.replace("~/.openclaw/workspace", "~/.vintos/workspace").replace("/.openclaw/", "/.vintos/").replace("~/.openclaw", "~/.vintos")
    # identity (docstrings only — no LLM calls in this module). order: specific before generic.
    t = re.sub(r'\bVelaris\b', "Vintos", t)
    t = re.sub(r'\bherself\b', "himself", t)
    t = re.sub(r'\bher own\b', "his own", t)
    t = re.sub(r'\bshe\b', "he", t)
    t = re.sub(r'\bhers\b', "his", t)
    t = re.sub(r'\bher\b', "his", t)
    return t

new = tf(src)
print("================  port her causal_self_model -> him  [%s]  ================\n" % ("APPLY" if APPLY else "DRY-RUN"))

# (a) dependency modules his fracture/promote functions lazily import
deps = ["yearning_scars", "self_statements", "latent_threads"]
missing = []
for m in deps:
    ok = any(os.path.isfile(os.path.join(HIS_SCR, m + e)) or os.path.islink(os.path.join(HIS_SCR, m + e))
             for e in (".py",)) or os.path.isfile(os.path.join(HIS_SCR, m.replace("_", "-") + ".py"))
    print("  dep %-16s in his tree: %s" % (m, "YES" if ok else "MISSING"))
    if not ok: missing.append(m)

# (b) compile
try:
    compile(new, HIS, "exec"); comp = "OK"
except SyntaxError as e:
    comp = "ERR %s" % e
print("\n  compiles: %s" % comp)

# (c) residuals
resid = sorted(set(re.findall(r'openclaw|velaris|\bshe\b|\bher\b|\bherself\b', new, re.I)))
print("  residual (want none): %s" % (resid or "none"))

print("\n  paths after transform:")
for i, l in enumerate(new.split("\n")):
    if re.search(r'WORKSPACE\s*=|MEMORY\s*=|MODEL_FILE\s*=|\.vintos/workspace.*scripts', l):
        print("    %d: %s" % (i + 1, l.strip()[:96]))
print("  identity docstrings after transform:")
for i, l in enumerate(new.split("\n")):
    if re.search(r'\bhe\b|\bhis\b|\bhimself\b|Vintos', l) and ('"""' in l or l.strip().startswith("#") or "model —" in l or "causality" in l):
        print("    %d: %s" % (i + 1, l.strip()[:92]))

blockers = []
if missing: blockers.append("missing deps %s" % missing)
if comp != "OK": blockers.append("does not compile")
if resid: blockers.append("residuals %s" % resid)

if not APPLY:
    print("\n(DRY-RUN — nothing written.%s --apply to commit.)" %
          ("" if not blockers else "  BLOCKED: " + "; ".join(blockers) + " —"))
    sys.exit(0)
if blockers:
    print("\n!! refusing to apply — %s" % "; ".join(blockers)); sys.exit(1)
ts = time.strftime("%Y%m%d-%H%M%S")
if os.path.isfile(HIS): shutil.copy2(HIS, HIS + ".bak-" + ts)
open(HIS, "w", encoding="utf-8").write(new)
print("\nported -> %s (backup %s)." % (HIS, HIS + ".bak-" + ts))
print("His causal self-model is whole: ten dead functions across seven of his scripts are live. He now learns into\n"
      "a model he can surface (get_self_model_context), feeds it from relational mismatch (add_from_mismatch = the\n"
      "eve_delta feeder), promotes imprints on schedule, and can fracture them under pressure. Substrate ready.")
