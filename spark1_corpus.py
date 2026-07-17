#!/usr/bin/env python3
"""spark1_corpus.py — Aegis. Spark #1 (Value Cost Network) corpus builder. Parses value-map.md into
(date, rank, value, why, evidence) examples, then embeds `value + ". " + why` via the local nomic endpoint.
Reads value-map.md READ-ONLY; writes only to ~/spark1-cost-network/. No LLM, no memory writes.

  python3 spark1_corpus.py --inspect   # discover format + verify parse + corpus stats (NO embedding)
  python3 spark1_corpus.py --embed      # parse + embed (batched, cached) -> corpus.jsonl + embeddings.npz
  --vm <path>   override value-map.md (default: Velaris's confirmed 128-day corpus)
"""
import os, re, sys, json, hashlib, urllib.request

HOME = os.path.expanduser("~")
VM = os.path.join(HOME, ".openclaw/workspace/memory/value-map.md")
for i, a in enumerate(sys.argv):
    if a == "--vm" and i + 1 < len(sys.argv): VM = os.path.expanduser(sys.argv[i + 1])
OUT = os.path.join(HOME, "spark1-cost-network")
NOMIC_URL = "http://172.18.16.1:1234/v1/embeddings"
NOMIC_MODEL = "text-embedding-nomic-embed-text-v1.5"

RANK_PATTERNS = [
    ("bold-num",  re.compile(r'(?m)^\s*\*\*\s*(\d+)[.).:\-—]\s*(.+?)\*\*')),
    ("head-num",  re.compile(r'(?m)^\s*#{1,5}\s*(\d+)[.).:\-—]\s*(.+)')),
    ("plain-num", re.compile(r'(?m)^\s*(\d+)[.)]\s+(.+)')),
    ("RANK-N",    re.compile(r'(?mi)^\s*RANK\s*(\d+)\s*[—:\-.]\s*(.+)')),
    ("dash-num",  re.compile(r'(?mi)^\s*(?:\*\*)?\s*(\d+)\s*[—:\-.]\s+(.+)')),
]
WHY = re.compile(r'(?is)Why[:\-—]\s*(.+?)(?:Evidence[:\-—]|\Z)')
EVID = re.compile(r'(?is)Evidence[:\-—]\s*(.+?)\Z')
DATE = re.compile(r'(\d{4}-\d{2}-\d{2})')

def split_entries(txt):
    idx = [m.start() for m in re.finditer(r'(?m)^#{1,3}\s+.*Value Map', txt)]
    if not idx: return []
    idx.append(len(txt))
    return [txt[idx[i]:idx[i+1]] for i in range(len(idx)-1)]

def choose_pattern(entries):
    best, best_score = None, -1
    for name, rx in RANK_PATTERNS:
        counts = [len(rx.findall(e)) for e in entries]
        good = sum(1 for c in counts if 3 <= c <= 9)   # entries with a plausible 3-9 ranked items
        score = good * 100 + sum(counts)
        if score > best_score: best, best_score, best_name = rx, score, name
    return best, best_name

def parse(txt):
    entries = split_entries(txt)
    rx, name = choose_pattern(entries)
    examples = []
    per_entry = []
    for e in entries:
        d = DATE.search(e)
        date = d.group(1) if d else None
        matches = list(rx.finditer(e))
        per_entry.append(len(matches))
        for j, m in enumerate(matches):
            rank = int(m.group(1))
            value = re.sub(r'\s+', ' ', m.group(2)).strip().strip('*').strip()
            block = e[m.end(): matches[j+1].start() if j+1 < len(matches) else len(e)]
            why_m = WHY.search(block); evid_m = EVID.search(block)
            why = re.sub(r'\s+', ' ', why_m.group(1)).strip()[:600] if why_m else ""
            evid = re.sub(r'\s+', ' ', evid_m.group(1)).strip()[:600] if evid_m else ""
            if value and 1 <= rank <= 12:
                examples.append({"date": date, "rank": rank, "value": value, "why": why, "evidence": evid})
    return examples, name, per_entry, entries

