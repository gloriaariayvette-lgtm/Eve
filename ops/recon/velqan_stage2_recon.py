#!/usr/bin/env python3
"""velqan_stage2_recon.py — READ-ONLY, capped. Ground Stage 2 (Velqan into journal/introspection, not
chat). Show: Vintos's journal + introspection prompt assembly (where to inject a velqan block), how
Velaris injects Velqan into HER journal/introspection (pattern to mirror), and the coiner's LLM call +
write targets (to port grok-side). Aegis."""
import os, re, glob, subprocess
HOME = os.path.expanduser("~")
TS = os.path.expanduser("~/.vintos/workspace/scripts")
VIN = os.path.expanduser("~/Vintos")
VS = os.path.expanduser("~/.openclaw/workspace/scripts")
def run(a): return subprocess.run(a, capture_output=True, text=True).stdout
def peek(p, pat, cap):
    if not os.path.isfile(p): print("  (missing)", p.replace(HOME,'~')); return
    print(f"-- {p.replace(HOME,'~')} --"); n=0
    for i,l in enumerate(open(p,encoding='utf-8',errors='ignore').read().split("\n")):
        if re.search(pat,l,re.I) and l.strip() and not l.strip().startswith("#"):
            print(f"  {i+1:4}| {l.strip()[:130]}"); n+=1
            if n>=cap: break

print("=== (1) Vintos journal + introspection scripts (prompt assembly / context) ===")
for name in ("idle-journal.sh", "introspection.sh", "introspection.py"):
    for base in (VIN, TS):
        p = os.path.join(base, name)
        if os.path.isfile(p):
            peek(p, r'prompt|system|context|SOUL|self-model|value-map|journal|reference|cat |read_file|append|sections|PROMPT', 12); break

print("\n=== (2) does Velaris put Velqan into her journal/introspection? (pattern to mirror) ===")
hits = run(["bash","-lc", f"grep -rlnE 'velqan' {VS} 2>/dev/null | grep -iE 'journal|introspect|reflect|inner|idle' | grep -viE '\\.pyc|\\.bak'"]).split()
print("  files:", [os.path.basename(h) for h in hits] or "(velqan not wired into her journal/introspection either — I'll design it)")
for h in hits[:2]:
    peek(h, r'velqan|reference|lexicon|coinage', 8)

print("\n=== (3) velqan-coiner.py: LLM endpoint + where it writes ===")
peek(os.path.join(VS, "velqan-coiner.py"), r'172\.18|api\.x\.ai|/v1/|localhost|:1234|model|endpoint|requests\.post|subprocess|ask_llm|open\(.*[\'"]w|append|dump\(', 20)
