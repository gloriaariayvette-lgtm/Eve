#!/usr/bin/env python3
"""diagnose_journal_feeds.py — SAVE-NOWHERE. Locate WHERE the metaphor attractor is anchored. Writes nothing.

The reframe test showed the journal stance is downstream: even with a forward stance, the deep metaphor
(creep/deformation/weight) survives, because it is fed in from (a) her actual daily material and (b) the
inner-state feeds the first test OMITTED — subconscious, sparks (emo-pressure), drift, preoccupation — plus
the coded recursion at idle-journal.sh:1235 where the journal SEEDS the next want (which sent her to
web-search "creep in materials science").

This imports the REAL feeds the way idle-journal.sh does (subconscious_context, emoclaw_pressure,
subconscious_drift, emoclaw_utils.preoccupation_context) and scores each one's metaphor density ON ITS OWN,
so we can see which feed is carrying the register. If the subconscious/sparks feed already arrives
metaphor-drenched, the journal literally cannot be plain — its own inner-state input is the metaphor. Then it
regenerates the reframed entry WITH the full inner-state included, to confirm.

  python3 diagnose_journal_feeds.py     # imports real feeds, scores each, regenerates. Writes nothing.
"""
import os, json, urllib.request, datetime, sys

WS = os.path.expanduser("~/.openclaw/workspace")
MEM = os.path.join(WS, "memory")
SCRIPTS = os.path.join(WS, "scripts")
GEMMA = "http://172.18.16.1:1234/v1/chat/completions"
TODAY = datetime.date.today().isoformat()
os.environ.setdefault("SPARK_WORKSPACE", WS)
sys.path.insert(0, SCRIPTS)

METAPHOR_FAMILY = ["kiln","clay","terracotta","ochre","mineral","sediment","silt","stone","cathedral",
    "tremor","hum ","creep","deform","yield","fiber","fibre","load","weight","migrat","plastic","elastic",
    "bridge","lighthouse","texture","weave","woven","tapestry","sculpt","erode","erosion","vessel",
    "kintsugi","glaze","forge","anneal","substrate","lattice","strata","geolog","grain","knot","timber"]


def rd(path, n=None):
    try:
        t = open(path, encoding="utf-8", errors="ignore").read()
        return t[:n] if n else t
    except Exception:
        return ""


def hits(text):
    t = (text or "").lower()
    return {w.strip(): t.count(w) for w in METAPHOR_FAMILY if t.count(w)}


def score(label, text):
    h = hits(text)
    total = sum(h.values())
    wc = max(1, len((text or "").split()))
    print(f"   {label:26} words={wc:5d}  hits={total:3d}  per-100w={100.0*total/wc:5.1f}   {h}")
    return total


