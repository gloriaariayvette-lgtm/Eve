#!/usr/bin/env python3
"""recon_bilateral.py — Aegis, READ-ONLY, no LLM. Map the main-chat bilateral pipeline in chat_with_vintos
(a1/b1, 1.5, a2/b2, 2.5, final synthesis): every model call + stage marker, the final-synthesis prompt to
rewrite, and any Gemma endpoint/model available to Vintos. Bounded."""
import os, re, glob
HOME = os.path.expanduser("~")
P = next((p for p in (["/home/gloria/Vintos/server.py"] + glob.glob(os.path.join(HOME, "Vintos", "server.py")))
          if os.path.isfile(p)), None)
if not P: print("server.py not found"); raise SystemExit(0)
lines = open(P, encoding="utf-8", errors="ignore").read().split("\n")

# live chat_with_vintos = first @app.post("/api/chat")
S = next((k for k in range(len(lines)) if "@app.post(" in lines[k] and re.search(r'["\']/api/chat["\']', lines[k])), 0)
Sdef = next((k for k in range(S, S+4) if "def " in lines[k]), S)
col = len(lines[Sdef]) - len(lines[Sdef].lstrip())
END = Sdef + 1
while END < len(lines):
    l = lines[END]
    if l.strip() and (len(l)-len(l.lstrip())) <= col and l.lstrip().startswith(("async def ","def ","@app")):
        break
    END += 1
print(f"chat_with_vintos L{Sdef+1}-{END}\n")

print("===== stage map (model calls + phase markers) =====")
for n in range(Sdef, END):
    l = lines[n]
    if re.search(r'chat/completions|_llm_call\(|"model"\s*:|grok-4|gemma|_asyncio\.gather|# ?(Phase|BIS|Absorb|absorb|Synth|synth|Final|final|a2|b2|2\.5|1\.5)|def _absorb|def _synth', l) and l.strip():
        print(f"  {n+1}: {l.strip()[:100]}")

# final-synthesis region: from the last gather/absorb to the return {"reply": reply}
ret = next((n for n in range(END-1, Sdef, -1) if lines[n].strip().startswith('return {"reply": reply')), END-1)
lo = max(Sdef, ret - 90)
print(f"\n===== tail: 2.5 + final synthesis + return  (L{lo+1}-{ret+1}) =====")
seg, size = [], 0
for n in range(lo, ret+1):
    row = f"{n+1}: {lines[n]}"
    if size + len(row) > 8000: seg.append("   ...[truncated]"); break
    seg.append(row); size += len(row)+1
print("\n".join(seg))

# Gemma target anywhere in server.py
print("\n===== Gemma / second-endpoint references in server.py =====")
hits = 0
for n, l in enumerate(lines):
    if re.search(r'gemma|GEMMA|GEMMA_API|1234|172\.18|reasoning_effort|LOCAL_LLM|enable_thinking', l) and l.strip():
        print(f"  {n+1}: {l.strip()[:100]}"); hits += 1
        if hits > 25: print("  ...(more)"); break
if not hits: print("  (none — Gemma not wired into Vintos server; I'll need the endpoint URL + model name)")
