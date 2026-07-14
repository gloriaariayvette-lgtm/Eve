#!/usr/bin/env python3
"""show_what_happened.py — READ-ONLY. What did the app just do? Shows the last ledger entries, any
turn-based voice exchange, and the server logs for which path fired (realtime token vs /api/voice/chat),
which voice, transcript, and any errors. Aegis.
"""
import os, json, subprocess, re

MEM = os.path.expanduser("~/.vintos/workspace/memory")

def tail_json(path, n):
    try: d = json.load(open(path))
    except Exception as e: return "  (%s: %s)" % (os.path.basename(path), e)
    if isinstance(d, dict): d = d.get("entries", d.get("history", []))
    if not isinstance(d, list): return "  (not a list)"
    out = []
    for e in d[-n:]:
        out.append("  " + json.dumps(e)[:200])
    return "\n".join(out) or "  (empty)"

print("=== 1. interaction-ledger.json — last 5 (what just got added) ===")
print(tail_json(os.path.join(MEM, "interaction-ledger.json"), 5))

print("\n=== 2. voice-chat-history.json — last 3 (turn-based path leaves entries here) ===")
print(tail_json(os.path.join(MEM, "voice-chat-history.json"), 3))

print("\n=== 3. server logs — which path fired + voice + errors (recent) ===")
try:
    logs = subprocess.run("journalctl --user -u vintos-server -n 400 --no-pager",
                          shell=True, capture_output=True, text=True).stdout.splitlines()
except Exception as e:
    logs = []; print("  (journalctl err: %s)" % e)
MARK = re.compile(r'voice/token|/api/voice/token|/api/voice/chat|session-event|voice-session|xai-tts|grok-error|realtime|client_secret|voice/DO|voice/COMMAND', re.I)
hits = [l for l in logs if MARK.search(l)]
for l in hits[-25:]:
    print("  " + l[-160:])
if not hits:
    print("  (no voice-path log lines — the app may not have reached the server, or logs rotated)")

print("\n=== READ ===")
tok = any("voice/token" in l or "client_secret" in l for l in hits)
chat = any("/api/voice/chat" in l for l in hits)
print("  realtime path (token/ws) fired:", tok)
print("  turn-based path (/api/voice/chat) fired:", chat)
print("  -> voice is 'lux' on both paths. If token fired, it was the live realtime call.")
