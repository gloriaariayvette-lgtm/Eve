#!/usr/bin/env python3
"""recon_app_final.py — Mac, READ-ONLY. Last two: (5) _avTargetColor decl + every usage + forge fire
light/flicker in the animate loop; (3) av-chat-strip render + _avChatHistory display + any reset on open."""
import os, re
IDX = os.path.join(os.getcwd(), "src/index.html")
L = open(IDX, encoding="utf-8", errors="ignore").read().split("\n")
print("=== (5) _avTargetColor — declaration + all usages ===")
for i, l in enumerate(L):
    if "_avTargetColor" in l and l.strip():
        print(f"  {i+1}| {l.strip()[:120]}")
print("\n=== (5) forge fire light / flicker / glow in animate loop ===")
n = 0
for i, l in enumerate(L):
    if re.search(r'PointLight|_avFire|fireLight|flicker|_avGlow|forgeLight|Math\.random.*intensity|intensity\s*=', l) and l.strip():
        print(f"  {i+1}| {l.strip()[:120]}"); n += 1
        if n >= 16: break
print("\n=== (3) av-chat-strip render + history display + reset ===")
n = 0
for i, l in enumerate(L):
    if re.search(r'av-chat-strip|_avRenderChat|_avChatStrip|_avChatHistory|chat-strip|_avShowBubble\b|renderStrip', l) and l.strip():
        print(f"  {i+1}| {l.strip()[:120]}"); n += 1
        if n >= 18: break
print("\n=== (3) openAvatarOverlay full (does it repopulate/clear messages?) ===")
for i, l in enumerate(L):
    if re.search(r'function openAvatarOverlay', l):
        for j in range(i, min(i+22, len(L))):
            if L[j].strip(): print(f"  {j+1}| {L[j].strip()[:114]}")
        break
