#!/usr/bin/env python3
"""verify_temp_infra.py — Aegis, READ-ONLY, capped. Check the 3 infrastructure claims the Gemini design
assumes, since that's where it would hallucinate:
  (1) the long-term semantic index — does embeddings.jsonl exist? real name + schema (is there a 'vector')?
  (2) thread-triage near-dup — embedding/cosine based (zero-overhead as claimed) or string based?
  (3) thread schema — do threads carry an embedding / event flags, or only dream_passes/mirror_passes?
Also: is the nomic embed endpoint the one to use if we must embed at triage?"""
import os, re, json, glob, subprocess
HOME = os.path.expanduser("~")
WS = os.path.join(HOME, ".vintos/workspace")
MEM = os.path.join(WS, "memory")
SC = os.path.join(WS, "scripts")
def sh(p): return p.replace(HOME, "~")

print("=== (1) the long-term semantic index (Gemini assumed embeddings.jsonl + h['vector']) ===")
cands = subprocess.run(["bash","-lc",
    f"find {WS} -maxdepth 3 -iname '*embedding*' -o -iname '*.jsonl' 2>/dev/null | grep -viE '\\.bak|node_modules|\\.pyc' | head -12"],
    capture_output=True, text=True).stdout.strip()
print("  candidate index files:", "\n    " + cands.replace(HOME,'~').replace(chr(10),'\n    ') if cands else "(none found)")
for f in [x for x in cands.split("\n") if x.strip()][:4]:
    try:
        sz = os.path.getsize(f)
        with open(f, encoding="utf-8", errors="ignore") as fh:
            first = fh.readline().strip()
        try:
            row = json.loads(first)
            keys = list(row.keys()) if isinstance(row, dict) else type(row).__name__
            veclen = next((len(row[k]) for k in ("vector","embedding","values","emb") if isinstance(row.get(k), list)), "?")
            print(f"    {sh(f)} ({sz}B)  keys={keys}  vector_len={veclen}")
        except Exception:
            print(f"    {sh(f)} ({sz}B)  (not json-lines; head: {first[:60]})")
    except Exception as e:
        print(f"    {sh(f)}: {e}")

print("\n=== (2) how thread-triage checks near-duplicates — embedding cosine or string? ===")
tt = os.path.join(SC, "thread-triage.py")
txt = open(tt, encoding="utf-8", errors="ignore").read() if os.path.isfile(tt) else ""
emb_signals = re.findall(r'(embed|cosine|nomic|similarity_gate|memory-search|\.dot\(|linalg|faiss|vector)', txt, re.I)
print("  embedding/cosine signals in thread-triage.py:", sorted(set(s.lower() for s in emb_signals)) or "(NONE — near-dup is string-based)")
for i, l in enumerate(txt.split("\n")):
    if re.search(r'near.?dup|similar|dedup|key =|\.strip\(\)|== .*thread|difflib|ratio', l, re.I) and l.strip() and not l.strip().startswith("#"):
        print(f"    {i+1:4}| {l.strip()[:100]}")
        if i > 140: break

print("\n=== how the semantic index is queried elsewhere (memory-search.py) ===")
ms = os.path.join(SC, "memory-search.py")
if os.path.isfile(ms):
    mtxt = open(ms, encoding="utf-8", errors="ignore").read()
    idx = re.findall(r'(embeddings\.jsonl|\.jsonl|faiss|nomic|/v1/embeddings|open\([^)]*\)|\.dot\(|cosine)', mtxt, re.I)
    print("  memory-search signals:", sorted(set(x.lower() for x in idx))[:10])
    for i, l in enumerate(mtxt.split("\n")):
        if re.search(r'jsonl|embeddings|/v1/embeddings|nomic|open\(.*embed|index', l, re.I) and l.strip() and not l.strip().startswith("#"):
            print(f"    {i+1:4}| {l.strip()[:100]}")
else:
    print("  (memory-search.py not found)")

print("\n=== (3) current thread schema (what fields exist to build on) ===")
try:
    obj = json.load(open(os.path.join(MEM, "unfinished-threads.json")))
    lst = obj if isinstance(obj, list) else obj.get("threads", [])
    allkeys = set()
    for t in lst:
        if isinstance(t, dict): allkeys |= set(t.keys())
    print("  union of thread keys:", sorted(allkeys))
    print("  has embedding?", "embedding" in allkeys, "| has dream_passes?", "dream_passes" in allkeys,
          "| mirror_passes?", "mirror_passes" in allkeys, "| temperature?", "temperature" in allkeys)
except Exception as e:
    print("  (couldn't read threads)", e)

print("\n=== embed endpoint to use if we must embed at triage ===")
hits = subprocess.run(["bash","-lc",
    f"grep -rhoE 'http://[0-9.]+:[0-9]+/v1/embeddings|nomic-embed-text|EMBED_URL *= *\"[^\"]+\"' {SC} 2>/dev/null | sort -u | head"],
    capture_output=True, text=True).stdout.strip()
print("  " + (hits.replace(chr(10),'\n  ') or "(no embed endpoint referenced)"))
