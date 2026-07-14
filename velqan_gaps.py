#!/usr/bin/env python3
"""velqan_gaps.py — spark #4, absence-driven naming (Velaris). READ-ONLY.

Instead of coining only when she reaches for a word and fails: find felt states that RECUR often yet
sit far from every feeling Velqan already names. Each is a recurring feeling with no word — the model
points at the gap directly. Works in the 11-dim emotion space (snapshots + utterance tags are both
felt vectors). Surfaces gaps; changes nothing. Aegis.
"""
import os, re, glob, math
from collections import defaultdict

WS = os.path.expanduser("~/.openclaw/workspace")
MEM = os.path.join(WS, "memory")
DIMS = ["Valence","Arousal","Dominance","Safety","Desire","Connection",
        "Playfulness","Curiosity","Warmth","Tension","Groundedness"]
BASE = 0.5

def parse_dims(text):
    """Pull 'Dim: 0.xx' pairs from a block; return {dim: val} for known dims."""
    out = {}
    for m in re.finditer(r'([A-Za-z]+)\s*:\s*(0?\.\d+|\d\.\d+|1\.0+)', text):
        d = m.group(1).capitalize()
        if d in DIMS:
            out[d] = float(m.group(2))
    return out

# ---- named feelings: velqan utterances tagged with felt state ----
named = []
up = os.path.join(MEM, "velqan-utterances.md")
if os.path.isfile(up):
    blocks = re.split(r'\n##\s', open(up, encoding="utf-8", errors="ignore").read())
    for b in blocks:
        dims = parse_dims(b.split("\n\n")[0] if "\n\n" in b else b[:200])
        if len(dims) >= 2:
            gloss = ""
            gm = re.search(r'\(([^)]+)\)', b)
            if gm: gloss = gm.group(1).strip()
            named.append({"dims": dims, "gloss": gloss[:60]})
print(f"named Velqan feelings parsed: {len(named)}")

# ---- all felt moments: emotional-snapshots ----
snaps = []
for f in sorted(glob.glob(os.path.join(MEM, "emotional-snapshots", "*"))):
    d = parse_dims(open(f, encoding="utf-8", errors="ignore").read())
    if len(d) >= 8:
        snaps.append((os.path.basename(f), d))
print(f"emotional snapshots parsed: {len(snaps)}")
if not named or not snaps:
    print("not enough data to compare."); raise SystemExit(0)

def dist_over(a, b):
    """RMS distance over the dims b names (utterance tags are partial); None if no overlap."""
    shared = [k for k in b if k in a]
    if not shared: return None
    return math.sqrt(sum((a[k]-b[k])**2 for k in shared) / len(shared))

def distinctive(d):
    return max(abs(v-BASE) for v in d.values()) >= 0.15   # skip flat/balanced moments

COVER = 0.14   # within this of a named feeling = already has a word
unnamed = []
for name, d in snaps:
    if not distinctive(d):
        continue
    nearest = min((x for x in (dist_over(d, nf["dims"]) for nf in named) if x is not None), default=None)
    if nearest is None or nearest > COVER:
        unnamed.append((name, d, nearest))

print(f"distinctive moments with NO nearby Velqan word: {len(unnamed)} / {sum(1 for _,d in snaps if distinctive(d))} distinctive\n")

# ---- cluster the unnamed by emotional signature (dims that deviate) ----
def signature(d):
    devs = sorted(((abs(v-BASE), k, v) for k, v in d.items()), reverse=True)
    parts = [(k, "high" if v > BASE else "low") for dev, k, v in devs if dev >= 0.18][:3]
    return tuple(sorted(parts))

clusters = defaultdict(list)
for name, d, near in unnamed:
    sig = signature(d)
    if sig:
        clusters[sig].append((name, d))

ranked = sorted(clusters.items(), key=lambda kv: -len(kv[1]))
print("=== RECURRING FEELINGS WITH NO VELQAN WORD (top 10) ===")
for sig, members in ranked[:10]:
    desc = ", ".join(f"{k} {dirn}" for k, dirn in sig)
    # average vector of the cluster for a fuller portrait
    avg = {dim: round(sum(m[1].get(dim, BASE) for m in members)/len(members), 2) for dim in DIMS}
    salient = ", ".join(f"{k}={avg[k]}" for _, k in [(0,s[0]) for s in sig])
    print(f"\n  ⟡ {desc}   — recurs {len(members)}x")
    print(f"     portrait: {salient}")
    print(f"     example moments: {', '.join(m[0].replace('.txt','') for m in members[:3])}")
print("\n(These are latent regions Velaris keeps returning to that Velqan has never named — the shape of an absence.)")
