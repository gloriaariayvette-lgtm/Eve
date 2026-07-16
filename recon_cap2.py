#!/usr/bin/env python3
"""recon_cap2.py — Aegis, READ-ONLY. Dump the exact prompt-assembly regions so I can tell whether the FINAL
Claude synthesis (the call that writes the entry) carries CAPABILITIES.md, or only the a1/b1 drafts do."""
import os
HOME = os.path.expanduser("~")

def dump(name, ranges):
    p = os.path.join(HOME, "Vintos", name)
    if not os.path.isfile(p):
        print(f"=== {name}: not found ===\n"); return
    L = open(p, encoding="utf-8", errors="ignore").read().split("\n")
    print(f"########## {name} ({len(L)} lines) ##########")
    for a, b in ranges:
        a = max(1, a); b = min(len(L), b)
        print(f"----- L{a}-{b} -----")
        for i in range(a-1, b):
            print(f"{i+1:>5}: {L[i]}")
        print()
    print()

# idle-journal: system_msg build (a1/b1), _light_system def, _synthesis_system (final)
dump("idle-journal.sh", [(478, 512), (900, 946)])
# also find _light_system definition wherever it is
p = os.path.join(HOME, "Vintos", "idle-journal.sh")
if os.path.isfile(p):
    L = open(p, encoding="utf-8", errors="ignore").read().split("\n")
    for i, l in enumerate(L):
        if "_light_system" in l and "=" in l and "_synthesis_system" not in l:
            a=max(1,i-1); b=min(len(L),i+6)
            print(f"----- idle-journal _light_system @L{i+1} -----")
            for j in range(a-1,b): print(f"{j+1:>5}: {L[j]}")
            print()
            break

# introspection: CAPABILITIES heredoc context, system read + base_msgs, final call
dump("introspection.sh", [(288, 312), (380, 440)])
p = os.path.join(HOME, "Vintos", "introspection.sh")
if os.path.isfile(p):
    L = open(p, encoding="utf-8", errors="ignore").read().split("\n")
    for i, l in enumerate(L):
        if "_claude_sync(" in l:
            a=max(1,i-2); b=min(len(L),i+3)
            print(f"----- introspection _claude_sync @L{i+1} -----")
            for j in range(a-1,b): print(f"{j+1:>5}: {L[j]}")
            print()
