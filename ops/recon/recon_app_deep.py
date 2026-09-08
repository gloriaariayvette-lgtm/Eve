#!/usr/bin/env python3
"""recon_app_deep.py — Mac, READ-ONLY. Nail 3/4/5: (3) avatar-chat open + message reset, (4) _avRemapClip
retarget + idle (T-pose root), (5) forgeSkin glow setup + how [COLOR] applies. Run in vintos-app."""
import os, re
IDX = os.path.join(os.getcwd(), "src/index.html")
L = open(IDX, encoding="utf-8", errors="ignore").read().split("\n")
def block(pat, span=22, cap=2, label=""):
    if label: print(f"\n=== {label} ===")
    n = 0
    for i, l in enumerate(L):
        if re.search(pat, l):
            for j in range(i, min(i+span, len(L))):
                if L[j].strip(): print(f"  {j+1}| {L[j].strip()[:114]}")
            print("  ---")
            n += 1
            if n >= cap: break
    if n == 0: print("  (no match)")

block(r'function _avRemapClip', 20, 1, "(4) _avRemapClip — bone retarget (T-pose if names mismatch)")
block(r'_avXbot\s*=|SkeletonUtils|\.skeleton|retarget|_avBoneMap|mixamorig', 4, 6, "(4) skeleton / bone names")
block(r'forgeSkin', 14, 3, "(5) forgeSkin glow material setup")
block(r'async function _avSpeakAndShow', 30, 1, "(5) _avSpeakAndShow — how `color` is used")
block(r'current-color|_avForge|forgeGlow|emissive.*color|\.emissive\.set|setHex', 3, 8, "(5) where color hits the glow")
block(r'function openAvatar|openAvatarOverlay|avatar-overlay|_avShowChat|avChatMsg|_avChatHistory\s*=|av-chat', 4, 10, "(3) avatar chat open + message reset")
