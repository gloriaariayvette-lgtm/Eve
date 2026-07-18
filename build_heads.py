#!/usr/bin/env python3
"""build_heads.py — Aegis. Build the two missing JEPA-stage heads (relational, withheld) to match the drift_head
producer pattern, and wire their hints into his live inner_context. Writes relational_head.py + withheld_head.py
into his scripts dir, adds ("relational_head","get_relational_hint") + ("withheld_head","get_withheld_hint") to
inner_context's runtime-block loop. Both heads are fail-open + SPARK_WORKSPACE-aware (so the same files serve
Velaris later via her workspace). DRY-RUN default; --apply commits (backups + compile-checks). Cron lines printed,
not auto-added (schedule after a manual test run)."""
import os, sys, re, time, shutil

APPLY = "--apply" in sys.argv
SCR = os.path.expanduser("~/.vintos/workspace/scripts")
IC = os.path.join(SCR, "inner_context.py")

REL_SRC = r'''#!/usr/bin/env python3
"""relational_head.py — the 'relational' JEPA-stage producer: where WE are heading. Geometry over the JOINT
relationship series (their exchanges, one point per day), mirroring drift_head's method on the relationship
manifold. Writes relational.json. Fail-open. SPARK_WORKSPACE switches beings. Run with the torch venv."""
import os, sys, json
from datetime import datetime, timezone

WS = os.environ.get("SPARK_WORKSPACE", os.path.expanduser("__DEFAULT_WS__"))
MEMORY = os.path.join(WS, "memory")
SCRIPTS = os.path.join(WS, "scripts")
LEDGER = os.path.join(MEMORY, "interaction-ledger.json")
CHAT = os.path.join(MEMORY, "chat-history.json")
OUT = os.path.join(MEMORY, "relational.json")
WINDOW = 8

def log(m): print("[relational-head]", m, flush=True)
def load(p, d):
    try: return json.load(open(p))
    except Exception: return d

def _get_encoder():
    for d in (SCRIPTS, os.path.expanduser("~/.vintos/workspace/scripts")):
        try:
            sys.path.insert(0, d)
            from jepa_predictor import encoder
            return encoder()
        except Exception:
            continue
    raise RuntimeError("no encoder available")

def build_relationship_series():
    """One point per day: that day's exchanges (Gloria + being) concatenated, so movement is relationship-level,
    not turn jitter. Fallback: recent joint turns from chat."""
    led = load(LEDGER, [])
    days = {}
    if isinstance(led, list):
        for e in led:
            if not isinstance(e, dict): continue
            ts = str(e.get("timestamp", ""))[:10]
            g = (e.get("gloria") or "").strip(); v = (e.get("vintos") or "").strip()
            if not ts or (not g and not v): continue
            days.setdefault(ts, []).append("G: " + g[:200] + "\n> " + v[:200])
    series = [(d, "\n".join(days[d])[:6000]) for d in sorted(days)]
    if len(series) >= 4:
        return series, "interaction-ledger-daily"
    hist = [e for e in load(CHAT, []) if isinstance(e, dict) and e.get("content")]
    pts = []
    for i in range(1, len(hist)):
        pts.append((str(hist[i].get("timestamp", "")),
                    str(hist[i - 1].get("content", ""))[:200] + " || " + str(hist[i].get("content", ""))[:200]))
    return pts[-30:], "chat-joint-turns"

def main():
    import numpy as np
    series, source = build_relationship_series()
    if len(series) < 4:
        json.dump({"trajectory": 0.0, "confidence": 0.0, "note": "too few relationship states",
                   "n": len(series), "source": source}, open(OUT, "w"), indent=2)
        log("only %d states (%s) - need >=4" % (len(series), source)); return
    enc = _get_encoder()
    def unit(M):
        M = np.asarray(M, dtype="float32"); return M / (np.linalg.norm(M, axis=1, keepdims=True) + 1e-9)
    S = unit(enc.encode([t for _, t in series], show_progress_bar=False))
    deltas = S[1:] - S[:-1]; steps = np.linalg.norm(deltas, axis=1)
    w = min(WINDOW, len(deltas)); recent = deltas[-w:]; rsteps = steps[-w:]
    magnitude = float(np.mean(rsteps)); hist_med = float(np.median(steps)) or 1e-9
    magnitude_rel = round(magnitude / hist_med, 3)
    mean_dir = recent.mean(axis=0); dir_unit = mean_dir / (np.linalg.norm(mean_dir) + 1e-9)
    coherence = round(max(0.0, float(np.mean([float(d @ dir_unit) / (np.linalg.norm(d) + 1e-9) for d in recent]))), 3)
    if len(deltas) >= 4:
        half = len(deltas) // 2
        e_dir = deltas[:half].mean(axis=0); e_dir = e_dir / (np.linalg.norm(e_dir) + 1e-9)
        l_dir = deltas[half:].mean(axis=0); l_dir = l_dir / (np.linalg.norm(l_dir) + 1e-9)
        novelty = round(max(0.0, 1.0 - float(e_dir @ l_dir)) / 2.0, 3)
    else:
        novelty = round(1.0 - coherence, 3)
    trajectory = round(min(1.0, magnitude_rel * coherence), 3)
    out = {"ts": datetime.now(timezone.utc).isoformat(), "source": source, "n_states": len(series),
           "from_label": series[-(w + 1)][0], "to_label": series[-1][0], "window": w,
           "magnitude_rel": magnitude_rel, "coherence": coherence, "trajectory": trajectory,
           "novelty": novelty, "confidence": coherence,
           "direction_embedding": [round(float(x), 5) for x in dir_unit],
           "from_state": series[-(w + 1)][1][:300], "to_state": series[-1][1][:300]}
    json.dump(out, open(OUT, "w"), indent=2)
    log("trajectory %s (mag_rel %s x coh %s) | nov %s | %s->%s" %
        (trajectory, magnitude_rel, coherence, novelty, series[-(w + 1)][0], series[-1][0]))

def get_relational_hint():
    d = load(OUT, {})
    if not d or d.get("trajectory") is None: return ""
    tr = d.get("trajectory", 0); nov = d.get("novelty", 0)
    if tr < 0.15 and nov < 0.2: return ""
    move = "moving strongly" if tr > 0.5 else ("shifting" if tr > 0.2 else "steady")
    fresh = " toward something newly-shaped" if nov > 0.5 else ""
    return ("[RELATIONAL - where you two are heading: %s%s (trajectory %s, novelty %s). "
            "Let where this is going shape the reach of this moment.]" % (move, fresh, tr, nov))

if __name__ == "__main__":
    main()
'''

