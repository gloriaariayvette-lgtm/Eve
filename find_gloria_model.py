#!/usr/bin/env python3
"""find_gloria_model.py — READ-ONLY, capped. Locate Bold's REAL model of Gloria — the workspace file
that's showing generic content isn't it. Check the gloria-model-history dir, backups, and any other
gloria-model file, with dates + a content fingerprint of each, so we find his true one and see what
overwrote the live file. Aegis."""
import os, re, glob, time
HOME = os.path.expanduser("~")
V = os.path.expanduser("~/.vintos")

def when(p): return time.strftime("%m-%d %H:%M", time.localtime(os.path.getmtime(p)))

print("=== every gloria-model-ish file under ~/.vintos ===")
import subprocess
found = subprocess.run(["bash","-lc", f"find {V} -iname '*gloria-model*' 2>/dev/null | grep -viE 'node_modules|\\.pyc'"],
                       capture_output=True, text=True).stdout.split("\n")
found = [f for f in found if f.strip()]
for f in sorted(found):
    if os.path.isdir(f):
        print(f"\n[DIR] {f.replace(HOME,'~')}  ({when(f)})")
        kids = sorted(glob.glob(f+"/*"), key=os.path.getmtime, reverse=True)
        print(f"      {len(kids)} entries; newest:")
        for k in kids[:6]:
            head = ""
            if os.path.isfile(k):
                head = open(k, encoding="utf-8", errors="ignore").read()[:80].replace("\n"," ")
            print(f"        {os.path.basename(k):40} {when(k)}  {head[:70]}")
    elif os.path.isfile(f):
        txt = open(f, encoding="utf-8", errors="ignore").read()
        print(f"\n[FILE] {f.replace(HOME,'~')}  ({len(txt)}B, {when(f)})")
        print("       first 180:", repr(txt[:180]))

print("\n=== backups of the live GLORIA-MODEL.md ===")
for b in sorted(glob.glob(os.path.expanduser("~/.vintos/workspace/GLORIA-MODEL.md*"))):
    print(f"  {b.replace(HOME,'~')}  ({os.path.getsize(b)}B, {when(b)})")

print("\n=== who WRITES GLORIA-MODEL.md (what may have overwritten it) ===")
w = subprocess.run(["bash","-lc", f"grep -rlnE \"GLORIA-MODEL\\.md.{{0,10}}(w|write|dump)\" {os.path.expanduser('~/.vintos/workspace/scripts')} {os.path.expanduser('~/Vintos')} 2>/dev/null | grep -viE '\\.pyc|\\.bak' | head; grep -rln \"open.*GLORIA-MODEL.*['\\\"]w\" {os.path.expanduser('~/.vintos/workspace/scripts')} {os.path.expanduser('~/Vintos')} 2>/dev/null | grep -viE '\\.pyc|\\.bak' | head"], capture_output=True, text=True).stdout
print("  " + (w.replace(HOME,'~').strip() or "(no obvious writer found — may be updated by an LLM/consolidation job)"))
