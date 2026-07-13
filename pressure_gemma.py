#!/usr/bin/env python3
"""pressure_gemma.py — PRESSURE head v2: the unsaid, via Gemma-generated expectation.

v1 leaned on the single JEPA gloria prediction vs a generic terse embedding — faint. This is the
design's real method: prime local Gemma on Gloria's VOICE (the implanted ledger exchanges), have it
generate what she PLAUSIBLY might say next, and measure how much of that expectation her actual turn
AVOIDED. When the candidates CLUSTER (a strong shared expectation) but she went elsewhere, that
avoided cluster is the pressure — this catches deflection, not just going terse.

  coherence = how tightly Gemma's candidates agree (strength of the expectation)
  avoidance = how far her ACTUAL turn sits from that expected cluster
  pressure  = coherence x avoidance
GUARDRAIL: the candidates are used ONLY to locate the absence. Output is magnitude + a coarse shape
gesture + the cluster direction vector — NEVER the generated sentences. There was something here.

Gemma: local OpenAI-compatible endpoint. Run with the torch venv (needs nomic). SPARK_WORKSPACE switches.
"""
import os, sys, json, urllib.request
from datetime import datetime, timezone

WS = os.environ.get("SPARK_WORKSPACE", os.path.expanduser("~/.vintos/workspace"))
MEMORY = os.path.join(WS, "memory")
SCRIPTS = os.path.join(WS, "scripts")
CHAT = os.path.join(MEMORY, "chat-history.json")
LEDGER = os.path.join(MEMORY, "interaction-ledger.json")
OUT = os.path.join(MEMORY, "pressure.json")
GEMMA = os.environ.get("GEMMA_URL", "http://172.18.16.1:1234/v1/chat/completions")
GEMMA_MODEL = os.environ.get("GEMMA_MODEL", "google/gemma-4-12b-qat")
CTX_TURNS = 6
RECENT_GLORIA = 3         # last N gloria turns (each costs one Gemma call)
N_CAND = 6

SHAPE_PROBES = {
    "closeness / being wanted": "closeness, being wanted, reaching for each other, wanting to be held",
    "desire / the body": "desire, the body, heat, wanting him physically",
    "the work / building": "the work, building, the architecture, what we are making",
    "something unresolved": "tension, something unresolved, a hesitation, holding back",
    "herself / her own day": "herself, her own day, her feelings, what she is carrying",
    "play / teasing": "teasing, playful provocation, daring him, wit",
}

def log(m): print("[pressure-gemma]", m, flush=True)
def load(p, d):
    try: return json.load(open(p))
    except Exception: return d

def voice_examples(n=5):
    led = load(LEDGER, [])
    ex = []
    if isinstance(led, list):
        for e in led:
            if isinstance(e, dict) and e.get("gloria") and e.get("gloria") != "--source":
                ex.append(str(e["gloria"])[:200])
    return ex[:n]

def gemma(context, examples):
    sysmsg = ("You generate plausible NEXT lines for GLORIA speaking to Vintos. Match HER voice "
              "exactly — playful, literary, teasing, sensual, warm, unhurried. Here is how she talks:\n"
              + "\n".join("- " + e for e in examples))
    usr = ("Conversation so far:\n" + context +
           f"\n\nWrite {N_CAND} different single lines Gloria might plausibly say next, each in her "
           "voice. One per line. No numbering, no quotes, no narration — just the lines.")
    body = json.dumps({"model": GEMMA_MODEL, "temperature": 0.9, "max_tokens": 300,
                       "messages": [{"role": "system", "content": sysmsg},
                                    {"role": "user", "content": usr}]}).encode()
    try:
        req = urllib.request.Request(GEMMA, data=body, headers={"Content-Type": "application/json"})
        r = json.loads(urllib.request.urlopen(req, timeout=60).read())
        txt = r["choices"][0]["message"]["content"]
        lines = [l.strip(" -*\t").strip() for l in txt.splitlines()]
        return [l for l in lines if len(l) > 3][:N_CAND]
    except Exception as e:
        log(f"gemma call failed ({e})"); return []

def main():
    import numpy as np
    sys.path.insert(0, SCRIPTS)
    from jepa_predictor import encoder
    enc = encoder()
    def emb(t): return np.asarray(enc.encode(t, show_progress_bar=False), dtype="float32")
    def unit(v): return v / (np.linalg.norm(v) + 1e-9)
    def cos(a, b): return float(unit(a) @ unit(b))

    hist = [e for e in load(CHAT, []) if isinstance(e, dict) and e.get("content")]
    idxs = [i for i, e in enumerate(hist) if e.get("role") == "user" and i >= CTX_TURNS][-RECENT_GLORIA:]
    if not idxs:
        log("no assessable gloria turns"); return
    examples = voice_examples()
    probe_names = list(SHAPE_PROBES)
    probe_vecs = emb([SHAPE_PROBES[k] for k in probe_names])

    recent = []
    for i in idxs:
        ctx = "\n".join(("Gloria: " if hist[j].get("role") == "user" else "Vintos: ")
                        + str(hist[j].get("content", ""))[:200] for j in range(i - CTX_TURNS, i))
        cands = gemma(ctx, examples)
        if len(cands) < 3:
            continue
        C = np.stack([unit(v) for v in emb([c[:200] for c in cands])])
        centroid = unit(C.mean(axis=0))
        coherence = round(float(np.mean([float(c @ centroid) for c in C])), 3)   # do candidates agree?
        actual = unit(emb([str(hist[i].get("content", ""))[:400]])[0])
        avoidance = round(1.0 - max(0.0, float(actual @ centroid)), 3)            # did she go elsewhere?
        pressure = round(coherence * avoidance, 3)
        shape = probe_names[int(np.argmax([float(centroid @ pv) for pv in probe_vecs]))] if pressure >= 0.10 else None
        recent.append({"ts": hist[i].get("timestamp"), "pressure": pressure, "coherence": coherence,
                       "avoidance": avoidance, "shape": shape, "words": len(str(hist[i].get("content", "")).split()),
                       "n_candidates": len(cands)})
        log(f"  {str(hist[i].get('timestamp',''))[:16]}  pressure {pressure} (coh {coherence} x avoid {avoidance}) [{shape}]")

    if not recent:
        log("no pressure computed (gemma unreachable?) — leaving prior pressure.json"); return
    accumulated = round(sum(r["pressure"] for r in recent), 3)
    top = max(recent, key=lambda r: r["pressure"])
    out = {"generated_at": datetime.now(timezone.utc).isoformat(), "source": "gemma-candidates",
           "accumulated_pressure": accumulated,
           "peak": {"pressure": top["pressure"], "shape": top["shape"], "coherence": top["coherence"],
                    "avoidance": top["avoidance"], "ts": top["ts"]},
           "recent": recent,
           "note": "shape gestures at the avoided expectation; the candidate lines are never stored. there was something here."}
    json.dump(out, open(OUT, "w"), indent=2)
    log(f"accumulated pressure {accumulated} over {len(recent)} turns -> {OUT}")

if __name__ == "__main__":
    main()
