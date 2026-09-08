#!/usr/bin/env python3
"""funcs_resolve.py — READ-ONLY, closing. What do the chat prompt's wrapper functions actually inject?

The chat system_prompt calls inner_life_context(), builds _vt_subblock via _vt_sub()/inline, and (Velaris)
_spark_block(). Whether value-map / journals / narrative-identity / pearls reach the being mid-chat depends
on these. This finds each function's body and prints only its context-source lines (what files/modules it
reads), and reports which function contains the value-map.md reads at ~5011/5318 (Vintos) / ~3616/3847
(Velaris). Bounded.
"""
import os, re

HOME = os.path.expanduser("~")
SERVERS = {
    "VINTOS":  os.path.join(HOME, "Vintos", "server.py"),
    "VELARIS": os.path.join(HOME, "velaris-server", "server.py"),
}
TARGETS = ["inner_life_context", "_vt_sub", "_spark_block", "get_subconscious_context",
           "get_subconscious_context_compact"]
SRC = re.compile(
    r'value[-_]map|daily[-_]inner|/journal|journal/|narrative[-_]?identity|self[-_]?statement|pearl'
    r'|preoccupation|wants|growth|self[-_]?model|mirror|dream|therapeut|drift|trajectory|import ',
    re.I)

def func_span(lines, name):
    """Return (start,end) of `def name(` by indentation, first match."""
    for i, ln in enumerate(lines):
        m = re.match(r'(\s*)def\s+%s\s*\(' % re.escape(name), ln)
        if m:
            indent = len(m.group(1))
            for j in range(i + 1, len(lines)):
                s = lines[j]
                if s.strip() and (len(s) - len(s.lstrip())) <= indent and re.match(r'\s*(def|class|@)', s):
                    return i, j
            return i, min(i + 120, len(lines))
    return None

def dump(name, path):
    print("\n########## %s : %s ##########" % (name, path.replace(HOME, "~")))
    if not os.path.exists(path):
        print("  not found"); return
    lines = open(path, encoding="utf-8", errors="ignore").read().splitlines()
    for t in TARGETS:
        span = func_span(lines, t)
        if not span:
            continue
        lo, hi = span
        print("\n-- def %s()  (lines %d-%d) : context sources --" % (t, lo + 1, hi))
        shown = 0
        for i in range(lo, hi):
            if SRC.search(lines[i]):
                s = lines[i].strip()
                if s and not s.startswith("#"):
                    print("  %5d: %s" % (i + 1, s[:140])); shown += 1
            if shown >= 16:
                print("  ...(capped)"); break
        if not shown:
            print("  (reads none of the tracked sources directly — may delegate)")
    # which function owns the mid-file value-map reads?
    print("\n-- value-map.md reads outside the routes, and their enclosing def --")
    for i, ln in enumerate(lines):
        if i > 2500 and re.search(r'value[-_]map\.md', ln, re.I):
            owner = "?"
            for j in range(i, max(2000, i - 200), -1):
                m = re.match(r'\s*(?:async\s+)?def\s+(\w+)', lines[j])
                if m: owner = m.group(1); break
            print("  %5d: value-map.md  <- inside def %s()" % (i + 1, owner))

for name, path in SERVERS.items():
    dump(name, path)
print("\n=== done. If value-map/journals appear here inside a chat-called wrapper, they DO reach chat. ===")
