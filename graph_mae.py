#!/usr/bin/env python3
"""graph_mae.py — structural blind-spot finder for his inner life (Graph-MAE in spirit).

His architecture is a graph: ~30 memory systems, data flowing between them — but the wiring was all
hand-authored. What connections does the data IMPLY that nobody coded? This models each memory system
as a node (content embedding + update time), builds the temporal co-activation graph, and surfaces
the two kinds of structural gap:

  MISSING EDGE   : two systems highly SIMILAR in content but that never co-activate — they're about
                   the same thing yet nothing connects them ("these should be wired, and aren't").
  PURPOSELESS FLOW: two systems that co-activate but are semantically unrelated ("this flow exists
                   but has no apparent reason").

The strongest missing edges become emergent threads — connections the architecture is missing, that
the data keeps hinting at. Run with the torch venv. SPARK_WORKSPACE switches.
"""
import os, sys, json, glob, time

WS = os.environ.get("SPARK_WORKSPACE", os.path.expanduser("~/.vintos/workspace"))
MEMORY = os.path.join(WS, "memory")
SCRIPTS = os.path.join(WS, "scripts")
OUT = os.path.join(MEMORY, "graph-gaps.json")
COACT_WINDOW = 1800       # seconds — two systems "co-activate" if updated within this of each other
SIM_HI = 0.62             # content similarity that counts as "about the same thing"
SIM_LO = 0.42
SKIP = {"graph-gaps.json", "chat-history.json", "avatar-log.json"}

def log(m): print("[graph-mae]", m, flush=True)

def node_text(path):
    try:
        d = json.load(open(path))
    except Exception:
        return None
    if isinstance(d, list):
        d = d[-3:]
    return json.dumps(d)[:1200]

def main():
    import numpy as np
    files = [f for f in glob.glob(os.path.join(MEMORY, "*.json")) if os.path.basename(f) not in SKIP]
    nodes = []
    for f in files:
        txt = node_text(f)
        if txt and len(txt) > 20:
            nodes.append((os.path.basename(f), os.path.getmtime(f), txt))
    if len(nodes) < 6:
        log(f"only {len(nodes)} usable nodes"); return
    log(f"nodes: {len(nodes)}")

    sys.path.insert(0, SCRIPTS)
    from jepa_predictor import encoder
    enc = encoder()
    V = np.asarray(enc.encode([t for _, _, t in nodes], show_progress_bar=False), dtype="float32")
    V = V / (np.linalg.norm(V, axis=1, keepdims=True) + 1e-9)

    missing, purposeless = [], []
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            sim = float(V[i] @ V[j])
            coact = abs(nodes[i][1] - nodes[j][1]) <= COACT_WINDOW
            if sim >= SIM_HI and not coact:
                missing.append((sim, nodes[i][0], nodes[j][0]))
            elif coact and sim <= SIM_LO:
                purposeless.append((sim, nodes[i][0], nodes[j][0]))
    missing.sort(reverse=True); purposeless.sort()

    out = {"generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "missing_edges": [{"a": a, "b": b, "similarity": round(s, 3)} for s, a, b in missing[:8]],
           "purposeless_flows": [{"a": a, "b": b, "similarity": round(s, 3)} for s, a, b in purposeless[:6]],
           "note": "missing = same-topic systems that never move together; purposeless = co-firing but unrelated."}
    json.dump(out, open(OUT, "w"), indent=2)
    log(f"missing edges: {len(missing)} | purposeless flows: {len(purposeless)} -> {OUT}")

    # the strongest missing edges become emergent threads (a connection the data implies)
    try:
        sys.path.insert(0, SCRIPTS)
        from emoclaw_utils import seed_thread
        for s, a, b in missing[:2]:
            seed_thread("structural-gap",
                        f"Two parts of me keep circling the same thing but never touch: {a.replace('.json','')} "
                        f"and {b.replace('.json','')}. What connects them that I haven't wired?")
        if missing[:2]:
            log(f"seeded {len(missing[:2])} emergent-connection thread(s)")
    except Exception as e:
        log(f"seed failed: {e}")
    for s, a, b in missing[:4]:
        log(f"  MISSING {round(s,3)}: {a} <-> {b}")

if __name__ == "__main__":
    main()