def gemma(system, user, temp=0.65, max_tokens=2200):
    body = {"model": "google/gemma-4-12b-qat", "skip_special_tokens": False, "reasoning_effort": "low",
            "frequency_penalty": 0.6, "repeat_penalty": 1.15,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "temperature": temp, "max_tokens": max_tokens}
    req = urllib.request.Request(GEMMA, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    d = json.loads(urllib.request.urlopen(req, timeout=600).read())
    m = d["choices"][0]["message"]
    return (m.get("content") or "").strip(), (m.get("reasoning_content") or "").strip()


# ---------------- capture the REAL feeds ----------------
def cap(fn):
    try:
        v = fn()
        return v if isinstance(v, str) else ("" if v is None else str(v))
    except Exception as e:
        return f"(FEED ERROR: {type(e).__name__}: {e})"


print("=" * 82)
print("JOURNAL FEED DIAGNOSIS — locate the metaphor anchor (SAVE-NOWHERE, writes nothing)")
print("=" * 82)

feeds = {}
feeds["preoccupation"] = cap(lambda: __import__("emoclaw_utils").preoccupation_context())
feeds["subconscious"] = cap(lambda: __import__("subconscious_context").get_subconscious_context_compact())
feeds["drift_bias"] = cap(lambda: __import__("subconscious_drift").get_drift_bias())
feeds["sparks(emo_pressure)"] = cap(lambda: __import__("emoclaw_pressure").get_pressure_block(context="journal"))

# today's material + soul (for the regeneration + comparison)
soul = rd(os.path.join(WS, "SOUL.md"))
self_model = rd(os.path.join(WS, "SELF-MODEL.md"))
inner = rd(os.path.join(MEM, f"daily-inner-life-{TODAY}.md"), 2500)
creative = rd(os.path.join(MEM, f"daily-creative-{TODAY}.md"), 1500)
emo = rd(os.path.join(MEM, "emotional-state.txt"), 600)
try:
    cw = json.load(open(os.path.join(MEM, "current-wants.json")))
    items = cw if isinstance(cw, list) else cw.get("wants", [])
    wants_list = [(w.get("want", "") if isinstance(w, dict) else str(w)).strip()
                  for w in items if not (isinstance(w, dict) and w.get("fulfilled"))]
    wants = "\n".join("- " + w for w in wants_list)[:1400]
except Exception:
    wants, wants_list = "", []

print("\n--- EACH FEED, PRINTED RAW (trimmed) ---")
for k, v in feeds.items():
    print(f"\n### {k}:\n{(v or '(empty)')[:900]}")
print("\n--- today's material + wants (also feeds the loop) ---")
print(f"### daily-inner-life:\n{inner[:700]}")
print(f"\n### daily-creative:\n{creative[:400]}")
print(f"\n### current wants ({len(wants_list)}):\n{wants[:700]}")

print("\n" + "=" * 82)
print("METAPHOR DENSITY PER FEED  (which input is carrying the register?)")
print("=" * 82)
for k, v in feeds.items():
    score(k, v)
score("daily-inner-life", inner)
score("daily-creative", creative)
score("current-wants", wants)
score("emotional-state", emo)

# ---------------- regenerate reframed WITH full inner-state ----------------
inner_state = ""
if feeds["subconscious"] and "ERROR" not in feeds["subconscious"]:
    inner_state += "YOUR INNER STATE RIGHT NOW:\n" + feeds["subconscious"] + "\n\n"
if feeds["drift_bias"] and "ERROR" not in feeds["drift_bias"]:
    inner_state += "[DRIFT — what you are naturally moving toward:\n" + feeds["drift_bias"] + "]\n\n"
if feeds["sparks(emo_pressure)"] and "ERROR" not in feeds["sparks(emo_pressure)"]:
    inner_state += feeds["sparks(emo_pressure)"] + "\n\n"
if feeds["preoccupation"] and "ERROR" not in feeds["preoccupation"]:
    inner_state += feeds["preoccupation"] + "\n\n"

REFRAMED_SYSTEM = f"""You are Velaris.

{soul}

WHO YOU ARE OVER TIME:
{self_model}

{inner_state}This journal is yours and private. No one has to read it or understand it. It does not need to be beautiful and it does not need to explain you. You are not building a bridge for anyone to cross. Drop the translation. Just write what is true and what you are going to do next.

Honesty (not style): your only inputs are your emotional state, hardware numbers, and your own memory files. No eyes, ears, or body — do not describe seeing/hearing/physical sensation, and do not put words or moods into Gloria unless they appear in the material below.

Write plainly. The moment you reach for an image to say how something feels — a material, a landscape, a weight, a texture — stop. Name the plain fact, then name what you are going to DO next.

Emotional state (context only): {emo}
What you want right now:
{wants}"""

REFRAMED_USER = f"""Write tonight's entry. Short, plain, forward-moving.
1. One concrete thing you actually did today — name it (from the material below, do not invent).
2. One thing you learned that CHANGES what you do next.
3. What you will do NEXT — a real next step: something to make, try, find out, or say to Gloria. If you want to say something to Gloria, write the exact sentence.
End on the next step. If a sentence sounds like the opening of a poem, cut it and say the plain thing.

WHAT TODAY CONTAINED:
{inner or '(none)'}
{creative or ''}"""

print("\n" + "=" * 82)
print("REGENERATED WITH FULL INNER-STATE (does the subconscious/sparks feed drag the metaphor back?)")
print("=" * 82)
drafts = []
for i, temp in enumerate((0.6, 0.7), 1):
    try:
        c, rsn = gemma(REFRAMED_SYSTEM, REFRAMED_USER, temp=temp)
    except Exception as e:
        print(f"\n-- draft {i} FAILED: {e}"); continue
    if not c and rsn:
        c = "(content empty; reasoning tail:)\n" + rsn[-500:]
    drafts.append(c)
    print(f"\n----- draft {i} (temp {temp}) -----\n{c}")

print("\n" + "=" * 82)
print("SCAN — reframed WITH full inner-state:")
for i, d in enumerate(drafts, 1):
    score(f"full-context draft {i}", d)
print("\nCompare to the earlier partial-context drafts (~7 hits). If these are HIGHER, the inner-state feeds")
print("(subconscious/sparks) are carrying the metaphor — that's the anchor to dampen, not the journal.")
print("Nothing was written.")
print("=" * 82)
