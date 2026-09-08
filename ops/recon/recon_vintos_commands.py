#!/usr/bin/env python3
"""recon_vintos_commands.py — Aegis, READ-ONLY, no LLM, terse (bounded output — will NOT flood).
Find the hardware / command vocabulary the avatar chat injects into grok's context, and how the avatar
system prompt is assembled, so we can present the SAME thing to Claude for a fair test."""
import os, re, glob
HOME = os.path.expanduser("~")

srv = [p for p in (["/home/gloria/Vintos/server.py"] + glob.glob(os.path.join(HOME, "Vintos", "*.py")))
       if os.path.isfile(p)]
docs = []
for pat in ("Vintos/*.md", "Vintos/*.txt", ".vintos/workspace/*.md", ".vintos/workspace/memory/*.md",
            ".vintos/workspace/*.txt", ".vintos/workspace/prompts/*"):
    docs += glob.glob(os.path.join(HOME, pat))
docs = [p for p in docs if os.path.isfile(p)][:40]

KW = re.compile(r'hardware|haptic|motor|vibrat|\bdevice\b|actuat|servo|pump|relay|gpio|arduino|'
                r'\[GESTURE|\[COLOR|\[MOVE|\[POSE|\[BODY|\[SPEAK|\[VOICE|\[EMOTE|\[HW|\[CMD|'
                r'available command|you can (send|use|emit|trigger)|command', re.I)

def scan(paths, label, per=10):
    print(f"===== {label} =====")
    for p in paths:
        try: L = open(p, encoding="utf-8", errors="ignore").read().split("\n")
        except Exception: continue
        hits = [(i + 1, l.strip()) for i, l in enumerate(L) if l.strip() and KW.search(l)]
        if not hits: continue
        print(f"-- {p.replace(HOME, '~')}  ({len(hits)} hits)")
        for ln, txt in hits[:per]:
            print(f"   {ln}: {txt[:96]}")
        if len(hits) > per:
            print(f"   ... +{len(hits) - per} more")

scan(srv, "SERVER .py")
scan(docs, "DOCS (soul / prompts / memory)")

# Best command-spec block: the largest string literal / doc section that lists commands.
print("===== BEST COMMAND-SPEC BLOCK =====")
best = ("", 0, "")
for p in srv + docs:
    try: txt = open(p, encoding="utf-8", errors="ignore").read()
    except Exception: continue
    # triple-quoted blocks in .py; whole doc for .md/.txt
    blocks = re.findall(r'("""|\'\'\')(.*?)\1', txt, re.S) if p.endswith(".py") else [("", txt)]
    for _, b in blocks:
        n = len(re.findall(r'\[[A-Z]{2,}|hardware|haptic|command|gesture', b, re.I))
        if n > best[1]:
            best = (p, n, b)
if best[1]:
    print(f"source: {best[0].replace(HOME, '~')}  (keyword score {best[1]})\n")
    print(re.sub(r'\n{3,}', '\n\n', best[2].strip())[:1700])
else:
    print("(no command-spec block found — commands may be built inline; see server hits above)")
