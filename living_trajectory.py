#!/usr/bin/env python3
"""living_trajectory.py — Spark System 1 (v2, calibrated).

A single moving object merging self_trajectory, gloria_trajectory, unresolved
(curiosities/tensions/motifs with momentum), and cache (System 2 fills cache).

v2 reads the real nested schemas (threads/tensions/stack/portrait) confirmed by
v1's probe. Still read-only except for living-trajectory.json. Fail-open. Prints
a compact nested-shape line so any remaining empty field is diagnosable.
"""
import os, json
from datetime import datetime, timezone

MEMORY = os.path.expanduser("~/.vintos/workspace/memory")
OUT    = os.path.join(MEMORY, "living-trajectory.json")

def load(name, default):
    try:
        with open(os.path.join(MEMORY, name)) as f:
            return json.load(f)
    except Exception:
        return default

def deep_text(obj, *fields, limit=280):
    """Pull first non-empty text; if a dict has no matching field, join its string values."""
    if isinstance(obj, str):
        return obj.strip()[:limit]
    if isinstance(obj, dict):
        for k in fields:
            v = obj.get(k)
            if isinstance(v, str) and v.strip():
                return v.strip()[:limit]
        # fallback: concatenate string values
        vals = [v.strip() for v in obj.values() if isinstance(v, str) and v.strip()]
        if vals:
            return " · ".join(vals)[:limit]
    if isinstance(obj, list) and obj:
        return deep_text(obj[-1], *fields, limit=limit)
    return ""

def num(d, *fields, default=0.5):
    if isinstance(d, dict):
        for k in fields:
            v = d.get(k)
            if isinstance(v, (int, float)):
                return float(v)
    return default

TXT = ("thread", "text", "tension", "question", "summary", "title", "content",
       "description", "statement", "note", "lean", "label", "name", "want")

def build():
    wants      = load("current-wants.json", [])
    latent     = load("latent-threads.json", {})
    unfinished = load("unfinished-threads.json", [])
    tension    = load("tension-field.json", {})
    carryover  = load("carryover.json", {})
    emo        = load("emotional-state.json", {})
    gmodel     = load("gloria-model.json", {})

    latent_threads = latent.get("threads", []) if isinstance(latent, dict) else []
    tensions       = tension.get("tensions", []) if isinstance(tension, dict) else []
    stack          = carryover.get("stack", []) if isinstance(carryover, dict) else []

    # nested-shape probe (one line, for final calibration)
    def k(o):
        return sorted(o[0].keys()) if isinstance(o, list) and o and isinstance(o[0], dict) else (
               sorted(o.keys()) if isinstance(o, dict) else type(o).__name__)
    probe = (f"threads[{len(latent_threads)}]={k(latent_threads)} | "
             f"tensions[{len(tensions)}]={k(tensions)} | "
             f"stack[{len(stack)}]={k(stack)} | "
             f"portrait={k(gmodel.get('portrait'))}")

    # self_trajectory
    active = [w for w in wants if isinstance(w, dict)
              and not w.get("fulfilled") and not w.get("dismissed")]
    active.sort(key=lambda w: (w.get("intensity", 0), w.get("timestamp", "")), reverse=True)
    self_traj = {
        "declared": [deep_text(w, "want") for w in active[:3] if deep_text(w, "want")],
        "carryover_lean": deep_text(stack, "lean", "text", "summary", "direction", "note"),
        "emotional_trajectory": emo.get("trajectory") if isinstance(emo, dict) else None,
        "updated": datetime.now(timezone.utc).isoformat(),
    }

    # gloria_trajectory
    gloria_traj = {
        "predicted": deep_text(gmodel.get("portrait"), "trajectory", "direction",
                               "summary", "current", "heading"),
        "updated": datetime.now(timezone.utc).isoformat(),
    }

    # unresolved
    unresolved = []
    for src, tag, mfields in [
        (latent_threads,     "latent-thread",     ("salience", "weight", "momentum")),
        (unfinished,         "unfinished-thread", ("priority", "weight", "momentum")),
        (tensions,           "tension",           ("pressure", "weight", "intensity")),
    ]:
        for e in (src if isinstance(src, list) else []):
            t = deep_text(e, *TXT)
            if not t:
                continue
            unresolved.append({
                "text": t,
                "kind": tag,
                "momentum": num(e, *mfields, default=0.5),
                "recurrence": int(num(e, "triage_count", "recurrence", "count", default=1)),
            })
    unresolved.sort(key=lambda x: (x["momentum"], x["recurrence"]), reverse=True)

    # trimmed emotion snapshot (no gru_hidden_state)
    snap = {kk: vv for kk, vv in emo.items()
            if isinstance(emo, dict) and kk in
            ("baseline_emotion", "emotion_vector", "trajectory", "message_count", "last_updated")}

    traj = {
        "self_trajectory": self_traj,
        "gloria_trajectory": gloria_traj,
        "unresolved": unresolved[:20],
        "cache": [],
        "emotion_snapshot": snap,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "version": "2",
    }
    return traj, probe

if __name__ == "__main__":
    traj, probe = build()
    print("=== NESTED SHAPES ===")
    print(" ", probe)
    print("\n=== LIVING TRAJECTORY ===")
    print("self.declared:")
    for d in traj["self_trajectory"]["declared"]:
        print("   -", d[:100])
    print("self.carryover_lean:", (traj["self_trajectory"]["carryover_lean"] or "(none)")[:120])
    print("gloria.predicted:", (traj["gloria_trajectory"]["predicted"] or "(none)")[:120])
    print("unresolved:", len(traj["unresolved"]), "items; top 5:")
    for u in traj["unresolved"][:5]:
        print(f"   [{u['kind']} m={u['momentum']:.2f} r={u['recurrence']}] {u['text'][:80]}")
    try:
        json.dump(traj, open(OUT, "w"), indent=2)
        print(f"\nwrote {OUT}")
    except Exception as e:
        print(f"\nwrite failed: {e}")
