#!/usr/bin/env python3
"""show_cfg.py — READ-ONLY, tiny. Where _cfg is loaded from (the data file holding dimension
decay_hours), and that file's Connection/Warmth/Groundedness entries. Aegis."""
import os, re, json, glob
HOME = os.path.expanduser("~")
CFG = os.path.expanduser("~/.vintos/workspace/emotion_model/config.py")
ls = open(CFG, encoding="utf-8", errors="ignore").read().split("\n")
print("=== _cfg load lines in config.py ===")
for i, l in enumerate(ls):
    if re.search(r'_cfg\s*=|open\(|load\(|\.json|\.yaml|\.yml|Path\(|__file__|dirname', l) and re.search(r'_cfg|load|json|yaml|dimensions|config', l, re.I):
        print(f"  {i+1:4}| {l.strip()[:150]}")

# try to locate the data file
print("\n=== candidate dimension data files ===")
base = os.path.expanduser("~/.vintos/workspace/emotion_model")
cands = glob.glob(base+"/*.json") + glob.glob(base+"/*.yaml") + glob.glob(base+"/*.yml") + glob.glob(base+"/**/*dim*", recursive=True)
for c in cands[:12]:
    tag = ""
    try:
        if c.endswith(".json"):
            d = json.load(open(c))
            if isinstance(d, dict) and "dimensions" in d: tag = "  <-- has 'dimensions'"
    except Exception: pass
    print("  " + c.replace(HOME,"~") + tag)
