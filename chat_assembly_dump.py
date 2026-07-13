#!/usr/bin/env python3
"""chat_assembly_dump.py — READ-ONLY, tight. Show the CHAT handler's system-prompt concatenation order.

The pieces are all loaded; the question is the ORDER they're joined into the final system prompt. This
locates the chat handler region (first SOUL/identity load after the API routes begin) and prints ONLY
the assembly lines there — the _ctx/_block vars, the system= concatenation, and the messages=[...] build
— verbatim with line numbers, so the true top-to-bottom order is visible. Bounded.
"""
import os, re

HOME = os.path.expanduser("~")
SERVERS = {
    "VINTOS":  os.path.join(HOME, "Vintos", "server.py"),
    "VELARIS": os.path.join(HOME, "velaris-server", "server.py"),
}

ASM = re.compile(
    r'(_ctx\b|_block\b|_subblock\b|\bsystem\s*=|\bsystem_prompt\b|\.join\(|messages\s*=|messages\.append'
    r'|content"\s*:\s*|role"\s*:\s*"(system|user|assistant)"|\bSOUL\b|load_soul|load_full_context'
    r'|value[-_]map|daily[-_]inner|preoccupation|emotional[-_]state|history\b|build_\w*context'
    r'|ask_llm|chat/completions|\+ *system|system *\+)')

def find_region(lines):
    """Start at the first place SOUL/identity is loaded after the routes begin; span ~420 lines."""
    start = None
    for i, ln in enumerate(lines):
        if i > 1800 and re.search(r'SOUL\.md|load_soul|load_full_context|YOUR IDENTITY', ln):
            start = i; break
    if start is None:
        start = 1900
    return max(0, start - 30), min(len(lines), start + 420)

def dump(name, path):
    print("\n########## %s : %s ##########" % (name, path.replace(HOME, "~")))
    if not os.path.exists(path):
        print("  not found"); return
    lines = open(path, encoding="utf-8", errors="ignore").read().splitlines()
    lo, hi = find_region(lines)
    print("  (scanning chat-handler region lines %d-%d, assembly lines only)\n" % (lo + 1, hi))
    shown = 0
    for i in range(lo, hi):
        ln = lines[i]
        if ASM.search(ln):
            s = ln.strip()
            if not s or s.startswith("#"): continue
            print("  %5d: %s" % (i + 1, s[:150]))
            shown += 1
            if shown >= 55:
                print("  ...(capped at 55 — enough to read the order)"); break
    if not shown:
        print("  (no assembly lines in region — widen the scan)")

for name, path in SERVERS.items():
    dump(name, path)
print("\n=== done. Read top->bottom: what leads the system prompt, and where history attaches. ===")
