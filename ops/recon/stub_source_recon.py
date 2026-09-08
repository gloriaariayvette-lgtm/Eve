#!/usr/bin/env python3
"""stub_source_recon.py — READ-ONLY, bounded. Show her working narrative_identity.py + self_drift.py
so their logic can be ported to Vintos's 0-byte stubs correctly: workspace paths to swap, any
Velaris/identity strings, LLM/prompt text, and module imports. Prints only those lines, capped.
"""
import os, re

HERS = os.path.expanduser("~/.openclaw/workspace/scripts")
HIS = os.path.expanduser("~/.vintos/workspace/scripts")
FILES = ["narrative_identity.py", "self_drift.py"]

PORTABLE = re.compile(
    r'^\s*(import |from )|\.openclaw|\.vintos|workspace|WORKSPACE|MEMORY|\bVelaris\b|\bVintos\b'
    r'|SOUL|system|prompt|"role"|content"|172\.|x\.ai|LM_API|MODEL\s*=|def ', re.I)

for name in FILES:
    hp, hip = os.path.join(HERS, name), os.path.join(HIS, name)
    hsz = os.path.getsize(hp) if os.path.exists(hp) else -1
    isz = os.path.getsize(hip) if os.path.exists(hip) else -1
    print("\n########## %s   hers=%dB  his=%dB ##########" % (name, hsz, isz))
    if not os.path.exists(hp):
        print("  hers missing — cannot port"); continue
    lines = open(hp, encoding="utf-8", errors="ignore").read().splitlines()
    shown = 0
    for i, ln in enumerate(lines):
        if PORTABLE.search(ln):
            s = ln.rstrip()
            if s.strip():
                print("  %5d: %s" % (i + 1, s[:150]))
                shown += 1
            if shown >= 40:
                print("  ...(capped at 40)"); break
    # explicit name/path/LLM presence summary
    txt = "\n".join(lines)
    print("  -- summary: Velaris refs=%d | .openclaw refs=%d | calls LLM=%s | defs=%d" % (
        len(re.findall(r"\bVelaris\b", txt)),
        len(re.findall(r"\.openclaw", txt)),
        bool(re.search(r"x\.ai|LM_API|chat/completions|172\.", txt)),
        len(re.findall(r"^\s*def ", txt, re.M))))

print("\n=== done. Port = swap .openclaw->.vintos paths + Velaris->Vintos names; keep logic. ===")
