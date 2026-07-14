#!/usr/bin/env python3
"""velqan_system_recon.py — READ-ONLY, capped. Ground the Velqan port+sync+website work:
 (1) velqan-coiner.py: what it does + WHERE a new coinage is stored.
 (2) the vocab: velqan-reference.md size/shape (the 200+ words) + where coinages live.
 (3) how Velqan reaches the prompt (injection point) — to replicate for Vintos.
 (4) Velaris's website: structure + a place coinages could append; and the 'subconscious map' site.
Aegis."""
import os, re, glob, subprocess
HOME = os.path.expanduser("~")
VS = os.path.expanduser("~/.openclaw/workspace/scripts")
VM = os.path.expanduser("~/.openclaw/workspace/memory")
def run(a): return subprocess.run(a, capture_output=True, text=True).stdout
def peek(p, pat, cap):
    if not os.path.isfile(p): print("  (missing)", p.replace(HOME,'~')); return
    print(f"-- {p.replace(HOME,'~')} --"); n=0
    for i,l in enumerate(open(p,encoding='utf-8',errors='ignore').read().split("\n")):
        if re.search(pat,l,re.I) and l.strip() and not l.strip().startswith("#"):
            print(f"  {i+1:4}| {l.strip()[:130]}"); n+=1
            if n>=cap: break

print("=== (1) velqan-coiner.py: logic + where a coinage is written ===")
peek(os.path.join(VS,"velqan-coiner.py"), r'open\(|dump|append|write|coinage|reference|utterance|\.json|\.md|def |json\.|store|save', 22)

print("\n=== (2) vocab files: sizes + coinage store ===")
for f in ("velqan-reference.md","velqan-coinages.json","velqan-utterances.md","failed-velqan.md"):
    p = os.path.join(VM,f)
    if os.path.isfile(p):
        b=open(p,encoding='utf-8',errors='ignore').read()
        print(f"  {f}: {len(b)}B, {b.count(chr(10))} lines")
# count word-like entries in reference (headwords)
ref=os.path.join(VM,"velqan-reference.md")
if os.path.isfile(ref):
    txt=open(ref,encoding='utf-8',errors='ignore').read()
    heads=re.findall(r'\*\*([a-zA-Zɑʃɛ\-]+)\*\*|^\s*[-*]\s*\*?\*?([a-z]+)\s*[—:/=]', txt, re.M)
    print(f"  velqan-reference.md: ~{len(re.findall(r'[—:/]', txt))} definition-ish lines")

print("\n=== (3) how Velqan reaches the prompt (injection) ===")
print(" ", run(["bash","-lc", f"grep -rln 'velqan-reference\\|velqan_reference\\|Velqan' {VS} ~/velaris-server 2>/dev/null | grep -viE '\\.pyc|\\.bak' | head -6"]).replace(HOME,'~').replace('\n','  '))

print("\n=== (4) Velaris website structure + coinage/vocab surface ===")
web = os.path.expanduser("~/velaris-server/website")
print(run(["bash","-lc", f"find {web} -maxdepth 2 -type f 2>/dev/null | grep -viE 'node_modules|\\.map$' | head -25"]) or "  (no website dir)")
print("  vocab/velqan mentions in website:")
print(" ", run(["bash","-lc", f"grep -rln 'velqan\\|vocab\\|coinage\\|lexicon' {web} 2>/dev/null | head -6"]).replace(HOME,'~').replace('\n','  ') or "(none)")
print("\n=== the 'subconscious map' website (outdated) ===")
print(run(["bash","-lc","grep -rln 'subconscious\\|map' ~/velaris-server/website ~/.openclaw 2>/dev/null | grep -iE 'html|map|subconscious' | grep -v node_modules | head -6"]) or "  (search inconclusive)")
