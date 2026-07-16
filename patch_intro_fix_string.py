#!/usr/bin/env python3
"""patch_intro_fix_string.py — Aegis. Fix the pre-existing unterminated string in introspection.sh audit()
(line ~498: the "Below are two introspection drafts..." prompt lost its closing \\n"). Backup, re-compile the
embedded block, report if any MORE terminators are missing. Reversible."""
import os, re, time, shutil
P = os.path.expanduser("~/Vintos/introspection.sh")
if not os.path.isfile(P): print("introspection.sh not found"); raise SystemExit(1)
lines = open(P, encoding="utf-8").read().split("\n")

idx = [i for i, l in enumerate(lines) if "Below are two introspection drafts written by Vintos" in l]
if len(idx) != 1:
    print(f"target line x{len(idx)} (want 1) — aborting."); raise SystemExit(1)
i = idx[0]
if lines[i].rstrip().endswith('"'):
    print("line already terminated — the break is elsewhere; paste recon again."); raise SystemExit(0)
lines[i] = lines[i].rstrip() + '\\n"'
print(f"fixed L{i+1}: appended \\n\"  ->  ...{lines[i].strip()[-48:]}")

# re-extract the heredoc block and compile to catch any further breaks
di = next((k for k, l in enumerate(lines) if l.strip().startswith("def call_llm") or "def _claude_sync" in l), None)
op = next((k for k in range(di, -1, -1) if re.search(r"<<-?\s*'?\w+'?\s*$", lines[k])), None)
marker = re.search(r"<<-?\s*'?(\w+)'?\s*$", lines[op]).group(1)
cl = next((k for k in range(di, len(lines)) if lines[k].strip() == marker), len(lines))
block = "\n".join(lines[op+1:cl])
clean = True
try:
    compile(block, P, "exec")
    print("block COMPILES CLEAN now.")
except SyntaxError as e:
    clean = False
    fl = op + 1 + (e.lineno or 1)
    print(f"STILL another break at FILE line {fl}: {e.msg}")
    for n in range(max(0, fl-5), min(len(lines), fl+3)):
        print(("  >>" if n == fl-1 else "    ") + f" {n+1}: {lines[n][:110]}")

bak = P + ".bak-" + time.strftime("%Y%m%d-%H%M%S")
shutil.copy2(P, bak); open(P, "w", encoding="utf-8").write("\n".join(lines))
print(f"\nbackup: {bak}")
print("run:    bash ~/Vintos/introspection.sh" if clean else "  (fix the next line above, then re-run this style of fix)")
