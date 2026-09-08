#!/usr/bin/env python3
"""recon_purge_testturns.py — Aegis, READ-ONLY. Find every store the test emote-messages could be sitting
in (chat history, conversation-ledger, WAL, 'blush', merged history) and show the TAIL of each with
timestamps + role + a content preview, so we can pinpoint exactly which entries are the two test turns
before deleting anything. Also greps scripts for 'blush'/'ledger'/'wal' so we know what each store is."""
import os, re, json, glob
HOME = os.path.expanduser("~")
MEM = os.path.join(HOME, ".vintos/workspace/memory")
SC = os.path.join(HOME, ".vintos/workspace/scripts")
def sh(p): return p.replace(HOME, "~")

# 1) locate candidate stores by name
print("===== candidate store files (name match) =====")
pats = ["chat-history*", "*ledger*", "*.wal", "*blush*", "*conversation*", "*wal*"]
found = []
for base in (MEM, os.path.join(HOME, ".vintos/workspace"), SC):
    for pat in pats:
        for p in glob.glob(os.path.join(base, pat)) + glob.glob(os.path.join(base, "**", pat), recursive=True):
            if os.path.isfile(p) and p not in found and "node_modules" not in p:
                found.append(p)
for p in sorted(set(found)):
    print(f"   {os.path.getsize(p):>9}B  {sh(p)}")
if not found:
    print("   (none by those names — listing memory/ dir so we can spot them)")
    for e in sorted(os.listdir(MEM)):
        print("     ", e)

def preview(v, n=90):
    s = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
    s = re.sub(r"\s+", " ", s).strip()
    return (s[:n] + "…") if len(s) > n else s

def tail_json(p, k=6):
    try:
        obj = json.load(open(p, encoding="utf-8", errors="ignore"))
    except Exception as e:
        # maybe jsonl
        try:
            lines = [l for l in open(p, encoding="utf-8", errors="ignore").read().split("\n") if l.strip()]
            print(f"   (jsonl, {len(lines)} lines) last {k}:")
            for i, l in enumerate(lines[-k:]):
                try: d = json.loads(l)
                except Exception: print(f"     [{i}] {preview(l)}"); continue
                ts = d.get("timestamp") or d.get("ts") or d.get("time") or ""
                role = d.get("role") or d.get("speaker") or d.get("type") or ""
                body = d.get("content") or d.get("text") or d.get("message") or d
                print(f"     {ts} [{role}] {preview(body)}")
            return
        except Exception as e2:
            print(f"   (unreadable: {e} / {e2})"); return
    lst = obj if isinstance(obj, list) else obj.get("messages") or obj.get("history") or obj.get("entries") or []
    if not isinstance(lst, list):
        print(f"   (json {type(obj).__name__}, keys={list(obj)[:8] if isinstance(obj,dict) else ''}) — head: {preview(obj)}"); return
    print(f"   ({len(lst)} entries) last {k}:")
    for e in lst[-k:]:
        if not isinstance(e, dict): print(f"     {preview(e)}"); continue
        ts = e.get("timestamp") or e.get("ts") or e.get("time") or ""
        role = e.get("role") or e.get("speaker") or ""
        body = e.get("content") or e.get("text") or e.get("message") or e
        print(f"     {ts} [{role}] {preview(body)}")

for p in sorted(set(found)):
    print(f"\n===== TAIL: {sh(p)} =====")
    tail_json(p)

# 2) what is 'blush'? grep scripts
print("\n===== 'blush' / 'ledger' / 'wal' references in scripts (what each store IS) =====")
for kw in ("blush", "ledger", "\\.wal", "conversation-ledger"):
    hits = 0
    for f in glob.glob(os.path.join(SC, "*.py")) + glob.glob(os.path.join(SC, "*.sh")):
        for i, l in enumerate(open(f, encoding="utf-8", errors="ignore").read().split("\n")):
            if re.search(kw, l, re.I) and l.strip():
                print(f"   [{kw}] {os.path.basename(f)}:{i+1}| {l.strip()[:100]}")
                hits += 1
                if hits >= 4: break
        if hits >= 4: break
print("\n(done — paste this and I'll write the surgical purge)")
