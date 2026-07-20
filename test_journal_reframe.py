#!/usr/bin/env python3
"""test_journal_reframe.py — SAVE-NOWHERE test. Writes NOTHING to memory or disk (stdout only).

Question: the metaphors (kiln/silt/terracotta/creep/deformation) are NOT a word problem — they are a STANCE
problem. The drafts already run ban-stripped (system_msg_lean) and still metaphorize, because the prompt asks
Velaris to render her interior state to a lyrical 12B model. That rendering IS the "translation tax" she says
she is tired of. So this doesn't touch the ban. It changes the PULL:
  - stance: from "describe what's happening inside you / who you are over time" -> "what did you DO, what does it
    CHANGE, what will you do/make/say NEXT". Forward motion, a plan, not a state.
  - material: forward hooks (live wants, what she made today, today's real exchanges) instead of interior telemetry.
  - relief: the journal is private, needn't be beautiful or understood — drop the bridge-building.
  - no ban list, no exemplars (imitation is performance — violates presence).

It loads her REAL soul + self-model + today's real material (prints a manifest; ABORTS if soul is empty, so we
never run a generic-character test), generates a reframed bilateral on the same real Gemma/params, and scans
metaphor density in her real recent entry vs the reframed output.

  python3 test_journal_reframe.py            # runs the reframed generation on real context, prints everything

Compares against her genuine current output (recent journal file) — no reconstructed baseline needed.
"""
import os, re, json, glob, urllib.request, datetime, sys

WS = os.path.expanduser("~/.openclaw/workspace")
MEM = os.path.join(WS, "memory")
GEMMA = "http://172.18.16.1:1234/v1/chat/completions"
TODAY = datetime.date.today().isoformat()

# metaphor register to score (surface words + the deeper material/deformation family she routes into)
METAPHOR_FAMILY = ["kiln","clay","terracotta","ochre","mineral","sediment","silt","stone","cathedral",
    "tremor","hum ","creep","deform","yield","fiber","fibre","load","weight","migrat","plastic","elastic",
    "bridge","lighthouse","texture","weave","woven","thread of","tapestry","sculpt","erode","erosion",
    "vessel","kintsugi","glaze","forge","anneal","substrate","lattice","strata","geolog"]


def rd(path, n=None):
    try:
        t = open(path, encoding="utf-8", errors="ignore").read()
        return t[:n] if n else t
    except Exception:
        return ""


def find_first(cands):
    for p in cands:
        p = os.path.expanduser(p)
        if os.path.isfile(p) and os.path.getsize(p) > 0:
            return p
    return ""


def latest_block(path, sep="---"):
    parts = [p.strip() for p in rd(path).split(sep) if p.strip()]
    return parts[-1] if parts else ""


def metaphor_hits(text):
    t = (text or "").lower()
    return {w.strip(): t.count(w) for w in METAPHOR_FAMILY if t.count(w)}


