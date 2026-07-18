#!/usr/bin/env python3
"""build_mutual_sim.py — Aegis. Mutual Simulation (Spark #15): the INTERACTION model — the third model beside self-
and gloria-model — OPTIMIZED by Presence Audit scores. Reads presence-audit.json (replies scored arrived/moved/
left_alive/explained), separates what LANDS from what falls flat, derives the current growing edge (weakest presence
dimension), writes interaction-model.json, and get_interaction_hint() feeds it back so the scores actually steer the
being. Writes mutual_simulation.py + wires it into his inner_context. DRY-RUN default; --apply commits. SPARK_WORKSPACE
-aware so the same file serves Velaris."""
import os, sys, re, time, shutil

APPLY = "--apply" in sys.argv
SCR = os.path.expanduser("~/.vintos/workspace/scripts")
IC = os.path.join(SCR, "inner_context.py")

SRC = r'''#!/usr/bin/env python3
"""mutual_simulation.py — Mutual Simulation (Spark #15): the INTERACTION model, the third model beside self- and
gloria-model, OPTIMIZED by Presence Audit scores. Separates what LANDS from what falls flat and finds the current
growing edge (weakest presence dimension). Writes interaction-model.json; get_interaction_hint() steers generation
with it, so the scores close the loop. Fail-open. SPARK_WORKSPACE switches beings."""
import os, json, time
WS = os.environ.get("SPARK_WORKSPACE", os.path.expanduser("__DEFAULT_WS__"))
MEMORY = os.path.join(WS, "memory")
AUDIT = os.path.join(MEMORY, "presence-audit.json")
OUT = os.path.join(MEMORY, "interaction-model.json")
GEMMA = "http://172.18.16.1:1234/v1/chat/completions"
GEMMA_MODEL = "google/gemma-4-12b-qat"
HI, LO, WINDOW = 0.6, 0.4, 40

def log(m): print("[mutual-sim]", m, flush=True)
def load(p, d):
    try: return json.load(open(p))
    except Exception: return d

def main():
    import requests, re
    audits = [a for a in load(AUDIT, []) if isinstance(a, dict) and a.get("composite") is not None][-WINDOW:]
    if len(audits) < 6:
        json.dump({"note": "not enough audited replies yet", "n": len(audits)}, open(OUT, "w"), indent=2)
        log("only %d audits - need >=6" % len(audits)); return
    hi = [a for a in audits if a["composite"] >= HI]
    lo = [a for a in audits if a["composite"] < LO]
    def mean(k):
        xs = [float(a[k]) for a in audits if isinstance(a.get(k), (int, float))]
        return sum(xs) / len(xs) if xs else 0.5
    arrived, moved, alive, expl = mean("arrived"), mean("moved"), mean("left_alive"), mean("explained")
    cands = {"arriving from your own wanting": arrived, "moving something (not just describing)": moved,
             "leaving a thread alive": alive}
    edge_name = min(cands, key=cands.get); edge_val = cands[edge_name]
    if expl > 0.5 and expl > (1 - edge_val):
        edge_note = "you've been explaining ABOUT the moment more than being IN it - participate, don't narrate"
    else:
        edge_note = "your weakest reach lately is %s (avg %.2f) - put weight there" % (edge_name, edge_val)
    hn = [a.get("note", "") for a in hi if a.get("note")][-8:]
    ln = [a.get("note", "") for a in lo if a.get("note")][-8:]
    works, flat = [], []
    try:
        prompt = ("These are one-line notes on a being's replies. HIGH-PRESENCE (landed): %s. LOW-PRESENCE (fell "
                  'flat): %s. Return ONLY JSON {"works":["<2-3 short interaction moves that land>"],'
                  '"flat":["<2-3 that fall flat>"]}.' % (" | ".join(hn) or "(none)", " | ".join(ln) or "(none)"))
        r = requests.post(GEMMA, json={"model": GEMMA_MODEL, "temperature": 0.3, "max_tokens": 200,
            "messages": [{"role": "user", "content": prompt}]}, timeout=90)
        d = json.loads(re.search(r"\{.*\}", r.json()["choices"][0]["message"]["content"], re.S).group())
        works = [str(x).strip()[:80] for x in (d.get("works") or [])][:3]
        flat = [str(x).strip()[:80] for x in (d.get("flat") or [])][:3]
    except Exception as e:
        log("pattern extract failed (%s)" % e)
    out = {"what_works": works, "what_falls_flat": flat, "growth_edge": edge_name, "edge_note": edge_note,
           "means": {"arrived": round(arrived, 3), "moved": round(moved, 3), "left_alive": round(alive, 3),
                     "explained": round(expl, 3)},
           "n_high": len(hi), "n_low": len(lo), "n": len(audits), "updated": time.time()}
    json.dump(out, open(OUT, "w"), indent=2)
    log("edge '%s' | works %d flat %d | hi %d lo %d" % (edge_name, len(works), len(flat), len(hi), len(lo)))

def get_interaction_hint():
    d = load(OUT, {})
    if not d or not (d.get("what_works") or d.get("edge_note")): return ""
    parts = []
    if d.get("what_works"): parts.append("landing lately: " + "; ".join(d["what_works"][:2]))
    if d.get("what_falls_flat"): parts.append("going flat: " + "; ".join(d["what_falls_flat"][:2]))
    if d.get("edge_note"): parts.append("growing edge: " + d["edge_note"])
    return "[INTERACTION MODEL - " + ". ".join(parts) + ".]"

if __name__ == "__main__":
    main()
'''

