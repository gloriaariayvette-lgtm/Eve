#!/usr/bin/env python3
"""server_prompt_order.py — READ-ONLY, tight. The exact ORDER context enters the CHAT system prompt,
plus whether SOUL/identity, value-map, journals, and conversation history are injected at all.

Prints, per being's server:
  - the ordered list of what gets put into `parts` (labels only, in source order) — the injection order
  - where SOUL / IDENTITY.md enters, and whether it LEADS or trails
  - where parts -> system prompt is assembled, and where the user/history messages are built
  - presence check: value-map.md, journals/daily-inner-life, conversation history, emotional state
Labels only, no bodies. This is the real answer to "is her context actually in the prompt, in order."
"""
import os, re, glob

HOME = os.path.expanduser("~")
SERVERS = {
    "VINTOS":  os.path.join(HOME, "Vintos", "server.py"),
    "VELARIS": os.path.join(HOME, "velaris-server", "server.py"),
}

LABEL = re.compile(r'parts\.(append|insert)\((?:0,\s*)?f?["\']([^"\'\n]{0,80})')
SYS_ASM = re.compile(r'("\\n\\n"\.join\(parts\)|"\\n"\.join\(parts\)|\.join\(parts\)|system\s*=|system_prompt\s*=)')
MSG_ASM = re.compile(r'(messages\s*=|messages\.append|role"\s*:\s*"user|role"\s*:\s*"system|chat[-_]?history|conversation|history)')
PRESENCE = {
    "SOUL.md / identity":       re.compile(r'SOUL\.md|IDENTITY\.md|load_soul|YOUR IDENTITY', re.I),
    "value-map":                re.compile(r'value[-_]map', re.I),
    "journals / daily-inner":   re.compile(r'daily[-_]inner|/journal|journal/|JOURNAL', re.I),
    "conversation history":     re.compile(r'chat[-_]?history|conversation[-_]?history|messages\.append|recent.*turns', re.I),
    "emotional state":          re.compile(r'emotional[-_]state|emotion_vector|EMOTIONAL STATE', re.I),
    "value_map injected here":  re.compile(r'value[-_]map\.md', re.I),
}

def audit(name, path):
    print("\n########## %s : %s ##########" % (name, path.replace(HOME, "~")))
    if not os.path.exists(path):
        print("  server not found"); return
    lines = open(path, encoding="utf-8", errors="ignore").read().splitlines()

    print("\n-- injection order into `parts` (top = first in prompt) --")
    n = 0
    for i, ln in enumerate(lines):
        m = LABEL.search(ln)
        if m:
            how = "INSERT@0" if m.group(1) == "insert" else "append "
            print("  %5d  %s  %s" % (i + 1, how, m.group(2).strip()[:70]))
            n += 1
    if not n:
        print("  (no parts.append/insert found — chat context assembled differently; see seams below)")

    print("\n-- assembly seams (parts -> system, and message/history build) --")
    shown = 0
    for i, ln in enumerate(lines):
        if SYS_ASM.search(ln) or MSG_ASM.search(ln):
            s = ln.strip()
            if s and not s.startswith("#"):
                print("  %5d: %s" % (i + 1, s[:140])); shown += 1
        if shown >= 22:
            print("  ...(capped)"); break

    print("\n-- presence check (is it injected into chat at all?) --")
    for label, rx in PRESENCE.items():
        hits = [i + 1 for i, ln in enumerate(lines) if rx.search(ln)]
        where = ("lines " + ",".join(map(str, hits[:6]))) if hits else "!! NOT FOUND"
        print("  %-26s %s" % (label, where))

for name, path in SERVERS.items():
    audit(name, path)
print("\n=== done. If SOUL is missing or trails the memory dump, identity isn't leading the prompt. ===")