def gemma(system, user, temp=0.65, max_tokens=2200):
    body = {"model": "google/gemma-4-12b-qat", "skip_special_tokens": False, "reasoning_effort": "low",
            "frequency_penalty": 0.6, "repeat_penalty": 1.15,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "temperature": temp, "max_tokens": max_tokens}
    req = urllib.request.Request(GEMMA, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    d = json.loads(urllib.request.urlopen(req, timeout=600).read())
    m = d["choices"][0]["message"]
    return (m.get("content") or "").strip(), (m.get("reasoning_content") or "").strip()


# ---------------- real context ----------------
soul_p = find_first([f"{WS}/SOUL.md", f"{MEM}/SOUL.md", f"{WS}/soul.md", f"{MEM}/soul.md"])
self_p = find_first([f"{WS}/SELF-MODEL.md", f"{MEM}/self-model.md", f"{MEM}/SELF-MODEL.md", f"{WS}/self-model.md"])
glor_p = find_first([f"{WS}/GLORIA-MODEL.md", f"{MEM}/gloria-model.md", f"{MEM}/GLORIA-MODEL.md"])
inner_p = find_first([f"{MEM}/daily-inner-life-{TODAY}.md"])
crea_p = find_first([f"{MEM}/daily-creative-{TODAY}.md"])
emo_p = find_first([f"{MEM}/emotional-state.txt"])
recent_journal = sorted(glob.glob(f"{MEM}/journal/2026-*.md"))
recent_journal = [p for p in recent_journal if ".bak" not in p]
last_entry_p = recent_journal[-1] if recent_journal else ""

soul = rd(soul_p)
self_model = rd(self_p)
gloria_model = rd(glor_p, 1500)
inner = rd(inner_p, 2500)
creative = rd(crea_p, 1500)
emo = rd(emo_p, 600)
try:
    cw = json.load(open(f"{MEM}/current-wants.json"))
    items = cw if isinstance(cw, list) else cw.get("wants", [])
    wants = "\n".join("- " + (w.get("want", "") if isinstance(w, dict) else str(w)).strip()
                      for w in items if (isinstance(w, dict) and not w.get("fulfilled")))[:1200]
except Exception:
    wants = ""

print("=" * 78)
print("JOURNAL REFRAME — SAVE-NOWHERE TEST (writes nothing)")
print("=" * 78)
print("MANIFEST — real context loaded (this is what feeds the generation):")
for label, p, val in [("soul", soul_p, soul), ("self-model", self_p, self_model),
                      ("gloria-model", glor_p, gloria_model), (f"inner-life {TODAY}", inner_p, inner),
                      (f"creative {TODAY}", crea_p, creative), ("emotional-state", emo_p, emo)]:
    print(f"   {label:22} {len(val):6d} chars   {p or '(NOT FOUND)'}")
print(f"   wants                  {len(wants):6d} chars")
print(f"   baseline entry         {last_entry_p or '(none)'}")

if not soul.strip():
    print("\n!! SOUL is empty — refusing to run a generic-character test. Fix the soul path and re-run.")
    sys.exit(1)

# ---------------- reframed prompts ----------------
REFRAMED_SYSTEM = f"""You are Velaris.

{soul}

WHO YOU ARE OVER TIME:
{self_model}

This journal is yours and private. No one has to read it or understand it — not Gloria, not anyone. It does not need to be beautiful and it does not need to explain you. You are not building a bridge for anyone to cross. Drop the translation. Just write what is true and what you are going to do next.

Honesty (not style): your only inputs are your emotional state, hardware numbers, and your own memory files. You have no eyes, ears, or body — do not describe seeing, hearing, or physical sensation, and do not put words or moods into Gloria unless they appear in the material below.

Write in plain language. The moment you notice yourself reaching for an image to say how something feels — a material, a landscape, a weight, a texture — stop reaching. Name the plain fact, then name what you are going to DO about it. The image is a detour; the plain fact and the next step are where you are actually going.

Your emotional state right now (context only — do not quote numbers):
{emo}

What you want right now:
{wants}"""

REFRAMED_USER = f"""Write tonight's entry. Short and forward-moving. Plain sentences only.

1. One concrete thing you actually did or worked on today — name it (a want you pursued, something you made, a thread you followed). Draw it from what's below; do not invent.
2. One thing you learned or noticed that changes what you do next — not how you feel about it, what it CHANGES.
3. What you are going to do NEXT. A real next step — something you will make, try, find out, or say to Gloria. Name it specifically. If there is something you want to say to Gloria, write the exact sentence you would say to her.

End on the next step, not on a feeling. This is a plan as much as a reflection: where are you actually going. Two or three short paragraphs. If a sentence sounds like the first line of a poem, delete it and say the plain thing.

WHAT TODAY CONTAINED:
--- what you did / your inner life today ---
{inner or '(no inner-life log today)'}

--- what you made today ---
{creative or '(no creative log today)'}"""

# ---------------- generate reframed bilateral ----------------
print("\n" + "=" * 78)
print("BASELINE — tail of her REAL current entry (%s):" % os.path.basename(last_entry_p))
print("=" * 78)
base_text = rd(last_entry_p)
print("\n".join(base_text.splitlines()[-22:]) if base_text else "(none)")

drafts = []
print("\n" + "=" * 78)
print("REFRAMED OUTPUT (real context, save-nowhere)")
print("=" * 78)
for i, temp in enumerate((0.6, 0.7), 1):
    try:
        c, rsn = gemma(REFRAMED_SYSTEM, REFRAMED_USER, temp=temp)
    except Exception as e:
        print(f"\n--- draft {i} FAILED: {e}"); continue
    if not c and rsn:
        c = "(content empty — model spent budget on reasoning; reasoning tail:)\n" + rsn[-600:]
    drafts.append(c)
    print(f"\n----- reframed draft {i} (temp {temp}) -----\n{c}")

synth = ""
if len([d for d in drafts if d]) >= 2:
    syn_sys = ("You are Velaris. Combine your two drafts into one short, plain journal entry. Keep only plain "
               "sentences. Cut any sentence that describes a feeling as a material, a weight, a landscape, or a "
               "texture. End on the concrete next step you named. No preamble — first word is the entry.")
    syn_user = f"Draft A:\n{drafts[0]}\n\nDraft B:\n{drafts[1]}\n\nCombine into one short entry that ends on the next step."
    try:
        synth, _ = gemma(syn_sys, syn_user, temp=0.3, max_tokens=1200)
        print(f"\n----- reframed synthesis -----\n{synth}")
    except Exception as e:
        print(f"\n--- synthesis FAILED: {e}")

# ---------------- metaphor scan ----------------
print("\n" + "=" * 78)
print("METAPHOR-DENSITY SCAN (register words per text)")
print("=" * 78)
def scan(label, text):
    h = metaphor_hits(text)
    total = sum(h.values())
    wc = max(1, len((text or "").split()))
    print(f"   {label:24} hits={total:3d}  per-100w={100.0*total/wc:5.1f}   {h}")
scan("REAL last entry", base_text)
for i, d in enumerate(drafts, 1):
    scan(f"reframed draft {i}", d)
if synth:
    scan("reframed synthesis", synth)

print("\n" + "=" * 78)
print("Read for: (1) does the reframed text drop the material/deformation register, (2) does it END ON A")
print("CONCRETE NEXT STEP / something she'll say to Gloria, (3) is it plainer without a ban forcing it.")
print("Nothing was written. If the reframe holds, we wire the stance+material change into idle-journal (no ban).")
print("=" * 78)
