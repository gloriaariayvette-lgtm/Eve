#!/usr/bin/env python3
"""spark1_corpus.py — Aegis. Spark #1 (Value Cost Network) corpus builder. Parses value-map.md into
(date, entry, rank, value, why, evidence) examples anchored on the `Why:` marker (present on every ranked
value across all the format variants), with position-in-entry as the within-day rank. Then embeds
`value + ". " + why` via the local nomic endpoint. Reads value-map.md READ-ONLY; writes only to
~/spark1-cost-network/.

  python3 spark1_corpus.py --inspect   # parse + verify + corpus stats (NO embedding)
  python3 spark1_corpus.py --embed      # parse + embed (batched, cached) -> corpus.jsonl + embeddings-cache.json
  --vm <path>   override value-map.md (default: Velaris's confirmed 128-day corpus)
"""
import os, re, sys, json, hashlib, urllib.request
from collections import defaultdict

HOME = os.path.expanduser("~")
VM = os.path.join(HOME, ".openclaw/workspace/memory/value-map.md")
for i, a in enumerate(sys.argv):
    if a == "--vm" and i + 1 < len(sys.argv): VM = os.path.expanduser(sys.argv[i + 1])
OUT = os.path.join(HOME, "spark1-cost-network")
NOMIC_URL = "http://172.18.16.1:1234/v1/embeddings"
NOMIC_MODEL = "text-embedding-nomic-embed-text-v1.5"

DATE = re.compile(r'(\d{4}-\d{2}-\d{2})')
WHYLINE = re.compile(r'(?im)^[ \t]*Why[ \t]*[:\-—]')
EVID = re.compile(r'(?is)Evidence[ \t]*[:\-—]\s*(.+)\Z')
LEAD = re.compile(r'^(?:#{1,5}\s*)?(?:\*\*)?\s*(?:RANK\s*)?(\d+)?\s*[—:).\-]*\s*', re.I)

def split_entries(txt):
    idx = [m.start() for m in re.finditer(r'(?m)^#{1,3}\s+.*Value Map', txt)]
    if not idx: return []
    idx.append(len(txt))
    return [txt[idx[i]:idx[i+1]] for i in range(len(idx)-1)]

def parse(txt):
    entries = split_entries(txt)
    examples, per_entry = [], []
    for ei, e in enumerate(entries):
        d = DATE.search(e); date = d.group(1) if d else None
        whys = list(WHYLINE.finditer(e))
        per_entry.append(len(whys))
        for pos, wm in enumerate(whys):
            name_line = next((ln.strip() for ln in reversed(e[:wm.start()].split("\n")) if ln.strip()), "")
            lm = LEAD.match(name_line)
            rk = int(lm.group(1)) if lm and lm.group(1) else None
            name = LEAD.sub("", name_line).strip().strip('*').strip()
            end = whys[pos+1].start() if pos+1 < len(whys) else len(e)
            block = e[wm.end():end]
            evid_m = EVID.search(block)
            why = re.sub(r'\s+', ' ', block[:evid_m.start()] if evid_m else block).strip()[:600]
            evid = re.sub(r'\s+', ' ', evid_m.group(1)).strip()[:600] if evid_m else ""
            rank = rk if rk is not None else (pos + 1)
            if name and len(name) <= 90:
                examples.append({"date": date, "entry": ei, "rank": rank, "value": name, "why": why, "evidence": evid})
    return examples, per_entry, entries

def pairs_count(examples):
    byentry = defaultdict(list)
    for ex in examples: byentry[ex["entry"]].append(ex)
    n = 0
    for rows in byentry.values():
        r = [x["rank"] for x in rows]
        n += sum(1 for a in range(len(r)) for b in range(len(r)) if r[a] < r[b])
    days = len({ex["date"] for ex in examples if ex["date"]})
    return n, len(byentry), days

def main():
    if not os.path.isfile(VM):
        print(f"value-map.md not found: {VM}"); return
    txt = open(VM, encoding="utf-8", errors="ignore").read()
    examples, per_entry, entries = parse(txt)
    npairs, nentries, ndays = pairs_count(examples)
    with_evid = sum(1 for e in examples if e["evidence"])

    print(f"value-map.md: {VM.replace(HOME,'~')}  ({len(txt):,} B)")
    print(f"daily entries (snapshots): {len(entries)} | calendar days: {ndays} | ranked examples: {len(examples)}")
    print(f"values/entry: min={min(per_entry) if per_entry else 0} max={max(per_entry) if per_entry else 0} "
          f"avg={sum(per_entry)/max(1,len(per_entry)):.1f} | with Evidence: {with_evid}")
    print(f"within-entry training pairs: {npairs}")
    print("\nsample parsed examples (first entry + last entry):")
    shown = 0
    for e in examples:
        if e["entry"] in (0, entries and len(entries)-1):
            print(f"  [{e['date']}] rank {e['rank']}: {e['value'][:44]!r}  why={e['why'][:52]!r}")
            shown += 1
        if shown >= 10: break

    if "--embed" not in sys.argv:
        print("\n=== one raw entry (verify names/ranks line up) ===")
        print(re.sub(r'\n{3,}', '\n\n', entries[-1].strip())[:1100] if entries else "(none)")
        print("\nINSPECT ONLY — no embedding. If the parse looks right, re-run with --embed.")
        return

    os.makedirs(OUT, exist_ok=True)
    cache_path = os.path.join(OUT, "embeddings-cache.json")
    cache = json.load(open(cache_path)) if os.path.isfile(cache_path) else {}
    key = lambda t: hashlib.md5(t.encode()).hexdigest()
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
            print(f"\n  ! embed batch at {i} failed: {ex}"); return
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
    print(f"  in {OUT.replace(HOME,'~')}  — ready for the RankNet trainer.")

main()
