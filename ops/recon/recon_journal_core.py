#!/usr/bin/env python3
"""recon_journal_core.py — Aegis, READ-ONLY. Print the LLM-call helper + the final-synthesis call for
idle-journal.sh and introspection.sh, so a1/b1 -> Claude-reasoning + Claude-final can be spliced (sync
requests path). Bounded."""
import os, re, glob
HOME = os.path.expanduser("~")
VDIR = os.path.join(HOME, "Vintos")

def show(name, helper_rx, final_terms):
    p = os.path.join(VDIR, name)
    if not os.path.isfile(p): print(f"=== {name}: not found ==="); return
    L = open(p, encoding="utf-8", errors="ignore").read().split("\n")
    print(f"\n########## {name} ({len(L)} lines) ##########")
    # helper: first requests.post/def call_llm/def run + ~18 lines
    hi = next((i for i, l in enumerate(L) if helper_rx.search(l)), None)
    if hi is not None:
        print(f"--- call helper @ L{hi+1} ---")
        for n in range(hi, min(hi+22, len(L))):
            print(f"{n+1}: {L[n][:104]}")
    # final synthesis: last region mentioning integration/synthesis/carrying both + the reply
    fi = None
    for i, l in enumerate(L):
        if any(t in l for t in final_terms): fi = i
    if fi is not None:
        lo = max(0, fi-6)
        print(f"--- final synthesis region @ L{lo+1}-{min(fi+40, len(L))} ---")
        for n in range(lo, min(fi+40, len(L))):
            print(f"{n+1}: {L[n][:104]}")

show("idle-journal.sh", re.compile(r'def call_llm|def _call|requests\.post\("https://api\.x\.ai'),
     ["integration", "synthesis", "carrying both", "final response", "Both of these are true"])
show("introspection.sh", re.compile(r'def run\(|def _call|def call'),
     ["integration", "synthesis", "carrying both", "final synthesis", "Both of these are true"])
