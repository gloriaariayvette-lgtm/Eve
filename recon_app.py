#!/usr/bin/env python3
"""recon_app.py — READ-ONLY. Dump the exact app functions I need to fix (1) proactive messages not
appearing in chat and (2) the avatar-overlay conversation not appearing. Writes nothing.

RUN ON THE MAC in vintos-app (the canonical copy your phone builds from):
   python3 <(curl -fsSL <raw-url>/recon_app.py)
or point it explicitly:
   python3 recon_app.py --path src/index.html
"""
import os, sys, re

PATH = "src/index.html"
if "--path" in sys.argv:
    i = sys.argv.index("--path")
    if i + 1 < len(sys.argv):
        PATH = sys.argv[i + 1]
for cand in (PATH, "src/index.html", "index.html",
             os.path.expanduser("~/Downloads/vintos-repo/vintos-app/src/index.html"),
             os.path.expanduser("~/vintos-app/src/index.html")):
    if os.path.isfile(cand):
        PATH = cand; break

if not os.path.isfile(PATH):
    print("!! index.html not found — pass --path <file>"); sys.exit(0)

lines = open(PATH, encoding="utf-8", errors="ignore").read().splitlines()
print("=" * 78)
print("APP RECON (read-only):", os.path.abspath(PATH), "—", len(lines), "lines")
print("=" * 78)

# (label, [anchor regexes], lines_before, lines_after)
SECTIONS = [
    ("A. chat tab load + is there any polling?",
     [r"\bchatLoaded\b", r"dataset\.tab === 'chat'", r"loadChatHistory\(\)"], 2, 4),
    ("B. loadChatHistory() — the fetch + how a message row is rendered",
     [r"function loadChatHistory"], 0, 60),
    ("C. message render helper (if separate)",
     [r"function renderMessage", r"function addMessage", r"function appendMessage", r"function addChatMessage"], 0, 45),
    ("D. proactive / outreach surfacing (the 5-min poller)",
     [r"function checkOutreach", r"checkOutreach", r"pending-outreach", r"/api/pending", r"/api/outreach", r"/api/proactive"], 2, 45),
    ("E. avatar overlay — open + conversation container",
     [r"function _avOpen", r"function openAvatar", r"_avOpen\s*=", r"av-conversation", r"_avRenderConversation", r"_avRenderChat"], 0, 40),
    ("F. avatar conversation state + append",
     [r"_avChatHistory\s*=", r"_avChatHistory\.push", r"function _avAppend", r"function _avAddMsg"], 3, 25),
    ("G. avatar send + reply render",
     [r"/api/avatar/chat", r"function _avSend"], 4, 45),
    ("H. avatar bubbles (thought + command)",
     [r"function _avShowBubble", r"_avCheckCommandBubble", r"av-call-transcript"], 0, 30),
]

printed = set()  # avoid dumping overlapping windows twice
for label, anchors, before, after in SECTIONS:
    hit = None
    for rx in anchors:
        pat = re.compile(rx)
        for idx, ln in enumerate(lines):
            if pat.search(ln):
                hit = idx; break
        if hit is not None:
            break
    print("\n" + "-" * 78)
    print("###", label)
    print("-" * 78)
    if hit is None:
        print("   (no anchor matched: %s)" % " | ".join(anchors))
        continue
    lo = max(0, hit - before); hi = min(len(lines), hit + after)
    for n in range(lo, hi):
        if n in printed:
            continue
        printed.add(n)
        print("%5d| %s" % (n + 1, lines[n][:200]))

print("\n" + "=" * 78)
print("End recon. Paste this whole output back.")
print("=" * 78)
