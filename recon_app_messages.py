#!/usr/bin/env python3
"""recon_app_messages.py — Mac, READ-ONLY. Why aren't messages appearing? Dump the avatar-chat message
display path: _avShowBubble/_avHideBubble, the av-chat-strip element + anything that writes to it,
avSendChat, and the keep-messages reopen edit. Run in vintos-app."""
import os, re
IDX = os.path.join(os.getcwd(), "src/index.html")
L = open(IDX, encoding="utf-8", errors="ignore").read().split("\n")
def block(pat, span=20, cap=2, label=""):
    if label: print(f"\n=== {label} ===")
    n = 0
    for i, l in enumerate(L):
        if re.search(pat, l):
            for j in range(i, min(i+span, len(L))):
                if L[j].strip(): print(f"  {j+1}| {L[j].strip()[:112]}")
            print("  ---"); n += 1
            if n >= cap: break
    if n == 0: print("  (no match)")
block(r'function _avShowBubble', 16, 1, "_avShowBubble (how a message bubble is shown)")
block(r'function _avHideBubble', 8, 1, "_avHideBubble (when it disappears)")
block(r'function avSendChat', 20, 1, "avSendChat (sending a typed message)")
block(r'id="av-chat-strip"', 3, 1, "av-chat-strip element")
block(r'av-chat-strip|avChatStrip|chatStrip|renderStrip', 3, 6, "anything writing to the chat strip")
block(r'reverse\(\).find\(m=>m.role', 6, 1, "my keep-messages reopen edit (is it present?)")
print("\n=== the bubble element + its CSS (does it render offscreen / hidden?) ===")
for i, l in enumerate(L):
    if re.search(r'av-bubble|avBubble|_avBubble|bubble\.style|createElement.*bubble|id.*bubble', l) and l.strip():
        print(f"  {i+1}| {l.strip()[:110]}")
        if i > 3100: break
