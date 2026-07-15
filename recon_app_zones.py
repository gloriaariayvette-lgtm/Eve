#!/usr/bin/env python3
"""recon_app_zones.py — Mac, READ-ONLY. Verbatim: _avTouchResponse + the tap/zone-detection block
(to add a chest zone), the chat-strip markup (to build the running log), and _avSpeakAndShow head."""
import os
IDX = os.path.join(os.getcwd(), "src/index.html")
L = open(IDX, encoding="utf-8", errors="ignore").read().split("\n")
def rng(a, b, label):
    print(f"\n=== {label} (lines {a}..{b}) ===")
    for i in range(a-1, min(b, len(L))):
        print(f"{i+1:4}| {L[i][:120]}")
rng(3105, 3170, "_avTouchResponse + tap handler + zone detection")
rng(3757, 3766, "av-chat-strip markup (for the running log)")
rng(3071, 3080, "_avSpeakAndShow head")