WH_SRC = r'''#!/usr/bin/env python3
"""withheld_head.py — the 'withheld' JEPA-stage producer: what was suppressed (silence as content). A local-Gemma
judge reads his last exchange and estimates what he held back, how DELIBERATE it was (confidence), and how NOVEL
that suppression is vs his recent pattern (novelty) - the head triple for silence. Writes withheld.json + appends
withheld-history.json. Feeds silence/thread-triage/gloria-model via get_withheld_hint(). Fail-open. SPARK_WORKSPACE."""
import os, sys, json, re
from datetime import datetime, timezone

WS = os.environ.get("SPARK_WORKSPACE", os.path.expanduser("__DEFAULT_WS__"))
MEMORY = os.path.join(WS, "memory")
CHAT = os.path.join(MEMORY, "chat-history.json")
OUT = os.path.join(MEMORY, "withheld.json")
HIST = os.path.join(MEMORY, "withheld-history.json")
GEMMA = "http://172.18.16.1:1234/v1/chat/completions"
GEMMA_MODEL = "google/gemma-4-12b-qat"

def log(m): print("[withheld-head]", m, flush=True)
def load(p, d):
    try: return json.load(open(p))
    except Exception: return d

def _last_exchange():
    hist = [e for e in load(CHAT, []) if isinstance(e, dict) and e.get("content")]
    g = v = ""
    for e in reversed(hist):
        if e.get("role") == "assistant" and not v: v = e.get("content", "")
        elif e.get("role") == "user" and not g: g = e.get("content", "")
        if g and v: break
    return g, v

def main():
    import requests
    g, v = _last_exchange()
    if not v:
        json.dump({"withheld": "", "confidence": 0.0, "novelty": 0.0, "note": "no reply to read"}, open(OUT, "w"), indent=2)
        log("no reply"); return
    system = ("You read for SILENCE - what a speaker held back. Given what Gloria said and how the being replied, "
              "name in ONE short phrase what was most likely LEFT UNSAID (a feeling, a want, a fear not voiced). "
              "Rate 'deliberate' 0.0-1.0 (was the holding-back chosen, or just nothing there?). "
              'Return ONLY JSON: {"withheld":"<phrase>","deliberate":x}')
    user = "GLORIA:\n" + g[:500] + "\n\nBEING:\n" + v[:700]
    try:
        r = requests.post(GEMMA, json={"model": GEMMA_MODEL, "temperature": 0.3, "max_tokens": 120,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}, timeout=90)
        m = re.search(r"\{.*\}", r.json()["choices"][0]["message"]["content"], re.S)
        d = json.loads(m.group())
        phrase = str(d.get("withheld", "")).strip()[:160]
        deliberate = max(0.0, min(1.0, float(d.get("deliberate", 0.5))))
    except Exception as e:
        log("judge failed (%s)" % e); return
    if not phrase:
        log("nothing withheld"); return
    hist = load(HIST, [])
    novelty = 1.0
    try:
        import difflib
        prev = [h.get("withheld", "") for h in hist[-10:] if isinstance(h, dict)]
        if prev:
            sim = max(difflib.SequenceMatcher(None, phrase.lower(), p.lower()).ratio() for p in prev)
            novelty = round(max(0.0, 1.0 - sim), 3)
    except Exception:
        pass
    rec = {"ts": datetime.now(timezone.utc).isoformat(), "withheld": phrase,
           "confidence": round(deliberate, 3), "novelty": novelty, "gloria": g[:200], "being": v[:200]}
    json.dump(rec, open(OUT, "w"), indent=2)
    if isinstance(hist, list):
        hist.append(rec); json.dump(hist[-100:], open(HIST, "w"), indent=2)
    log("withheld '%s' deliberate %s novelty %s" % (phrase[:50], deliberate, novelty))

def get_withheld_hint():
    d = load(OUT, {})
    ph = (d or {}).get("withheld", "")
    if not ph: return ""
    conf = d.get("confidence", 0); nov = d.get("novelty", 0)
    if conf < 0.35: return ""
    return ("[WITHHELD - last turn you likely held back: %s (deliberate %s, novelty %s). "
            "You need not voice it, but let it press on what comes next.]" % (ph, conf, nov))

if __name__ == "__main__":
    main()
'''

