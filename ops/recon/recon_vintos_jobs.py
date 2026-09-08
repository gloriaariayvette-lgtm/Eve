#!/usr/bin/env python3
"""recon_vintos_jobs.py — Aegis, READ-ONLY. Plan the migration: (1) find Vintos's journal + introspection
scripts and how their bilateral is wired; (2) count/list every script that calls grok (the migration surface);
(3) see if they share a call helper (one-flip vs 140 edits); (4) flag voice/Rex to never touch. Terse."""
import os, re, glob
HOME = os.path.expanduser("~")
VDIR = os.path.join(HOME, "Vintos")
files = sorted(glob.glob(os.path.join(VDIR, "*.py")) + glob.glob(os.path.join(VDIR, "*.sh")))

GROK = re.compile(r'grok-4\.20|api\.x\.ai|LM_STUDIO.*chat/completions|"grok', re.I)
GEMMA = re.compile(r'172\.18\.16\.1:1234|gemma', re.I)
VOICE = re.compile(r'voice|tts|rex|kokoro|minimax|/speak', re.I)
JOURN = re.compile(r'journal|introspect|bilateral|dream|taste|reflection', re.I)
HELPER = re.compile(r'def call_llm|def _llm|def llm\(|import.*model_router|from model_router', re.I)

def has(p, rx):
    try: return bool(rx.search(open(p, encoding="utf-8", errors="ignore").read()))
    except Exception: return False

grok_jobs, gemma_jobs, voice_jobs, journ_jobs, helper_jobs = [], [], [], [], []
for p in files:
    try: txt = open(p, encoding="utf-8", errors="ignore").read()
    except Exception: continue
    b = os.path.basename(p)
    if GROK.search(txt): grok_jobs.append(b)
    if GEMMA.search(txt): gemma_jobs.append(b)
    if VOICE.search(txt): voice_jobs.append(b)
    if JOURN.search(b) or JOURN.search(txt[:400]): journ_jobs.append(b)
    if HELPER.search(txt): helper_jobs.append(b)

print(f"~/Vintos scripts: {len(files)} total")
print(f"  call grok:  {len(grok_jobs)}   call gemma: {len(gemma_jobs)}   voice/rex: {len(voice_jobs)}")
print(f"\njournal / introspection / bilateral scripts:")
for b in journ_jobs: print(f"  {b}")
print(f"\nvoice / Rex / TTS (NEVER migrate):")
for b in sorted(set(voice_jobs)): print(f"  {b}")
print(f"\nscripts with an LLM-call helper (call_llm / _llm / model_router):")
for b in helper_jobs[:40]: print(f"  {b}")

# how uniform is the grok call? sample the exact call line across a few jobs
print("\nsample grok call lines (uniformity check):")
shown = 0
for p in files:
    if os.path.basename(p) not in grok_jobs: continue
    try: L = open(p, encoding="utf-8", errors="ignore").read().split("\n")
    except Exception: continue
    for i, l in enumerate(L):
        if re.search(r'chat/completions|"grok-4\.20|api\.x\.ai', l) and l.strip():
            print(f"  {os.path.basename(p)}:{i+1}: {l.strip()[:92]}")
            shown += 1; break
    if shown >= 14: break
