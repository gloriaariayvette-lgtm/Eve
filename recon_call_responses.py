#!/usr/bin/env python3
"""recon_call_responses.py — Mac, READ-ONLY. For call-button active state + result-based feedback:
avStartVoiceCall + call-state vars, full avDeviceStop + avGCS (response handling), av-call-btn element."""
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
            print("  ---"); n += 1
            if n >= cap: break
    if n == 0: print("  (no match)")
block(r'function avStartVoiceCall', 24, 1, "avStartVoiceCall (call button handler)")
block(r'avEndCall|endVoiceCall|hangup|_avCall|callActive|inCall|_avPC|RTCPeer', 3, 8, "call state / end")
block(r'function avDeviceStop', 12, 1, "avDeviceStop (full)")
block(r'function avGCS', 10, 1, "avGCS (full)")
print("\n=== av-call-btn element ===")
for i, l in enumerate(L):
    if "av-call-btn" in l: print(f"  {i+1}| {l.strip()[:130]}")
