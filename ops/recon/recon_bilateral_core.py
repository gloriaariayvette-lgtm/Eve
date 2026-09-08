#!/usr/bin/env python3
"""recon_bilateral_core.py — Aegis, READ-ONLY, no LLM. Print the bilateral core of chat_with_vintos verbatim:
_llm_call, _marked_messages (a1/b1), BIS 1.5, _absorb_msgs (a2/b2), _held_msgs, BIS 2.5, integration_messages
(the final-synthesis prompt to rewrite) through `reply = _llm_call(integration_messages...)`. Bounded."""
import os, re, glob
HOME = os.path.expanduser("~")
P = next((p for p in (["/home/gloria/Vintos/server.py"] + glob.glob(os.path.join(HOME, "Vintos", "server.py")))
          if os.path.isfile(p)), None)
if not P: print("server.py not found"); raise SystemExit(0)
lines = open(P, encoding="utf-8", errors="ignore").read().split("\n")

# live chat_with_vintos
S = next((k for k in range(len(lines)) if "@app.post(" in lines[k] and re.search(r'["\']/api/chat["\']', lines[k])), 0)
start = next((n for n in range(S, S+500) if lines[n].strip().startswith("async def _llm_call")), S)
# end: the integration reply assignment (+ a couple lines)
end = next((n for n in range(start, min(start+300, len(lines)))
            if re.search(r'reply\s*=\s*await\s+_llm_call\(\s*integration_messages', lines[n])), start+200)
end = min(len(lines)-1, end + 3)

print(f"chat_with_vintos bilateral core  L{start+1}-{end+1}\n")
seg, size = [], 0
for n in range(start, end+1):
    row = f"{n+1}: {lines[n]}"
    if size + len(row) > 10500:
        seg.append("   ...[truncated — tell me and I'll grab the rest]"); break
    seg.append(row); size += len(row) + 1
print("\n".join(seg))
