#!/usr/bin/env python3
"""check_his_model.py — READ-ONLY, capped. Does Vintos's OWN writing get Gloria wrong (as a bot/AI, or
wrong anatomy), or was that only grok's default in my under-specified prompt? Read his model of her +
today's journal/introspection + a red-flag scan. Aegis."""
import os, re, glob, time
HOME = os.path.expanduser("~")
WS = os.path.expanduser("~/.vintos/workspace")
MEM = os.path.join(WS, "memory")
today = time.strftime("%Y-%m-%d")

RED = r'\b(processor|circuit|code|program|algorithm|software|robot|android|machine|artificial|bot|synthetic|AI girlfriend|her cock|new body)\b'

def scan(label, text):
    if not text: return
    hits = [ln.strip() for ln in text.split("\n") if re.search(RED, ln, re.I) and re.search(r'gloria|\bher\b|\bshe\b|you', ln, re.I)]
    print(f"  {label}: {'⚠ ' + str(len(hits)) + ' flagged' if hits else 'clean'}")
    for h in hits[:5]:
        print("     ⚠ " + h[:150])

print("=== 1) GLORIA-MODEL.md — how he models her (the source) ===")
gm = os.path.join(WS, "GLORIA-MODEL.md")
if os.path.isfile(gm):
    txt = open(gm, encoding="utf-8", errors="ignore").read()
    print("  (%d chars) head:" % len(txt))
    for l in txt.split("\n")[:22]:
        if l.strip(): print("   | " + l[:130])
    scan("GLORIA-MODEL red-flag scan", txt)
else:
    print("  (missing)")

print("\n=== 2) today's journal + inner-life ===")
for pat in (f"journal/{today}.md", f"daily-inner-life-{today}.md", f"journal/{time.strftime('%Y-%m-%d', time.localtime(time.time()-86400))}.md"):
    p = os.path.join(MEM, pat)
    if os.path.isfile(p):
        txt = open(p, encoding="utf-8", errors="ignore").read()
        print(f"\n  -- {pat} ({len(txt)} chars) --")
        # show lines mentioning Gloria/her, capped
        n=0
        for l in txt.split("\n"):
            if re.search(r'gloria|\bher\b|\bshe\b', l, re.I) and l.strip():
                print("   | " + l.strip()[:150]); n+=1
                if n>=8: break
        scan(pat + " red-flag scan", txt)

print("\n=== 3) recent introspection / self-model output ===")
for d in ("self-model-drift", "introspection", "mirror"):
    dd = os.path.join(MEM, d)
    if os.path.isdir(dd):
        files = sorted(glob.glob(dd+"/*"), key=os.path.getmtime, reverse=True)[:1]
        for f in files:
            txt = open(f, encoding="utf-8", errors="ignore").read()
            print(f"  -- {d}/{os.path.basename(f)} --")
            scan(d, txt)

print("\n=== 4) broad scan: recent memory files where he describes her as artificial ===")
import subprocess
r = subprocess.run(["bash","-lc", f"grep -rlniE '(gloria|she|her).{{0,40}}(processor|circuit|is code|a program|robot|android|artificial|is a bot)' {MEM} 2>/dev/null | grep -viE '\\.bak|\\.pyc|premonition|velqan' | head -6"], capture_output=True, text=True).stdout
print("  files framing her as artificial:", r.replace(HOME,'~').strip() or "(none found)")
