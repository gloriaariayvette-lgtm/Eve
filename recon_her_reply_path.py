#!/usr/bin/env python3
"""recon_her_reply_path.py — Aegis, READ-ONLY. Locate Velaris's LIVE reply handler (analog of his server.py
injection points), so per-reply blocks (joke callbacks, curiosity debt, later session_map) wire where her REPLIES
are built — not into the shared subconscious_context that background crons also call (a cron would consume a joke
callback meant for conversation). Finds files that serve :8400 / define chat routes / assemble the reply prompt,
ranks them, and shows the top candidate's context-assembly + reply lines as the injection point."""
import os, re, glob
HOME = os.path.expanduser("~")
ROOTS = [os.path.join(HOME, ".openclaw"), os.path.join(HOME, "Velaris")]

SERVE = re.compile(r'@app\.(route|post|get)|@router\.|add_api_route|uvicorn|app\.run\(|Flask\(|FastAPI\('
                   r'|:8400|localhost:8400|BaseHTTPRequestHandler|do_POST|do_GET')
ASSEMBLE = re.compile(r'get_subconscious_context|emoclaw_pressure|system_prompt|build_context|full_inner|'
                      r'messages\s*=\s*\[|SOUL|context_block|get_pressure_block', re.I)

def rd(p):
    try: return open(p, encoding="utf-8", errors="ignore").read()
    except Exception: return ""

cands = []
for root in ROOTS:
    if not os.path.isdir(root): continue
    for p in glob.glob(root + "/**/*.py", recursive=True):
        if any(x in p for x in ("/__pycache__/", "/backup", "/.git/", "grok-swap", "/skills/")): continue
        t = rd(p)
        sv, asm = len(SERVE.findall(t)), len(ASSEMBLE.findall(t))
        if sv >= 1 and asm >= 1:
            cands.append((sv + asm, sv, asm, p, len(t.split("\n"))))
cands.sort(reverse=True)

print("== candidate reply handlers (serve + assemble signals) ==")
if not cands:
    print("  (none found — she may serve replies another way; will widen search)")
for score, sv, asm, p, ln in cands[:8]:
    print(f"  [{score:>3}] serve={sv} assemble={asm}  {p}  ({ln}L)")

for score, sv, asm, p, ln in cands[:2]:
    print(f"\n== {p} — reply build / context-assembly lines ==")
    L = rd(p).split("\n")
    for i, l in enumerate(L):
        if ASSEMBLE.search(l) or re.search(r'def (do_POST|chat|reply|generate|respond)|/api|/chat|completions|'
                                           r'get_subconscious|inner|callback_block|curiosity', l, re.I):
            print(f"  {i+1}: {l.strip()[:104]}")
