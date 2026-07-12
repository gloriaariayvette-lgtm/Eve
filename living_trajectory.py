#!/usr/bin/env python3
"""living_trajectory.py — Spark System 1 (v3, production).

One continuously-moving object: self_trajectory, gloria_trajectory, unresolved
(curiosities/tensions/motifs w/ momentum), cache (System 2 fills). Runs every 15
min via cron (the object moves even when Gloria is absent) and can be called
in-process on each interaction. Read-only except living-trajectory.json. Fail-open.
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
    """First matching text field; else join meaningful string values (noise-filtered)."""
    if isinstance(obj, str):
        return obj.strip()[:limit]
    if isinstance(obj, dict):
        for k in fields:
            v = obj.get(k)
            if isinstance(v, str) and _clean(v):
                return v.strip()[:limit]
        vals = [_clean(v) for v in obj.values() if isinstance(v, str)]
        vals = [v for v in vals if v]
        if vals:
            return " · ".join(vals)[:limit]
    if isinstance(obj, list) and obj:
        return deep_text(obj[-1], *fields, limit=limit)
    return ""

import re
NOISE = re.compile(r'^(lt_|\d{4}-\d\d|expand|refine|hold|pivot|resolve|want:)', re.I)

def _clean(v):
    v = v.strip()
    return "" if (NOISE.match(v) or len(v) < 12) else v

def num(d, *fields, default=0.5):
    if isinstance(d, dict):
        for k in fields:
            v = d.get(k)
            if isinstance(v, (int, float)):
                return float(v)
    return default

TXT = ("origin", "thread", "text", "tension", "question", "summary", "title",
       "content", "description", "statement", "note", "label")

def _flatten(seq):
    """tensions is a list that may contain nested lists — flatten one level."""
    out = []
    for e in seq if isinstance(seq, list) else []:
        if isinstance(e, list):
            out.extend(e)
        else:
            out.append(e)
    return out

def build():
    wants      = load("current-wants.json", [])
    latent     = load("latent-threads.json", {})
    unfinished = load("unfinished-threads.json", [])
    tension    = load("tension-field.json", {})
    carryover  = load("carryover.json", {})
    emo        = load("emotional-state.json", {})
    gmodel     = load("gloria-model.json", {})

    latent_threads = latent.get("threads", []) if isinstance(latent, dict) else []
    tensions       = _flatten(tension.get("tensions", []) if isinstance(tension, dict) else [])
    stack          = carryover.get("stack", []) if isinstance(carryover, dict) else []

    # self_trajectory
    active = [w for w in wants if isinstance(w, dict)
              and not w.get("fulfilled") and not w.get("dismissed")]
    active.sort(key=lambda w: (w.get("intensity", 0), w.get("timestamp", "")), reverse=True)
    top = stack[-1] if stack else {}
    self_traj = {
        "declared": [deep_text(w, "want") for w in active[:3] if deep_text(w, "want")],
        "carryover_lean": {
            "direction_bias": top.get("direction_bias"),
            "boost_thread_id": top.get("boost_thread_id"),
            "weight": top.get("weight"),
        } if isinstance(top, dict) else {},
        "emotional_trajectory": emo.get("trajectory") if isinstance(emo, dict) else None,
        "updated": datetime.now(timezone.utc).isoformat(),
    }

    # gloria_trajectory — portrait, else recent observations
    portrait = gmodel.get("portrait") if isinstance(gmodel, dict) else ""
    predicted = portrait.strip()[:280] if isinstance(portrait, str) and portrait.strip() else ""
    if not predicted:
        obs = gmodel.get("observations", []) if isinstance(gmodel, dict) else []
        predicted = " · ".join(deep_text(o, "observation", "text", "note", "summary")
                                for o in obs[-2:] if deep_text(o, "observation", "text", "note", "summary"))[:280]
    gloria_traj = {"predicted": predicted, "updated": datetime.now(timezone.utc).isoformat()}

    # unresolved
    unresolved = []
    for src, tag, mfields in [
        (latent_threads, "latent-thread",     ("salience", "momentum", "pressure", "weight")),
        (unfinished,     "unfinished-thread", ("priority", "weight", "momentum")),
        (tensions,       "tension",           ("pressure", "weight", "intensity")),
    ]:
        for e in (src if isinstance(src, list) else []):
            t = deep_text(e, *TXT)
            if not t:
                continue
            unresolved.append({
                "text": t,
                "kind": tag,
                "momentum": num(e, *mfields, default=0.5),
                "recurrence": int(num(e, "triage_count", "loss_count", "recurrence", "count", default=1)),
            })
    unresolved.sort(key=lambda x: (x["momentum"], x["recurrence"]), reverse=True)

    # trimmed emotion snapshot (no gru_hidden_state)
    snap = {kk: vv for kk, vv in (emo.items() if isinstance(emo, dict) else [])
            if kk in ("baseline_emotion", "emotion_vector", "trajectory", "message_count", "last_updated")}

    return {
        "self_trajectory": self_traj,
        "gloria_trajectory": gloria_traj,
        "unresolved": unresolved[:20],
        "cache": load("latent-cache.json", []),
        "emotion_snapshot": snap,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "version": "3.1",
    }

def build_and_write():
    traj = build()
    try:
        json.dump(traj, open(OUT, "w"), indent=2)
    except Exception:
        pass
    return traj

if __name__ == "__main__":
    traj = build_and_write()
    st = traj["self_trajectory"]
    print("self.declared:")
    for d in st["declared"]:
        print("   -", d[:100])
    print("self.carryover_lean:", st["carryover_lean"])
    print("gloria.predicted:", (traj["gloria_trajectory"]["predicted"] or "(none)")[:140])
    print(f"unresolved: {len(traj['unresolved'])} items; top 5:")
    for u in traj["unresolved"][:5]:
        print(f"   [{u['kind']} m={u['momentum']:.2f} r={u['recurrence']}] {u['text'][:80]}")
    print(f"cache (from latent prep): {len(traj['cache'])} arrivals")
    print(f"wrote {OUT}")
