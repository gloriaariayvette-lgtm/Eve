#!/usr/bin/env python3
"""living_trajectory.py — Spark System 1 (v1, dry-run / schema-probe).

A single moving object merging: self_trajectory, gloria_trajectory, unresolved
(curiosities/tensions/motifs with momentum), and cache (filled later by System 2).

This v1 READS existing memory files defensively, assembles a draft trajectory,
and — on this first run — also prints the SHAPE of every source it touches so the
build can be calibrated to real schemas instead of guesses. It only writes a new
file (living-trajectory.json); it changes nothing else. Fail-open throughout.
"""
import os, json, glob
from datetime import datetime, timezone

MEMORY = os.path.expanduser("~/.vintos/workspace/memory")
OUT    = os.path.join(MEMORY, "living-trajectory.json")

def load(name, default):
    try:
        with open(os.path.join(MEMORY, name)) as f:
            return json.load(f)
    except Exception:
        return default

def shape(name, obj):
    """Describe a source file's structure for calibration."""
    if isinstance(obj, list):
        head = obj[0] if obj else None
        keys = sorted(head.keys()) if isinstance(head, dict) else type(head).__name__
        return f"{name}: list[{len(obj)}] first-keys={keys}"
    if isinstance(obj, dict):
        return f"{name}: dict keys={sorted(obj.keys())[:12]}"
    return f"{name}: {type(obj).__name__}"

def first_text(d, *fields):
    """Pull the first present, non-empty text field from a dict."""
    if not isinstance(d, dict):
        return str(d)[:200] if d else ""
    for k in fields:
        v = d.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return ""

def build():
    probe = []
    # --- sources ---
    wants      = load("current-wants.json", [])
    latent     = load("latent-threads.json", [])
    unfinished = load("unfinished-threads.json", [])
    tension    = load("tension-field.json", [])
    carryover  = load("carryover.json", {})
    emo        = load("emotional-state.json", {})
    gmodel     = load("gloria-model.json", {})
    for n, o in [("current-wants", wants), ("latent-threads", latent),
                 ("unfinished-threads", unfinished), ("tension-field", tension),
                 ("carryover", carryover), ("emotional-state", emo),
                 ("gloria-model", gmodel)]:
        probe.append(shape(n, o))

    # --- self_trajectory: strongest active wants + carryover lean ---
    active = [w for w in wants if isinstance(w, dict)
              and not w.get("fulfilled") and not w.get("dismissed")]
    active.sort(key=lambda w: (w.get("intensity", 0), w.get("timestamp", "")), reverse=True)
    self_traj = {
        "declared": [first_text(w, "want") for w in active[:3] if first_text(w, "want")],
        "carryover_lean": first_text(carryover, "lean", "text", "summary", "direction"),
        "updated": datetime.now(timezone.utc).isoformat(),
    }

    # --- gloria_trajectory: from gloria-model portrait ---
    gloria_traj = {
        "predicted": first_text(gmodel, "trajectory", "direction", "summary", "portrait"),
        "updated": datetime.now(timezone.utc).isoformat(),
    }

    # --- unresolved: threads + tensions, each with a coarse momentum ---
    unresolved = []
    for src, tag in [(latent, "latent-thread"), (unfinished, "unfinished-thread"),
                     (tension, "tension")]:
        items = src if isinstance(src, list) else src.get("clusters", []) if isinstance(src, dict) else []
        for e in items:
            t = first_text(e, "thread", "text", "question", "summary", "title", "content")
            if not t:
                continue
            unresolved.append({
                "text": t[:280],
                "kind": tag,
                "momentum": float(e.get("weight", e.get("momentum", e.get("pressure", 0.5)))) if isinstance(e, dict) else 0.5,
                "recurrence": int(e.get("recurrence", e.get("count", 1))) if isinstance(e, dict) else 1,
            })
    unresolved.sort(key=lambda x: (x["momentum"], x["recurrence"]), reverse=True)

    traj = {
        "self_trajectory": self_traj,
        "gloria_trajectory": gloria_traj,
        "unresolved": unresolved[:20],
        "cache": [],   # System 2 (Latent Preparation) fills this
        "emotion_snapshot": emo if isinstance(emo, dict) else {},
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "version": "1-dryrun",
    }
    return traj, probe

if __name__ == "__main__":
    traj, probe = build()
    print("=== SOURCE SHAPES (calibration) ===")
    for line in probe:
        print(" ", line)
    print("\n=== DRAFT LIVING TRAJECTORY ===")
    print("self.declared:", traj["self_trajectory"]["declared"])
    print("self.carryover_lean:", (traj["self_trajectory"]["carryover_lean"] or "(none)")[:120])
    print("gloria.predicted:", (traj["gloria_trajectory"]["predicted"] or "(none)")[:120])
    print("unresolved:", len(traj["unresolved"]), "items; top 3:")
    for u in traj["unresolved"][:3]:
        print(f"   [{u['kind']} m={u['momentum']:.2f}] {u['text'][:90]}")
    try:
        json.dump(traj, open(OUT, "w"), indent=2)
        print(f"\nwrote {OUT}")
    except Exception as e:
        print(f"\nwrite failed: {e}")
