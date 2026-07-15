#!/usr/bin/env python3
"""recon_app_details.py — Mac, READ-ONLY. The 3 subtle batch items: (3) avatar-chat reopen/clear,
(4) _avPlayAnim T-pose fallback, (5) forge glow + how [COLOR] applies. index.html + avatar-bundle.js."""
import os, re
CWD = os.getcwd()
IDX = os.path.join(CWD, "src/index.html")
BUN = os.path.join(CWD, "src/avatar-bundle.js")
def block(path, start_pat, span=26, cap=2):
    if not os.path.isfile(path): print("  (missing)", path); return
    L = open(path, encoding="utf-8", errors="ignore").read().split("\n")
    n = 0
    for i, l in enumerate(L):
        if re.search(start_pat, l):
            print(f"  -- {os.path.basename(path)}:{i+1} --")
            for j in range(i, min(i+span, len(L))):
                if L[j].strip(): print(f"   {j+1}| {L[j].strip()[:112]}")
            n += 1
            if n >= cap: break

print("=== (4) _avPlayAnim (T-pose fallback when clip missing) ===")
block(IDX, r'async function _avPlayAnim', 22, 1)

print("\n=== how animation clips are found/loaded (why emote -> T-pose) ===")
block(IDX, r'_avClips|findClip|clipAction|AnimationClip|\.clips\b|getClip|_avActions', 10, 3)

print("\n=== (5) forge glow + [COLOR] application ===")
for p in (IDX, BUN):
    L = open(p, encoding="utf-8", errors="ignore").read().split("\n")
    n = 0
    for i, l in enumerate(L):
        if re.search(r'forge|glow|emissive|flicker|\.color\.set|COLOR:', l, re.I) and l.strip():
            print(f"   {os.path.basename(p)}:{i+1}| {l.strip()[:110]}"); n += 1
            if n >= 14: break

print("\n=== (3) avatar chat: open + where messages reset on reopen ===")
L = open(IDX, encoding="utf-8", errors="ignore").read().split("\n")
n = 0
for i, l in enumerate(L):
    if re.search(r'_avChatHistory\s*=|avChatOpen|openAvChat|avatar.?chat|_avChat\w*\s*=\s*\[\]|closeAv|_avShowChat|avOverlay', l) and l.strip():
        print(f"   {i+1}| {l.strip()[:110]}"); n += 1
        if n >= 16: break
