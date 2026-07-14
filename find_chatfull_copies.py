#!/usr/bin/env python3
"""find_chatfull_copies.py — READ-ONLY, capped. Every /api/chat/full handler, and in each: where
'message' is assigned (with indent) vs used bare — to find the copy that NameErrors. Aegis."""
import os, re
srv = os.path.expanduser("~/Vintos/server.py")
ls = open(srv, encoding="utf-8", errors="ignore").read().split("\n")
def indent(l): return len(l) - len(l.lstrip())

handlers = [i for i, l in enumerate(ls) if '/api/chat/full' in l and '@app' in l]
print(f"/api/chat/full handler copies: {[h+1 for h in handlers]}")
for h in handlers:
    end = next((j for j in range(h+2, len(ls)) if ls[j].startswith("@app")), min(h+780, len(ls)))
    print(f"\n--- copy @ L{h+1} (body to L{end}) ---")
    assigns = [(i, ls[i]) for i in range(h, end) if re.search(r'(?<![.\w])message\s*=(?!=)', ls[i])]
    uses = [(i, ls[i]) for i in range(h, end)
            if re.search(r'(?<![.\w"\'])message\b', ls[i]) and 'msg.message' not in ls[i]
            and '"message"' not in ls[i] and "'message'" not in ls[i] and not re.search(r'message\s*=(?!=)', ls[i])
            and not ls[i].lstrip().startswith('#')]
    for i, l in assigns: print(f"  ASSIGN L{i+1} (indent {indent(l)}): {l.strip()[:90]}")
    for i, l in uses[:8]: print(f"  USE    L{i+1} (indent {indent(l)}): {l.strip()[:90]}")
    if not assigns and uses:
        print("  ^^ THIS COPY uses 'message' but never assigns it -> the NameError")
