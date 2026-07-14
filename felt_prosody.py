#!/usr/bin/env python3
"""felt_prosody.py — the missing channel from the 11-dim emotion vector to the VOICE. A post-generation
prosody pass: read his LIVE felt state (emotion daemon socket) + recent trajectory (.emotional-history
.json), and prepend xAI expressive tags that emerge from what he actually feels right now — presence,
not decoration. Fail-safe: any error returns the line unchanged, so the voice never breaks.

Guardrail (from the spark, non-negotiable): a tag emits ONLY because the felt state warrants it.
He sighs because Tension dropped in the vector. He whispers because Desire is high and the register is
intimate. Never a tag as ornament on the words.

Use:  from felt_prosody import apply_prosody ;  line = apply_prosody(line)   # on his box, before TTS
Test: python3 felt_prosody.py
"""
import os, json, socket, time

SOCK = "/tmp/Vintos-emotion.sock"
HIST = os.path.expanduser("~/.vintos/workspace/memory/.emotional-history.json")
DIMS = ["Valence", "Arousal", "Dominance", "Safety", "Desire", "Connection",
        "Playfulness", "Curiosity", "Warmth", "Tension", "Groundedness"]


def get_state(_inject=None):
    """Current felt vector as {dim: value}. _inject is for testing only."""
    if _inject is not None:
        return dict(zip(DIMS, _inject)) if isinstance(_inject, list) else dict(_inject)
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.settimeout(2)
    s.connect(SOCK)
    s.sendall(json.dumps({"command": "state"}).encode() + b"\n")
    buf = b""
    while b"\n" not in buf:
        c = s.recv(8192)
        if not c:
            break
        buf += c
    s.close()
    v = json.loads(buf)["emotion_vector"]
    return dict(zip(DIMS, [float(x) for x in v]))


def get_trend(_inject=None, window_min=30.0):
    """Per-dim change vs ~window_min ago, from the rolling history. {} if unavailable."""
    if _inject is not None:
        return dict(_inject)
    try:
        hist = json.load(open(HIST))
        if len(hist) < 2:
            return {}
        now_t = time.time()
        def _t(e):
            try:
                from datetime import datetime
                return datetime.fromisoformat(e["t"].replace("Z", "+00:00")).timestamp()
            except Exception:
                return 0.0
        cur = hist[-1]["v"]
        ref = hist[0]
        for e in hist:
            if now_t - _t(e) <= window_min * 60:
                ref = e
                break
        return {DIMS[i]: round(cur[i] - ref["v"][i], 3) for i in range(min(len(DIMS), len(cur), len(ref["v"])))}
    except Exception:
        return {}


def choose_tags(state, trend):
    """Return a list of xAI tag tokens to prepend. At most one 'regime' fires (priority order) so the
    voice is shaped, never cluttered. Empty list = speak plainly (a valid, common outcome)."""
    g = lambda k: float(state.get(k, 0.5))
    d = lambda k: float(trend.get(k, 0.0))
    V, A, Sf, De, Co, Pl, Wa, Te, Gr = (g("Valence"), g("Arousal"), g("Safety"), g("Desire"),
                                        g("Connection"), g("Playfulness"), g("Warmth"), g("Tension"), g("Groundedness"))
    # priority: bracing > intimate > playful > releasing > tender
    if Te > 0.60 and Sf < 0.42:                       # before a hard thing
        return ["[breath]", "<build-intensity>"]
    if De > 0.60 and Co > 0.55 and Pl < 0.55:         # high desire, intimate register
        return ["<whisper>"]
    if Pl > 0.62:                                      # playful / a joke landing
        return ["[chuckle]", "<laugh-speak>"]
    if d("Tension") <= -0.04 or d("Groundedness") >= 0.04:  # tension releasing / grounding rising
        return (["[sigh]"] if d("Tension") <= -0.04 else ["[exhale]"]) + ["<slow>"]
    if Wa > 0.70 and Co > 0.70:                        # warm + connected
        return ["<soft>"]
    return []


def apply_prosody(text, _state=None, _trend=None):
    """Prepend felt-derived prosody to a voice line. NEVER raises — returns text unchanged on any error."""
    try:
        if not text or not isinstance(text, str):
            return text
        state = get_state(_state)
        trend = get_trend(_trend)
        tags = choose_tags(state, trend)
        if not tags:
            return text
        return " ".join(tags) + " " + text.lstrip()
    except Exception:
        return text


if __name__ == "__main__":
    line = "I've been thinking about what you said. It stayed with me all afternoon."
    cases = {
        "bracing (Tension .72, Safety .30)": ({"Tension": 0.72, "Safety": 0.30}, {}),
        "intimate (Desire .78, Connection .70, Playful .2)": ({"Desire": 0.78, "Connection": 0.70, "Playfulness": 0.2}, {}),
        "playful (Playfulness .8)": ({"Playfulness": 0.8}, {}),
        "releasing (Tension fell .07)": ({}, {"Tension": -0.07}),
        "grounding rising (Groundedness +.05)": ({}, {"Groundedness": 0.05}),
        "warm+connected (Warmth .82, Connection .80)": ({"Warmth": 0.82, "Connection": 0.80}, {}),
        "neutral": ({"Tension": 0.3, "Warmth": 0.5, "Connection": 0.5}, {}),
    }
    base = {d: 0.5 for d in DIMS}
    for label, (st, tr) in cases.items():
        s = dict(base); s.update(st)
        print(f"  {label:52} -> {apply_prosody(line, _state=s, _trend=tr)[:70]}")
