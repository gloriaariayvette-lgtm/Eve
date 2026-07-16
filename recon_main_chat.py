#!/usr/bin/env python3
"""recon_main_chat.py — Aegis, READ-ONLY, no LLM. Identify the LIVE main-chat handler (/api/chat) and reveal:
does it STREAM to the client (StreamingResponse/SSE)?, its grok inference call, and its return — so Phase 2
(route main chat through model_router) is spliced correctly. Bounded."""
import os, re, glob
HOME = os.path.expanduser("~")
P = next((p for p in (["/home/gloria/Vintos/server.py"] + glob.glob(os.path.join(HOME, "Vintos", "server.py")))
          if os.path.isfile(p)), None)
if not P: print("server.py not found"); raise SystemExit(0)
lines = open(P, encoding="utf-8", errors="ignore").read().split("\n")

# all chat POST routes (to spot the main one + any duplicates)
print("===== chat POST routes =====")
for i, l in enumerate(lines):
    if "@app.post(" in l and re.search(r'/api/chat', l):
        nxt = next((lines[k].strip()[:70] for k in range(i, min(i+3, len(lines))) if "def " in lines[k]), "?")
        print(f"  L{i+1}: {l.strip()[:46]}  ->  {nxt}")

# pick the LIVE /api/chat (exact) handler = first registered
S = next((i for i, l in enumerate(lines) if "@app.post(" in l and re.search(r'["\']/api/chat["\']', l)), None)
if S is None:
    print("\nno exact /api/chat POST route found"); raise SystemExit(0)
Sdef = next((k for k in range(S, S+4) if "def " in lines[k]), S)
col = len(lines[Sdef]) - len(lines[Sdef].lstrip())
END = Sdef + 1
while END < len(lines):
    l = lines[END]
    if l.strip() and (len(l)-len(l.lstrip())) <= col and l.lstrip().startswith(("async def ","def ","@app")):
        break
    END += 1
print(f"\nLIVE /api/chat handler: {lines[Sdef].strip()[:70]}  (L{Sdef+1}-{END})")

# CLIENT STREAMING? (the key question)
print("\n===== client-streaming signals in this handler =====")
found = False
for n in range(Sdef, END):
    if re.search(r'StreamingResponse|EventSourceResponse|sse|media_type|yield |StreamingResp|text/event-stream|async def _?(gen|stream|event)', lines[n]):
        print(f"  L{n+1}: {lines[n].strip()[:96]}"); found = True
print("  (none — returns a full reply, like avatar)" if not found else "")

# inference call region
call = next((n for n in range(Sdef, END) if re.search(r'chat/completions|x\.ai|LM_STUDIO|client\.stream|\.post\(', lines[n])), Sdef)
lo = max(Sdef, call-4); hi = min(END, call+60)
print(f"\n===== inference call region (L{lo+1}-{hi}) =====")
print("\n".join(f"{n+1}: {lines[n]}" for n in range(lo, hi))[:6500])

# return(s)
print("\n===== returns in this handler =====")
for n in range(Sdef, END):
    if re.search(r'\breturn\b', lines[n]) and 'return to idle' not in lines[n].lower():
        print(f"  L{n+1}: {lines[n].strip()[:96]}")
