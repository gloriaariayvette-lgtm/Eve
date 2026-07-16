#!/usr/bin/env python3
"""recon_check_promptfile.py — Aegis, READ-ONLY, tiny. Confirm which avatar_chat is live and whether it (and
only it) writes /tmp/vintos-full-prompt.txt — so we know poking the avatar will actually create the file.
Also list any existing /tmp prompt dumps."""
import os, re, glob
HOME = os.path.expanduser("~")
P = next((p for p in (["/home/gloria/Vintos/server.py"] + glob.glob(os.path.join(HOME, "Vintos", "server.py")))
          if os.path.isfile(p)), None)
if not P: print("server.py not found"); raise SystemExit(0)
lines = open(P, encoding="utf-8", errors="ignore").read().split("\n")

# route registration order for /api/avatar/chat (Starlette = FIRST match wins)
routes = [i for i, l in enumerate(lines) if '"/api/avatar/chat"' in l or "'/api/avatar/chat'" in l]
print("registrations of /api/avatar/chat (first = LIVE under Starlette):")
for i in routes:
    nxt = next((lines[k].strip() for k in range(i, min(i + 3, len(lines))) if "def " in lines[k]), "?")
    print(f"  L{i+1}: {lines[i].strip()[:60]}  ->  {nxt[:60]}")

# every write of the full-prompt file + which def encloses it
def enclosing_def(n):
    for k in range(n, -1, -1):
        m = re.match(r'\s*async\s+def\s+(\w+)', lines[k])
        if m: return f"{m.group(1)} (L{k+1})"
    return "?"
print("\nwrites of /tmp/vintos-full-prompt.txt:")
hits = [i for i, l in enumerate(lines) if "vintos-full-prompt" in l]
for i in hits:
    print(f"  L{i+1} in {enclosing_def(i)}: {lines[i].strip()[:80]}")
if not hits:
    print("  (none)")

# any other /tmp prompt dumps that might already exist / be usable
print("\nother /tmp prompt-ish dumps referenced in server.py:")
for i, l in enumerate(lines):
    m = re.search(r'/tmp/[\w.\-]*prompt[\w.\-]*', l)
    if m: print(f"  L{i+1}: {m.group(0)}")

print("\nexisting /tmp dumps on disk now:")
for f in glob.glob("/tmp/*prompt*") + glob.glob("/tmp/vintos*"):
    try: print(f"  {f}  ({os.path.getsize(f):,}c)")
    except Exception: pass