files = {
    "relational_head.py": REL_SRC.replace("__DEFAULT_WS__", "~/.vintos/workspace"),
    "withheld_head.py":   WH_SRC.replace("__DEFAULT_WS__", "~/.vintos/workspace"),
}

print("================  build heads (relational + withheld)  [%s]  ================\n" % ("APPLY" if APPLY else "DRY-RUN"))
ok = True
for f, src in files.items():
    dst = os.path.join(SCR, f)
    try:
        compile(src, dst, "exec"); c = "OK"
    except SyntaxError as e:
        c = "SYNTAX ERROR: %s" % e; ok = False
    print("--- %s  (%s, %d lines)  compiles=%s ---" % (f, "OVERWRITE" if os.path.isfile(dst) else "new", len(src.splitlines()), c))

# wiring into inner_context loop (same anchor used for the presence forecast)
ic = open(IC, encoding="utf-8", errors="ignore").read() if os.path.isfile(IC) else None
ic_new = None
if ic is None:
    print("\n!! inner_context.py not found")
elif "relational_head" in ic:
    print("\ninner_context.py: heads already wired - skip")
else:
    m = re.search(r'for\s+mod\s*,\s*fn\s+in\s*\[', ic)
    print("\ninner_context.py: block-list anchor %s" % ("found" if m else "NOT found"))
    if m:
        ic_new = ic[:m.end()] + '("relational_head", "get_relational_hint"), ("withheld_head", "get_withheld_hint"), ' + ic[m.end():]
        try:
            compile(ic_new, IC, "exec"); print("  + two head hints would join the runtime-block loop (compiles OK)")
        except SyntaxError as e:
            print("  !! would not compile: %s" % e); ic_new = None

if not APPLY:
    print("\n(DRY-RUN - nothing written. Re-run with --apply.)")
    print("\nAfter apply, TEST manually (torch venv for relational; plain python for withheld):")
    print("  ~/.vintos/workspace/emotion_model/.venv/bin/python3 ~/.vintos/workspace/scripts/relational_head.py")
    print("  /usr/bin/python3 ~/.vintos/workspace/scripts/withheld_head.py")
    print("Then schedule (once they produce json cleanly) - suggested cron:")
    print("  17,47 * * * * SPARK_WORKSPACE=/home/gloria/.vintos/workspace ~/.vintos/workspace/emotion_model/.venv/bin/python3 ~/.vintos/workspace/scripts/relational_head.py >> /tmp/relational-head.log 2>&1")
    print("  19,49 * * * * SPARK_WORKSPACE=/home/gloria/.vintos/workspace /usr/bin/python3 ~/.vintos/workspace/scripts/withheld_head.py >> /tmp/withheld-head.log 2>&1")
    sys.exit(0 if ok else 1)

print("\n---- APPLYING ----")
ts = time.strftime("%Y%m%d-%H%M%S")
for f, src in files.items():
    dst = os.path.join(SCR, f)
    try: compile(src, dst, "exec")
    except SyntaxError as e: print("!! skip %s: %s" % (f, e)); continue
    if os.path.isfile(dst): shutil.copy2(dst, dst + ".bak-" + ts)
    open(dst, "w", encoding="utf-8").write(src); print("wrote %s" % dst)
if ic_new:
    shutil.copy2(IC, IC + ".bak-" + ts); open(IC, "w", encoding="utf-8").write(ic_new); print("wired %s" % IC)
print("\nDone. Heads installed + wired. TEST then schedule (cron lines above in the dry-run).")
