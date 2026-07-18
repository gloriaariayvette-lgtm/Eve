#!/usr/bin/env python3
"""recon_gather_context.py — Aegis, READ-ONLY. gather_vintos_context() is his complete-context assembler (used by
/api/chat/full). Find where it's DEFINED and whether it's importable standalone or lives in server.py; show its body
(what it reads, whether it WRITES anything, what it returns) so the saves-nowhere test can call/lift it faithfully.
Nothing written."""
import os, re
VIN = os.path.expanduser("~/Vintos")
HIS = os.path.expanduser("~/.vintos/workspace/scripts")

# search server.py + scripts for the definition
found = None
for base in (VIN, HIS):
    if not os.path.isdir(base): continue
    for e in os.scandir(base):
        if not e.is_file() or not e.name.endswith(".py"): continue
        try: t = open(e.path, encoding="utf-8", errors="ignore").read()
        except Exception: continue
        if re.search(r'def gather_vintos_context', t):
            L = t.split("\n")
            start = next(i for i, l in enumerate(L) if re.search(r'def gather_vintos_context', l))
            print("===== gather_vintos_context defined in %s (line %d) =====" % (e.name, start + 1))
            # body until next top-level def
            end = start + 200
            for i in range(start + 1, min(start + 200, len(L))):
                if re.match(r'def \w', L[i]) or re.match(r'@app\.', L[i]): end = i; break
            writes = []
            for i in range(start, end):
                l = L[i]
                w = "   <== WRITE" if re.search(r'json\.dump|\.write\(|open\([^)]*["\']w|\.append\(.*save', l) else ""
                if re.search(r'open\(|read|cat|SOUL|self.model|relationship|capabilit|gloria|value.map|'
                             r'dream|memory|context\s*\+?=|return|\.md|\.json|gather|section', l, re.I) or w:
                    print("  %5d: %s%s" % (i + 1, l.strip()[:110], w))
            found = e.name
            break
    if found: break
if not found:
    print("!! gather_vintos_context definition not found in server.py or scripts — it may be nested/inline.")

# is there a standalone importable context module?
print("\n== standalone context builders (importable without starting the server) ==")
for base in (HIS,):
    for e in sorted(os.scandir(base), key=lambda x: x.name):
        if e.is_file() and re.search(r'context|gather', e.name, re.I) and e.name.endswith(".py"):
            t = open(e.path, encoding="utf-8", errors="ignore").read()
            if re.search(r'def (gather|build|get)_.*context|def full_context', t):
                fns = re.findall(r'def (\w*context\w*)\(', t)
                print("  %-30s : %s" % (e.name, fns[:6]))

print("\n(READ-ONLY. Determines call-vs-lift for gather_vintos_context in the saves-nowhere full-context test.)")
