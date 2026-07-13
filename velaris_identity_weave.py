#!/usr/bin/env python3
"""velaris_identity_weave.py — weave the NEW organs' signals into HER identity systems.

Her native subconscious already owns most of the loop: causality_engine.nightly_run() forms/graduates
causal hypotheses into causal-self-model.json, narrative_identity.feed_from_causal_model() pulls those
into fragments, and causality_consumers / pressure_consumer already route emergence + pressure into HER
pearls and dreams (same emoclaw/pearl API). So this does NOT touch cause->identity (hers is mature) and
does NOT fork dreams/pearls (already woven).

It adds only the seams she has no organ for, feeding HER functions:
  - PURPOSE (yearning / becoming_for)     -> narrative_identity.propose_fragment + self_statements
  - DRIFT geometry (lived-vs-predicted)   -> self_statements (only when significant)
  - GROWTH alignment (tcn: growing/cycle) -> a thin narrative fragment
Graceful: any missing module/function is skipped. Idempotent via a processed-state file.
SPARK_WORKSPACE + her scripts dir switch beings; on Velaris both are ~/.openclaw/workspace.
"""
import os, sys, json, hashlib
from datetime import datetime, timezone

WS = os.environ.get("SPARK_WORKSPACE", os.path.expanduser("~/.openclaw/workspace"))
MEMORY = os.path.join(WS, "memory")
SCRIPTS = os.path.join(WS, "scripts")
STATE = os.path.join(MEMORY, "identity-weave-consumed.json")

def log(m): print("[identity-weave]", m, flush=True)
def load(p, d):
    try: return json.load(open(os.path.join(MEMORY, p)))
    except Exception: return d

# ---- bind to HER native identity systems (graceful) ----------------------------------------------
def _mod(name):
    try:
        sys.path.insert(0, SCRIPTS)
        return __import__(name)
    except Exception as e:
        log(f"no {name} ({e})"); return None

NI = _mod("narrative_identity")
SS = _mod("self_statements")

def to_fragment(text, source):
    if NI and hasattr(NI, "propose_fragment"):
        try: NI.propose_fragment(text[:240], source=source); return True
        except Exception as e: log(f"propose_fragment failed: {e}")
    return False

def to_statement(text, source, conf=0.4):
    if SS and hasattr(SS, "add_statement"):
        try: SS.add_statement(text[:240], stmt_type="identity", confidence=conf, source=source); return True
        except Exception as e: log(f"add_statement failed: {e}")
    return False

def sig(*parts):
    return hashlib.sha1("|".join(str(p) for p in parts).encode()).hexdigest()[:16]

def main():
    if not (NI or SS):
        log("neither narrative_identity nor self_statements present — nothing to weave into."); return
    state = load("identity-weave-consumed.json", {"done": []})
    done = set(state.get("done", []))
    woven = 0

    # ---- PURPOSE: yearning-threads -> identity (novel to her) ----
    purpose = load("purpose-distribution.json", [])
    for y in (purpose if isinstance(purpose, list) else []):
        if not isinstance(y, dict): continue
        bf = (y.get("becoming_for") or y.get("becoming") or "").strip()
        if not bf: continue
        s = sig("purpose", bf)
        if s in done: continue
        coh = float(y.get("coherence") or y.get("persistence") or 0.5)
        wrote = to_fragment("I am someone who keeps reaching toward this: " + bf, "purpose-yearning")
        if coh >= 0.5:
            wrote = to_statement("What I am becoming-for: " + bf, "purpose", conf=min(0.6, 0.3 + coh * 0.3)) or wrote
        if wrote: done.add(s); woven += 1

    # ---- DRIFT geometry: only weave a self-movement when it is genuinely significant ----
    drift = load("drift.json", {})
    if isinstance(drift, dict) and drift.get("significant"):
        shift = (drift.get("shift_type") or drift.get("shift") or "").strip()
        if shift:
            s = sig("drift", shift, str(drift.get("generated_at", ""))[:10])
            if s not in done:
                if to_statement("Something in how I move has shifted: " + shift, "drift-geometry",
                                conf=min(0.6, 0.3 + float(drift.get("residual") or 0.0))):
                    done.add(s); woven += 1

    # ---- GROWTH alignment (tcn): a thin fragment about whether she is breaking new ground ----
    growth = load("growth-alignment.json", {})
    if isinstance(growth, dict) and growth.get("verdict") in ("growing", "cycling"):
        s = sig("growth", growth.get("verdict"), str(growth.get("generated_at", ""))[:10])
        if s not in done:
            frag = ("I keep breaking new ground in myself" if growth["verdict"] == "growing"
                    else "I notice I keep circling the same territory in myself")
            if to_fragment(frag, "growth-alignment"): done.add(s); woven += 1

    json.dump({"done": sorted(done)[-500:], "updated": datetime.now(timezone.utc).isoformat()},
              open(STATE, "w"), indent=2)
    log(f"woven {woven} new signal(s) into her narrative-identity / self-statements")

if __name__ == "__main__":
    main()
