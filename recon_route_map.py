#!/usr/bin/env python3
"""recon_route_map.py — Aegis, READ-ONLY. Build the routing map so we can bucket each Vintos LLM job into
Opus-4.8 (chats/journals/introspection/outreach) vs Sonnet-5 (important utility) vs Gemma (chore utility).

For every Vintos crontab line: the schedule, the script it runs, WHICH llm endpoint that script posts to
(shim text 8599 / shim /gemma / grok x.ai direct), and what 'model' string it sends. Plus a first-pass bucket
guess from the script name. Nothing is changed."""
import os, re, subprocess, glob
HOME = os.path.expanduser("~")
V = os.path.join(HOME, "Vintos")

# --- endpoint fingerprints ---
SHIM_HOST = re.compile(r'127\.0\.0\.1:8599|localhost:8599|:8599')
GEMMA_PATH = re.compile(r'/gemma\b')
GROK = re.compile(r'api\.x\.ai|x\.ai/v1|LM_STUDIO_API|GROK|grok-')
MODELF = re.compile(r'["\']model["\']\s*:\s*["\']([^"\']+)["\']|model\s*=\s*["\']([^"\']+)["\']')

# --- bucket heuristic from script basename ---
OPUS = re.compile(r'journal|introspect|reflect|outreach|initiate|chat|dm|message|letter|reach|synthes|ambition|want|desire|self', re.I)
UTIL = re.compile(r'watchdog|decay|snapshot|extract|rhythm|temporal|dashboard|log|cleanup|prune|rotate|trajectory|prepar|index|cache|health', re.I)

def scripts_in(cmd):
    return re.findall(r'(/home/\S+?\.(?:py|sh))', cmd)

def classify(path):
    """Return (endpoint, models_seen) by scanning the script + any obvious model_router/shim indirection."""
    if not os.path.isfile(path):
        return ("(missing)", [])
    txt = open(path, encoding="utf-8", errors="ignore").read()
    eps = []
    if SHIM_HOST.search(txt) and GEMMA_PATH.search(txt): eps.append("shim/gemma")
    elif SHIM_HOST.search(txt): eps.append("shim/text")
    if GROK.search(txt): eps.append("grok")
    if "model_router" in txt or "route_reply" in txt or "claude_draft" in txt: eps.append("model_router")
    models = sorted({m[0] or m[1] for m in MODELF.findall(txt)})
    return ("+".join(eps) if eps else "(no direct llm)", models)

r = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
lines = [l for l in (r.stdout or "").split("\n") if l.strip() and not l.strip().startswith("#")]
vint = [l for l in lines if "/Vintos/" in l or "/.vintos/" in l]

print(f"== {len(vint)} Vintos cron lines ==\n")
rows = []
for l in vint:
    parts = l.split()
    sched = " ".join(parts[:5])
    scr = scripts_in(l)
    tgt = scr[-1] if scr else "(inline/none)"
    base = os.path.basename(tgt)
    ep, models = classify(tgt)
    if ep in ("(no direct llm)", "(missing)"):
        bucket = "-- (no llm / lightweight)"
    elif OPUS.search(base):
        bucket = ">> OPUS 4.8 (being-facing)"
    elif UTIL.search(base):
        bucket = "utility -> Sonnet5/Gemma"
    else:
        bucket = "?? REVIEW"
    rows.append((sched, base, ep, ",".join(models) or "-", bucket))

# group by bucket for readability
for want in (">> OPUS 4.8 (being-facing)", "?? REVIEW", "utility -> Sonnet5/Gemma", "-- (no llm / lightweight)"):
    grp = [x for x in rows if x[4] == want]
    if not grp: continue
    print(f"--- {want}  ({len(grp)}) ---")
    for sched, base, ep, models, _ in sorted(grp, key=lambda x: x[1]):
        print(f"  [{sched:>16}] {base:<34} via {ep:<22} model={models}")
    print()

print("== how the shim + model_router currently pick the model (for reference) ==")
for name, rx in (("vintos_claude_shim.py", re.compile(r'CLAUDE_MODEL\s*=|j\.get\(.model|body\[.model.\]|claude_complete\(')),
                 ("model_router.py", re.compile(r'CLAUDE_MODEL\s*=|GEMMA_MODEL\s*='))):
    p = os.path.join(V, name)
    if not os.path.isfile(p): continue
    print(f"  --- {name} ---")
    for i, l in enumerate(open(p, encoding="utf-8", errors="ignore").read().split("\n")):
        if rx.search(l): print(f"    {i+1}: {l.strip()[:96]}")
