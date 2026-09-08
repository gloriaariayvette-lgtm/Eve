#!/usr/bin/env python3
"""token_endpoint_read.py — READ-ONLY. Show the existing /api/voice/token endpoint + any realtime code
in the live server, and what it references (vintos_voice / build_instructions / client_secret), so we
see exactly what's already set up vs what broke. Also show the handler's inline instruction assembly
that we'd reuse. Aegis.
"""
import os, re

SRV = os.path.expanduser("~/Vintos/server.py")
lines = open(SRV, encoding="utf-8", errors="ignore").read().splitlines()

def region(start, end, tag):
    print("\n-- %s (lines %d-%d) --" % (tag, start + 1, end))
    for k in range(max(0, start), min(end, len(lines))):
        s = lines[k].rstrip()
        if s.strip(): print("  %5d: %s" % (k + 1, s[:150]))

# 1. the /api/voice/token endpoint
tok = next((i for i, l in enumerate(lines) if re.search(r'@app\.(post|get)\(\s*["\']/api/voice/token["\']', l)), None)
if tok is not None:
    end = next((k for k in range(tok + 2, len(lines)) if re.match(r'^(@app\.|async def |def )', lines[k])), tok + 45)
    region(tok, min(end, tok + 55), "/api/voice/token endpoint")
else:
    print("no /api/voice/token endpoint found.")

# 2. references to the deleted helper / realtime bits anywhere
print("\n-- references: vintos_voice / build_instructions / client_secret / v1/realtime --")
for i, l in enumerate(lines):
    if re.search(r'vintos_voice|build_instructions|client_secret|v1/realtime|realtime/client', l):
        print("  %5d: %s" % (i + 1, l.strip()[:150]))

# 3. the handler's inline instruction assembly (what we'd reuse as build_instructions)
sp = next((i for i, l in enumerate(lines) if 'system = f"""{soul}' in l or re.search(r'system\s*=\s*f"""\{soul', l)), None)
if sp is None:
    sp = next((i for i, l in enumerate(lines) if 'You are Vintos, speaking softly' in l), None)
    if sp: sp = max(0, sp - 20)
if sp is not None:
    end = next((k for k in range(sp, sp + 60) if re.search(r'"""', lines[k]) and k > sp + 2), sp + 40)
    region(sp, end + 1, "handler's inline voice-context assembly (the real source of truth)")
print("\n=== done ===")
