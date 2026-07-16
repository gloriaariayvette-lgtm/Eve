#!/usr/bin/env python3
"""recon_ed.py — Aegis, READ-ONLY. (A) Dump Vintos's Enactment Distiller (idle-journal.sh block + the module it
calls). (B) Find + dump Velaris's ED as the correct reference. (C) Trace where kiss/blush/mischief enter
Vintos's pipeline — he shouldn't have those. Bounded output."""
import os, glob, re
HOME = os.path.expanduser("~")

def head(t): print("\n" + "=" * 78 + "\n" + t + "\n" + "=" * 78)

# ---------- (A) Vintos ED block in idle-journal.sh ----------
head("(A) VINTOS ED BLOCK — idle-journal.sh around L1195")
p = os.path.join(HOME, "Vintos", "idle-journal.sh")
if os.path.isfile(p):
    L = open(p, encoding="utf-8", errors="ignore").read().split("\n")
    s = next((i for i, l in enumerate(L) if "Enactment Distiller" in l), 1194)
    # print until the python -c closes (a line == '" 2>/dev/null') after s, +cap
    e = s
    for j in range(s+1, min(len(L), s+120)):
        e = j
        if L[j].strip().startswith('" 2>/dev/null') or L[j].strip() == '"':
            break
    for i in range(max(0, s-2), min(len(L), e+2)):
        print(f"{i+1:>5}: {L[i]}")

# ---------- ED / distiller modules in both scripts dirs ----------
RX = re.compile(r'enact|observed capab|distill|Observed capability|named_without', re.I)
def dump_scripts(label, base):
    head(f"{label} — modules matching enact/distill/capability in {base.replace(HOME,'~')}")
    if not os.path.isdir(base): print("  (dir not found)"); return
    for f in sorted(glob.glob(os.path.join(base, "*.py"))):
        try: txt = open(f, encoding="utf-8", errors="ignore").read()
        except Exception: continue
        if RX.search(txt):
            print(f"\n----- {f.replace(HOME,'~')} ({txt.count(chr(10))+1} lines) -----")
            lines = txt.split("\n")
            if len(lines) <= 160:
                for i, l in enumerate(lines): print(f"{i+1:>5}: {l}")
            else:
                for i, l in enumerate(lines):
                    if RX.search(l):
                        a=max(0,i-3); b=min(len(lines),i+8)
                        for j in range(a,b): print(f"{j+1:>5}: {lines[j]}")
                        print("   ----")

dump_scripts("(A2) VINTOS scripts", os.path.join(HOME, ".vintos/workspace/scripts"))
dump_scripts("(B) VELARIS scripts", os.path.join(HOME, ".openclaw/workspace/scripts"))

# ---------- (C) kiss / blush / mischief sources ----------
head("(C) WHERE DO kiss / blush / mischief ENTER VINTOS?")
KRX = re.compile(r'kiss|blush|mischief', re.I)
for base, tag in ((os.path.join(HOME, "Vintos"), "Vintos/"),
                  (os.path.join(HOME, ".vintos/workspace/scripts"), ".vintos/scripts/")):
    if not os.path.isdir(base): continue
    for f in sorted(glob.glob(os.path.join(base, "**", "*.*"), recursive=True)):
        if not f.endswith((".py", ".sh")): continue
        try: lines = open(f, encoding="utf-8", errors="ignore").read().split("\n")
        except Exception: continue
        hits = [(i+1, l.strip()) for i, l in enumerate(lines) if KRX.search(l)]
        if hits:
            print(f"\n--- {tag}{os.path.basename(f)} ({len(hits)} hits) ---")
            for ln, t in hits[:10]:
                print(f"  {ln:>5}: {t[:120]}")
            if len(hits) > 10: print(f"   ... +{len(hits)-10} more")
