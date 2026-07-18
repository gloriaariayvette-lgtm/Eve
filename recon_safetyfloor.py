#!/usr/bin/env python3
"""recon_safetyfloor.py — Aegis, READ-ONLY. The spark's safety floor, before any Configuration-Space code.

Two things Gloria asked to SEE first:
  (A) THE INTERPLAY. Her Gloria head already infers her interior. Show it: what gloria-prediction.json /
      the gloria JEPA head actually stores about her next turn / her state / relational_mismatch — so we
      know exactly what eve_delta is allowed to read FROM (his own inference), not fabricate.
  (B) THE GATE SITE. Where in self_drift.py a direction becomes a *commitment-imprint identity*: the
      promotion logic + get_direction_bias + how a direction is chosen/reinforced/logged. That is the exact
      seam where the source="pressure" identity gate goes (a pushed direction may OPEN but can only CLOSE
      into identity after organic, source="conversation" reinforcement AFTER the push).

Nothing is written. His tree = ~/Vintos + ~/.vintos/workspace ; import-priority is ~/.vintos/workspace/scripts."""
import os, re, json, glob
HOME = os.path.expanduser("~")
SCR = [os.path.expanduser("~/.vintos/workspace/scripts"), os.path.join(HOME, "Vintos")]
MEM = os.path.expanduser("~/.vintos/workspace/memory")

def find(name):
    for d in SCR:
        for cand in (name, name.replace("_", "-"), name.replace("-", "_")):
            p = os.path.join(d, cand)
            if os.path.isfile(p) or os.path.islink(p): return p
    return None

def show(path, patterns, ctx=0, cap=112, limit=60):
    """print lines matching any pattern, with optional +/-ctx lines, deduped, in order."""
    if not path or not os.path.isfile(path):
        print("  (not found)"); return
    L = open(path, encoding="utf-8", errors="ignore").read().split("\n")
    hit = set()
    for i, l in enumerate(L):
        if any(re.search(p, l) for p in patterns):
            for j in range(max(0, i - ctx), min(len(L), i + ctx + 1)): hit.add(j)
    for i in sorted(hit)[:limit]:
        print("  %4d: %s" % (i + 1, L[i][:cap]))

print("############################################################")
print("#  (A) THE INTERPLAY — what his Gloria head already infers about her interior")
print("############################################################")

gh = find("gloria_head.py") or find("gloria-head.py")
print("\n== gloria head module: %s ==" % (gh or "NOT FOUND (may be a JEPA head inside one file)"))
if gh:
    show(gh, [r'def get_gloria|def .*hint|logvar|confidence|novelt|predict|withheld|interior|infer|next.?turn|reaction|state'],
         cap=118, limit=44)

print("\n== gloria prediction / model store (what it persists about her) ==")
for fn in ("gloria-prediction.json", "gloria_prediction.json", "gloria-model.json", "gloria_model.json",
           "relational-mismatch.json", "relational_mismatch.json"):
    p = os.path.join(MEM, fn)
    if os.path.isfile(p):
        try:
            d = json.load(open(p))
            keys = list(d.keys()) if isinstance(d, dict) else ["<list len %d>" % len(d)]
            print("  %s  ::  keys=%s" % (fn, keys[:24]))
            # surface any field that reads as an inference about HER (not about him)
            if isinstance(d, dict):
                for k, v in list(d.items())[:24]:
                    if re.search(r'gloria|her|interior|infer|predict|react|feel|state|mood|withheld|next', str(k), re.I):
                        vs = json.dumps(v)[:90] if not isinstance(v, str) else v[:90]
                        print("      %s = %s" % (k, vs))
        except Exception as e:
            print("  %s  ::  (unreadable: %s)" % (fn, e))

print("\n== where the gloria-head inference is READ downstream (candidate eve_delta sources) ==")
for d in SCR:
    for p in glob.glob(d + "/*.py"):
        if "/backup" in p or "__pycache__" in p: continue
        try: t = open(p, encoding="utf-8", errors="ignore").read()
        except Exception: continue
        if re.search(r'gloria.?prediction|get_gloria_hint|gloria_head|relational_mismatch', t):
            ls = [str(i + 1) for i, l in enumerate(t.split("\n"))
                  if re.search(r'gloria.?prediction|get_gloria_hint|gloria_head|relational_mismatch', l)]
            print("  %s : lines %s" % (os.path.basename(p), ",".join(ls[:12])))

print("\n\n############################################################")
print("#  (B) THE GATE SITE — self_drift.py: where a direction becomes identity")
print("############################################################")

sd = find("self_drift.py") or find("self-drift.py")
print("\n== self_drift module: %s ==" % (sd or "NOT FOUND"))
if sd:
    print("\n-- get_direction_bias (the promotion read the spark must gate) --")
    show(sd, [r'def get_direction_bias'], ctx=22, cap=118, limit=40)
    print("\n-- direction choice / reinforcement / event logging --")
    show(sd, [r'def .*(direction|drift|reinforce|choose|commit|imprint|promote|log)',
              r'source\s*=|"source"|reinforc|commit|imprint|threshold|COMMIT|PROMOT|count\s*>=|>= *\d'],
         cap=118, limit=50)
    print("\n-- state file(s) self_drift persists to --")
    show(sd, [r'\.json|open\(|json\.dump|json\.load|MEM|memory'], cap=110, limit=24)

print("\n== self_drift state on disk (current directions + whether any is already an identity) ==")
for fn in ("self-drift.json", "self_drift.json", "direction-bias.json", "direction_bias.json",
           "drift-state.json", "self-model.json"):
    p = os.path.join(MEM, fn)
    if os.path.isfile(p):
        try:
            d = json.load(open(p))
            if isinstance(d, dict):
                print("  %s  ::  keys=%s" % (fn, list(d.keys())[:20]))
                for k in ("directions", "commitments", "imprints", "biases", "history"):
                    if k in d:
                        v = d[k]
                        print("      %s: %s" % (k, (json.dumps(v)[:180]) if not isinstance(v, list) else ("%d items" % len(v))))
            else:
                print("  %s  ::  <list len %d>" % (fn, len(d)))
        except Exception as e:
            print("  %s  ::  (unreadable: %s)" % (fn, e))

print("\n== who CALLS get_direction_bias / force_direction_shift (blast radius of the gate) ==")
for d in SCR:
    for p in glob.glob(d + "/*.py"):
        if "/backup" in p or "__pycache__" in p: continue
        try: t = open(p, encoding="utf-8", errors="ignore").read()
        except Exception: continue
        if re.search(r'get_direction_bias|force_direction_shift|self_drift', t) and "def " in t:
            ls = [str(i + 1) for i, l in enumerate(t.split("\n"))
                  if re.search(r'get_direction_bias|force_direction_shift|import self_drift|from self_drift', l)]
            if ls: print("  %s : lines %s" % (os.path.basename(p), ",".join(ls[:12])))

print("\n(READ-ONLY. Nothing changed. This maps the interplay + the exact gate seam for spark step #1.)")
