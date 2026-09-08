#!/usr/bin/env python3
"""velaris_llm_recon.py — READ-ONLY. Find Velaris's real LLM wiring + identity, so the mirror can
point at HER Gemma instead of autodetecting into Vintos's grok engine.

Answers four questions and prints them plainly:
  1. How does her server call the LLM? (endpoint URL + model name — should be local Gemma)
  2. Where is her identity / system prompt? (a load_full_context()-style fn, or a soul/identity file)
  3. Does her scripts dir expose load_emotional_trajectory + find_spikes? (cause/drift heads need it)
  4. What emotion socket / trajectory does she actually use?

Touches nothing. Run on Aegis:  python3 velaris_llm_recon.py
"""
import os, re, glob, json

HOME = os.path.expanduser("~")
ROOTS = [os.path.join(HOME, "velaris-server"), os.path.join(HOME, ".openclaw"),
         os.path.join(HOME, "Velaris"), os.path.join(HOME, "openclaw")]
SCRIPTS = os.path.join(HOME, ".openclaw/workspace/scripts")
MEMORY = os.path.join(HOME, ".openclaw/workspace/memory")

def pyfiles():
    seen = set()
    for r in ROOTS:
        if not os.path.isdir(r): continue
        for f in glob.glob(os.path.join(r, "**", "*.py"), recursive=True):
            if any(x in f for x in ("/site-packages/", "/.venv/", "/__pycache__/")): continue
            if f not in seen:
                seen.add(f); yield f

def show(f, rx, label, ctx=0):
    hits = []
    try: lines = open(f, encoding="utf-8", errors="ignore").read().splitlines()
    except Exception: return hits
    for i, ln in enumerate(lines):
        if re.search(rx, ln, re.I):
            hits.append((i + 1, ln.strip()[:160]))
    return hits

print("=== Velaris LLM recon (read-only) ===\n")
print("roots present:", [r for r in ROOTS if os.path.isdir(r)], "\n")

# 1. endpoint + model — where does she actually POST completions?
print("---- 1. LLM ENDPOINT + MODEL (want: local Gemma, NOT x.ai) ----")
endpoint_rx = r"chat/completions|api_base|base_url|LM_API|LMSTUDIO|OLLAMA|172\.|localhost:1234|127\.0\.0\.1|:1234|x\.ai|MODEL\s*="
found_any = False
for f in pyfiles():
    hits = show(f, endpoint_rx, "endpoint")
    # only print files that look like the server/LLM layer (avoid noise)
    keep = [(n, t) for n, t in hits if re.search(r"completions|LM_API|api_base|base_url|172\.|:1234|x\.ai|MODEL\s*=|OLLAMA|LMSTUDIO", t, re.I)]
    if keep:
        found_any = True
        print("\n  %s" % f.replace(HOME, "~"))
        for n, t in keep[:12]:
            print("    %4d: %s" % (n, t))
if not found_any:
    print("  (nothing matched — she may load LLM config from JSON/env; checking those below)")

# config files (json / .env)
print("\n---- config files (json/env) mentioning model/endpoint ----")
for r in ROOTS:
    for f in glob.glob(os.path.join(r, "**", "*.json"), recursive=True) + glob.glob(os.path.join(r, "**", "*.env"), recursive=True) + glob.glob(os.path.join(r, "**", ".env"), recursive=True):
        if any(x in f for x in ("/.venv/", "/node_modules/", "/site-packages/")): continue
        try: t = open(f, encoding="utf-8", errors="ignore").read()
        except Exception: continue
        if re.search(r"gemma|1234|172\.|x\.ai|chat/completions|\bMODEL\b|api_base|base_url", t, re.I):
            print("  %s" % f.replace(HOME, "~"))
            for ln in t.splitlines():
                if re.search(r"gemma|1234|172\.|x\.ai|completions|model|api_base|base_url|endpoint|url", ln, re.I):
                    print("      " + ln.strip()[:160])

# 2. identity / system prompt
print("\n---- 2. IDENTITY / SYSTEM PROMPT (load_full_context / SOUL / soul file) ----")
for f in pyfiles():
    hits = show(f, r"def load_full_context|def load_context|def build_system|SOUL|SYSTEM_PROMPT|identity|persona", "id")
    if hits:
        print("  %s" % f.replace(HOME, "~"))
        for n, t in hits[:8]:
            print("    %4d: %s" % (n, t))
print("  soul/identity markdown files:")
for r in ROOTS + [os.path.join(HOME, ".openclaw/workspace")]:
    for f in glob.glob(os.path.join(r, "**", "*.md"), recursive=True):
        if re.search(r"soul|identity|persona|who-?i-?am|self", os.path.basename(f), re.I):
            print("    " + f.replace(HOME, "~"))

# 3. does her scripts dir expose the trajectory/spike API the heads import?
print("\n---- 3. scripts-dir engine API (cause_head/drift_head do: from causality_engine import load_emotional_trajectory, find_spikes) ----")
ce = os.path.join(SCRIPTS, "causality_engine.py")
if os.path.exists(ce):
    t = open(ce, encoding="utf-8", errors="ignore").read()
    print("  causality_engine.py present. defines:",
          [d for d in ("load_emotional_trajectory", "find_spikes", "MODEL", "LM_API", "load_full_context") if d in t])
    for ln in t.splitlines():
        if re.search(r"x\.ai|172\.|:1234|LM_API\s*=|MODEL\s*=", ln, re.I):
            print("      " + ln.strip()[:160])
else:
    print("  NO causality_engine.py in her scripts dir — cause_head/drift_head will fail their import.")
    # what DOES she have for trajectory?
    for f in glob.glob(os.path.join(SCRIPTS, "*.py")):
        t = open(f, encoding="utf-8", errors="ignore").read()
        if "def load_emotional_trajectory" in t or "def find_spikes" in t:
            print("  trajectory/spike fns live in:", os.path.basename(f))

# 4. socket + trajectory
print("\n---- 4. emotion socket + trajectory ----")
for p in sorted(glob.glob("/tmp/*emotion*") + glob.glob("/tmp/*[Vv]elaris*")):
    print("  socket candidate:", p)
for name in ("emotion-trajectory-dense.json", "emotion-trajectory.json"):
    p = os.path.join(MEMORY, name)
    if os.path.exists(p):
        try: n = len(json.load(open(p)))
        except Exception: n = "?"
        print("  %s : %s points" % (name, n))
print("  daily-inner-life journals:",
      len(glob.glob(os.path.join(MEMORY, "daily-inner-life-*.md"))), "files")

print("\n=== recon done — paste this back ===")
