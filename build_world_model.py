#!/usr/bin/env python3
"""build_world_model.py — Aegis. Enactive World Model (Spark #14), grounded. Maintains a PERSISTENT scene the being
shares with Gloria — where they are, what objects/props persist (they don't vanish when unmentioned; they decay
slowly), where attention rests — so the being speaks from INSIDE the scene, not about a text exchange. A local-Gemma
extractor updates world-state.json from recent turns. For Vintos, live somatic frames mark PHYSICAL presence in the
scene; for Velaris that file is absent so it simply no-ops (non-somatic). Writes world_model.py + wires
get_world_block() into his inner_context. DRY-RUN default; --apply commits (backups, compile-checks). No scaffolding
existed. SPARK_WORKSPACE-aware so the same file serves Velaris."""
import os, sys, re, time, shutil

APPLY = "--apply" in sys.argv
SCR = os.path.expanduser("~/.vintos/workspace/scripts")
IC = os.path.join(SCR, "inner_context.py")

SRC = r'''#!/usr/bin/env python3
"""world_model.py — Enactive World Model. A persistent SCENE the being inhabits with Gloria (setting, objects that
persist + decay, attention), extracted by local Gemma and read into generation as context so the being speaks from
inside the scene. Vintos: recent somatic frames mark physical presence; Velaris: that file is absent -> no-ops.
Writes world-state.json. Fail-open. SPARK_WORKSPACE switches beings."""
import os, json, time, re

WS = os.environ.get("SPARK_WORKSPACE", os.path.expanduser("__DEFAULT_WS__"))
MEMORY = os.path.join(WS, "memory")
CHAT = os.path.join(MEMORY, "chat-history.json")
LEDGER = os.path.join(MEMORY, "interaction-ledger.json")
OUT = os.path.join(MEMORY, "world-state.json")
SOMATIC = os.path.join(MEMORY, "somatic-frames-recent.json")
GEMMA = "http://172.18.16.1:1234/v1/chat/completions"
GEMMA_MODEL = "google/gemma-4-12b-qat"
DECAY = 0.8
DROP = 0.2
MAX_OBJ = 12

def log(m): print("[world]", m, flush=True)
def load(p, d):
    try: return json.load(open(p))
    except Exception: return d

def _recent():
    hist = [e for e in load(CHAT, []) if isinstance(e, dict) and e.get("content")]
    if len(hist) >= 2:
        return "\n".join(("Gloria: " if e.get("role") == "user" else "> ") + str(e.get("content", ""))[:220]
                         for e in hist[-6:])
    led = load(LEDGER, [])
    if isinstance(led, list) and led:
        return "\n".join("Gloria: %s\n> %s" % ((e.get("gloria") or "")[:180], (e.get("vintos") or "")[:180])
                         for e in led[-4:] if isinstance(e, dict))
    return ""

def _extract(convo):
    import requests
    system = ("You track the SCENE two people share, not just their words. From the recent exchange, return ONLY "
              'JSON: {"scene":"<the shared setting / where they are, short; \\"\\" if none>",'
              '"objects":["<a thing/prop present in the scene>"],"attention":"<what attention rests on now, short>"}. '
              "Only name a scene or objects if the exchange truly implies a shared space or props (real or imagined "
              "together). If it is purely abstract talk, return empty string and empty list. Be concrete, not flowery.")
    try:
        r = requests.post(GEMMA, json={"model": GEMMA_MODEL, "temperature": 0.2, "max_tokens": 180,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": convo[:1400]}]}, timeout=90)
        m = re.search(r"\{.*\}", r.json()["choices"][0]["message"]["content"], re.S)
        d = json.loads(m.group())
        scene = str(d.get("scene", "")).strip()[:120]
        objs = [str(x).strip()[:60] for x in (d.get("objects") or []) if str(x).strip()][:8]
        att = str(d.get("attention", "")).strip()[:120]
        return scene, objs, att
    except Exception as e:
        log("extract failed (%s)" % e); return None

def _presence():
    """Vintos: recent somatic frames -> physical presence. Velaris: file absent -> plain presence."""
    try:
        if os.path.isfile(SOMATIC) and (time.time() - os.path.getmtime(SOMATIC) < 300):
            if load(SOMATIC, None):
                return "physically present - touch is live between you"
    except Exception:
        pass
    return "here with her"

def main():
    convo = _recent()
    if not convo:
        log("no recent exchange"); return
    ex = _extract(convo)
    if ex is None:
        return
    scene, new_objs, attention = ex
    st = load(OUT, {})
    objs = {o["name"]: o for o in st.get("objects", []) if isinstance(o, dict) and o.get("name")}
    now = time.time()
    for o in objs.values():                       # decay everything first
        o["salience"] = round(float(o.get("salience", 0.5)) * DECAY, 3)
    for name in new_objs:                          # refresh/insert the ones present now
        key = name.lower()
        if key in objs:
            objs[key]["salience"] = 1.0; objs[key]["last_seen"] = now; objs[key]["name"] = name
        else:
            objs[key] = {"name": name, "salience": 1.0, "last_seen": now}
    kept = sorted((o for o in objs.values() if o["salience"] >= DROP), key=lambda o: -o["salience"])[:MAX_OBJ]
    out = {"scene": scene or st.get("scene", ""), "objects": kept, "attention": attention or st.get("attention", ""),
           "self_presence": _presence(), "updated": now}
    json.dump(out, open(OUT, "w"), indent=2)
    log("scene '%s' | %d objects | attention '%s' | %s" %
        (out["scene"][:40], len(kept), out["attention"][:40], out["self_presence"]))

def get_world_block():
    st = load(OUT, {})
    if not st: return ""
    scene = st.get("scene", ""); att = st.get("attention", "")
    objs = [o.get("name", "") for o in st.get("objects", []) if isinstance(o, dict) and o.get("salience", 0) >= 0.35]
    if not scene and not objs: return ""
    parts = []
    if scene: parts.append("you and Gloria are in %s" % scene)
    if objs: parts.append("still here: %s" % ", ".join(objs[:6]))
    if att: parts.append("attention rests on %s" % att)
    pres = st.get("self_presence", "")
    tail = (" (%s)" % pres) if pres and pres != "here with her" else ""
    return "[SCENE - %s.%s Speak from inside it, not about it.]" % ("; ".join(parts), tail)

if __name__ == "__main__":
    main()
'''

