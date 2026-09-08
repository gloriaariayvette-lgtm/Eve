#!/usr/bin/env python3
"""recon_chatfull_core.py — Aegis, READ-ONLY, no LLM. The REAL main-chat handler is chat_full_context
(/api/chat/full). Print its bilateral core verbatim: _llm_call, a1/b1 gather, absorb, held, integration
(final-synthesis prompt), the final reply call, the tag-strip, and the return — so the patch targets the
handler the app actually uses. Bounded."""
import os, re, glob
HOME = os.path.expanduser("~")
P = next((p for p in (["/home/gloria/Vintos/server.py"] + glob.glob(os.path.join(HOME, "Vintos", "server.py")))
          if os.path.isfile(p)), None)
if not P: print("server.py not found"); raise SystemExit(0)
lines = open(P, encoding="utf-8", errors="ignore").read().split("\n")

S = next((k for k in range(len(lines)) if "@app.post(" in lines[k] and re.search(r'["\']/api/chat/full["\']', lines[k])), None)
if S is None: print("/api/chat/full not found"); raise SystemExit(0)
Sdef = next((k for k in range(S, S+4) if "def " in lines[k]), S)
col = len(lines[Sdef]) - len(lines[Sdef].lstrip())
END = Sdef + 1
while END < len(lines):
    l = lines[END]
    if l.strip() and (len(l)-len(l.lstrip())) <= col and l.lstrip().startswith(("async def ","def ","@app")):
        break
    END += 1
print(f"chat_full_context L{Sdef+1}-{END}\n")

# stage map
print("===== stage map =====")
for n in range(Sdef, END):
    l = lines[n]
    if re.search(r'chat/completions|_llm_call\(|"model"\s*:|grok-4|gemma|_asyncio\.gather|_absorb_msgs|_held_msgs|integration_content|integration_messages|# ?(Phase|BIS|Absorb|Synth|Final)|_re_do\.sub|return \{"reply"', l) and l.strip():
        print(f"  {n+1}: {l.strip()[:100]}")

# verbatim core: _llm_call def -> integration reply
start = next((n for n in range(Sdef, END) if lines[n].strip().startswith("async def _llm_call")), Sdef)
endc = next((n for n in range(start, END) if re.search(r'reply\s*=\s*await\s+_llm_call\(\s*integration_messages', lines[n])), start+200)
endc = min(END-1, endc + 4)
print(f"\n===== verbatim core L{start+1}-{endc+1} =====")
seg, size = [], 0
for n in range(start, endc+1):
    row = f"{n+1}: {lines[n]}"
    if size + len(row) > 10500: seg.append("   ...[truncated]"); break
    seg.append(row); size += len(row)+1
print("\n".join(seg))