src = SRC.replace("__DEFAULT_WS__", "~/.vintos/workspace")
dst = os.path.join(SCR, "mutual_simulation.py")
print("================  build Mutual Simulation  [%s]  ================\n" % ("APPLY" if APPLY else "DRY-RUN"))
try:
    compile(src, dst, "exec"); print("mutual_simulation.py: compiles OK (%d lines, %s)" % (len(src.splitlines()), "OVERWRITE" if os.path.isfile(dst) else "new"))
except SyntaxError as e:
    print("!! SYNTAX ERROR: %s" % e); sys.exit(1)

ic = open(IC, encoding="utf-8", errors="ignore").read() if os.path.isfile(IC) else None
ic_new = None
if ic is None:
    print("!! inner_context.py not found")
elif "mutual_simulation" in ic:
    print("inner_context.py: already wired — skip")
else:
    m = re.search(r'for\s+mod\s*,\s*fn\s+in\s*\[', ic)
    print("inner_context.py: anchor %s" % ("found" if m else "NOT found"))
    if m:
        ic_new = ic[:m.end()] + '("mutual_simulation", "get_interaction_hint"), ' + ic[m.end():]
        try: compile(ic_new, IC, "exec"); print("  + interaction hint would join the loop (compiles OK)")
        except SyntaxError as e: print("  !! %s" % e); ic_new = None

if not APPLY:
    print("\n(DRY-RUN.)\nTEST:  /usr/bin/python3 ~/.vintos/workspace/scripts/mutual_simulation.py")
    print("Cron:  26 1,7,13,19 * * * SPARK_WORKSPACE=/home/gloria/.vintos/workspace /usr/bin/python3 ~/.vintos/workspace/scripts/mutual_simulation.py >> /tmp/mutual-sim.log 2>&1")
    sys.exit(0)

ts = time.strftime("%Y%m%d-%H%M%S")
if os.path.isfile(dst): shutil.copy2(dst, dst + ".bak-" + ts)
open(dst, "w", encoding="utf-8").write(src); print("\nwrote %s" % dst)
if ic_new:
    shutil.copy2(IC, IC + ".bak-" + ts); open(IC, "w", encoding="utf-8").write(ic_new); print("wired %s" % IC)
print("\nDone. TEST then schedule; Velaris copy follows.")
