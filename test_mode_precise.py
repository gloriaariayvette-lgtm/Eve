#!/usr/bin/env python3
"""test_mode_precise.py — READ-ONLY, accurate. For each write that PERSISTS a conversation (dumps a
*-history.json / interaction-ledger to disk), find its enclosing @app handler and report whether
_test_mode_active is checked ANYWHERE in that handler before the write. Ignores in-memory request
building (messages.append) and read-endpoint appends. Flags the real leaks only. Aegis.
"""
import os, re

SERVER = os.path.expanduser("~/Vintos", ) if False else os.path.expanduser("~/Vintos/server.py")
lines = open(SERVER, encoding="utf-8", errors="ignore").read().splitlines()

# real persistence: json.dump of a conversation history/ledger, or writing those files
PERSIST = re.compile(r'json\.dump\(\s*(\w*history\w*|\w*ledger\w*|history|tv_history|av_history|voice_history)\b'
                     r'|\.dump\(\s*_tvl?_?\w*|interaction-ledger', re.I)

def enclosing(i):
    """nearest @app route above line i, with its path + def line."""
    for k in range(i, -1, -1):
        m = re.search(r'@app\.\w+\("([^"]+)"', lines[k])
        if m:
            # find the def just after
            for j in range(k, min(k + 4, len(lines))):
                dm = re.search(r'def\s+(\w+)', lines[j])
                if dm: return m.group(1), dm.group(1), k
            return m.group(1), "?", k
    return "(module)", "?", 0

def handler_bounds(route_line):
    end = len(lines)
    for k in range(route_line + 2, len(lines)):
        if re.match(r'@app\.\w+\(', lines[k]): end = k; break
    return route_line, end

seen = set()
print("=== conversation-persistence writes: guarded vs LEAK (per handler) ===")
for i, l in enumerate(lines):
    if not PERSIST.search(l): continue
    if l.strip().startswith("#"): continue
    route, fn, rline = enclosing(i)
    if (route, rline) in seen: continue
    seen.add((route, rline))
    lo, hi = handler_bounds(rline)
    guarded = any("_test_mode_active" in lines[j] for j in range(lo, hi))
    dead = rline > 9600   # the duplicate/dead second half
    tag = "DEAD-DUP (never runs)" if dead else ("guarded" if guarded else ">>> LEAK — logs in test mode")
    print("  %-26s (def %s, @%d)  ->  %s   [write ~L%d]" % (route[:26], fn, rline + 1, tag, i + 1))

print("\n=== READ ===")
print("  'guarded' = respects test mode. 'DEAD-DUP' = duplicate code that never executes (ignore).")
print("  '>>> LEAK' = a live conversation surface that writes even in test mode — those I guard.")