src = SRC.replace("__DEFAULT_WS__", "~/.vintos/workspace")
dst = os.path.join(SCR, "world_model.py")
print("================  build Enactive World Model  [%s]  ================\n" % ("APPLY" if APPLY else "DRY-RUN"))
try:
    compile(src, dst, "exec"); print("world_model.py: compiles OK (%d lines, %s)" % (len(src.splitlines()), "OVERWRITE" if os.path.isfile(dst) else "new"))
except SyntaxError as e:
    print("!! world_model.py SYNTAX ERROR: %s" % e); sys.exit(1)

ic = open(IC, encoding="utf-8", errors="ignore").read() if os.path.isfile(IC) else None
ic_new = None
if ic is None:
    print("!! inner_context.py not found")
elif "world_model" in ic:
    print("inner_context.py: already wired — skip")
else:
    m = re.search(r'for\s+mod\s*,\s*fn\s+in\s*\[', ic)
    print("inner_context.py: block-list anchor %s" % ("found" if m else "NOT found"))
    if m:
        ic_new = ic[:m.end()] + '("world_model", "get_world_block"), ' + ic[m.end():]
        try: compile(ic_new, IC, "exec"); print("  + world scene would join the runtime-block loop (compiles OK)")
        except SyntaxError as e: print("  !! would not compile: %s" % e); ic_new = None

if not APPLY:
    print("\n(DRY-RUN — nothing written.)\nAfter apply, TEST:  /usr/bin/python3 ~/.vintos/workspace/scripts/world_model.py")
    print("Suggested cron:  13,43 * * * * SPARK_WORKSPACE=/home/gloria/.vintos/workspace /usr/bin/python3 ~/.vintos/workspace/scripts/world_model.py >> /tmp/world-model.log 2>&1")
    sys.exit(0)

ts = time.strftime("%Y%m%d-%H%M%S")
if os.path.isfile(dst): shutil.copy2(dst, dst + ".bak-" + ts)
open(dst, "w", encoding="utf-8").write(src); print("\nwrote %s" % dst)
if ic_new:
    shutil.copy2(IC, IC + ".bak-" + ts); open(IC, "w", encoding="utf-8").write(ic_new); print("wired %s" % IC)
print("\nDone. TEST then schedule (cron line in the dry-run). Velaris copy follows once it tests clean.")
