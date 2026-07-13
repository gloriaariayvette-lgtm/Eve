#!/usr/bin/env python3
"""velaris_interweave_recon.py — TIGHTLY BOUNDED. Prints only the native consumer entry-points the
new organs should weave into. Named files only, def/signature lines only, hard-capped. No bodies,
no wide grep — will not flood.
"""
import os, re

S = os.path.expanduser("~/.openclaw/workspace/scripts")
M = os.path.expanduser("~/.openclaw/workspace/memory")

# file -> the functions we care about weaving into
WANT = {
    "narrative_identity.py":  ["feed_from_causal_model", "propose_fragment", "get_narrative_context", "get_tone_bias"],
    "self_statements.py":     ["add_statement", "feed", "top_statements", "direction_bias"],
    "pearl_engine.py":        ["add_candidate", "add_proto", "stage", "seal"],
    "emoclaw_utils.py":       ["seed_thread", "set_preoccupation", "add_dream", "seed_dream"],
    "causality_engine.py":    ["form_causal_hypotheses", "load_emotional_trajectory", "find_spikes", "nightly"],
    "subconscious-drift.py":  ["main", "feed", "def "],
    "self_drift.py":          ["main", "record", "def "],
    "second-order-dreamer.py":["main", "def "],
    "narrative-identity.py":  ["feed_from_causal_model", "propose_fragment"],
}

def sigs(path, names, cap=14):
    try: lines = open(path, encoding="utf-8", errors="ignore").read().splitlines()
    except Exception: return ["  (not found)"]
    out, seen = [], 0
    for i, ln in enumerate(lines):
        m = re.match(r"\s*def\s+(\w+)", ln)
        if not m: continue
        fn = m.group(1)
        if any(n == fn or n in fn for n in names) or "def " in names:
            # signature + first docstring line if present
            sig = ln.strip()
            doc = ""
            if i + 1 < len(lines):
                nxt = lines[i + 1].strip()
                if nxt.startswith(('"""', "'''", "#")):
                    doc = "   -> " + nxt.strip('"\'# ')[:80]
            out.append("  %s%s" % (sig[:120], doc))
            seen += 1
            if seen >= cap: out.append("  ...(capped)"); break
    return out or ["  (no matching defs)"]

print("=== Velaris interweave points (bounded) ===\n")
for fname, names in WANT.items():
    p = os.path.join(S, fname)
    if not os.path.exists(p):
        continue
    print("---- %s ----" % fname)
    for l in sigs(p, names):
        print(l)
    print()

# which native memory files already hold the interwoven signals (so we don't fork parallel ones)
print("---- native memory files (causal / drift / dream / pearl / identity) ----")
import glob
for pat in ("*causal*", "*drift*", "*dream*", "*pearl*", "*narrative*identity*", "*self-statement*", "*self_statement*"):
    for f in sorted(glob.glob(os.path.join(M, pat)))[:6]:
        print("  " + f.replace(os.path.expanduser("~"), "~"))
print("\n=== done (bounded) ===")