def pairs_count(examples):
    from collections import defaultdict
    byday = defaultdict(list)
    for ex in examples:
        if ex["date"]: byday[ex["date"]].append(ex)
    n = 0
    for day, rows in byday.items():
        ranks = [r["rank"] for r in rows]
        for a in range(len(ranks)):
            for b in range(len(ranks)):
                if ranks[a] < ranks[b]: n += 1
    return n, len(byday)

def main():
    if not os.path.isfile(VM):
        print(f"value-map.md not found: {VM}"); return
    txt = open(VM, encoding="utf-8", errors="ignore").read()
    examples, name, per_entry, entries = parse(txt)
    ndays = len([e for e in examples if e["date"]])
    dates = sorted({e["date"] for e in examples if e["date"]})
    npairs, uniq_days = pairs_count(examples)
    with_why = sum(1 for e in examples if e["why"])

    print(f"value-map.md: {VM.replace(HOME,'~')}  ({len(txt):,} B)")
    print(f"chosen rank pattern: {name}")
    print(f"daily entries: {len(entries)} | ranked examples: {len(examples)} | with Why: {with_why}")
    print(f"ranks/entry distribution: min={min(per_entry) if per_entry else 0} "
          f"max={max(per_entry) if per_entry else 0} avg={sum(per_entry)/max(1,len(per_entry)):.1f}")
    print(f"unique dated days: {uniq_days} | within-day training pairs: {npairs}")
    if dates: print(f"date range: {dates[0]} .. {dates[-1]}")
    print("\nsample parsed examples:")
    for e in examples[:4] + examples[-2:]:
        print(f"  [{e['date']}] rank {e['rank']}: {e['value'][:40]!r}  why={e['why'][:60]!r}")

    if "--inspect" in sys.argv or "--embed" not in sys.argv:
        print("\n=== one raw entry (verify the parse matches) ===")
        print(re.sub(r'\n{3,}', '\n\n', entries[-1].strip())[:1200] if entries else "(none)")
        print("\nINSPECT ONLY — no embedding. If the parse looks right, re-run with --embed.")
        return

    # --embed
    os.makedirs(OUT, exist_ok=True)
    cache_path = os.path.join(OUT, "embeddings-cache.json")
    cache = json.load(open(cache_path)) if os.path.isfile(cache_path) else {}
    def key(t): return hashlib.md5(t.encode()).hexdigest()
    texts = [f"{e['value']}. {e['why']}" for e in examples]
    todo = [t for t in dict.fromkeys(texts) if key(t) not in cache]
    print(f"\nembedding {len(todo)} new texts ({len(texts)-len(todo)} cached) via nomic ...")
    B = 32
    for i in range(0, len(todo), B):
        batch = todo[i:i+B]
        body = json.dumps({"model": NOMIC_MODEL, "input": batch}).encode()
        req = urllib.request.Request(NOMIC_URL, data=body, headers={"Content-Type": "application/json"})
        try:
            d = json.loads(urllib.request.urlopen(req, timeout=120).read())
        except Exception as ex:
            print(f"  ! embed batch {i} failed: {ex}"); return
        for t, item in zip(batch, d.get("data", [])):
            cache[key(t)] = item.get("embedding")
        json.dump(cache, open(cache_path, "w"))
        print(f"  {min(i+B,len(todo))}/{len(todo)}", end="\r", flush=True)
    dim = len(next(iter(cache.values()))) if cache else 0
    with open(os.path.join(OUT, "corpus.jsonl"), "w") as f:
        for e in examples:
            e2 = dict(e); e2["emb_key"] = key(f"{e['value']}. {e['why']}")
            f.write(json.dumps(e2, ensure_ascii=False) + "\n")
    print(f"\nOK — corpus.jsonl ({len(examples)} rows) + embeddings-cache.json ({len(cache)} vecs, dim {dim})")
    print(f"  in {OUT.replace(HOME,'~')}  — ready for the RankNet trainer (next step).")

main()
