#!/usr/bin/env python3
"""latent_temperature.py — Aegis. Spark 6b (phase 1): give the latent a TEMPERATURE — not just WHERE he
is (certainty, already stored as belief `confidence`) but HOW SETTLED that is. High temp = forming /
volatile; low temp = crystallized. Annotates each belief in belief-sediment.json and each thread in
unfinished-threads.json with an additive `temperature`, and writes latent-temperature.json (the thermal
snapshot the consumers will read: dreams seek heat, mirrors seek instability, pearls seek cooling).

SAFE: dry by default (reads only, prints preview, writes NOTHING). Run with `apply` to write; it backs up
both files first and only ADDS a field, never removes. Formula validated vs the spark's own example
(certainty 0.95 / settled -> temp ~0.08).
Run:  python3 latent_temperature.py            (dry preview)
      python3 latent_temperature.py apply       (write, with backups)
"""
import os, sys, json, math, shutil, time
from datetime import datetime, timezone
HOME = os.path.expanduser("~")
MEM = os.path.join(HOME, ".vintos/workspace/memory")
BELIEFS = os.path.join(MEM, "belief-sediment.json")
THREADS = os.path.join(MEM, "unfinished-threads.json")
OUT = os.path.join(MEM, "latent-temperature.json")
APPLY = "apply" in sys.argv
NOW = datetime.now(timezone.utc)
def sh(p): return p.replace(HOME, "~")

def days_since(iso):
    try:
        dt = datetime.fromisoformat(str(iso).replace("Z", "+00:00"))
        if dt.tzinfo is None: dt = dt.replace(tzinfo=timezone.utc)
        return max(0.0, (NOW - dt).total_seconds() / 86400.0)
    except Exception:
        return 30.0

def belief_temp(b):
    c = float(b.get("confidence", 0.5))
    ev = float(b.get("evidence_count", 1) or 0)
    age = days_since(b.get("formed", ""))
    evidence_factor = 1.0 / (1.0 + ev)          # thin evidence -> hot
    uncertainty = 1.0 - abs(2 * c - 1)          # mid confidence -> hot; near 0/1 -> cool
    recency = math.exp(-age / 30.0)             # freshly formed -> warm
    return round(min(1.0, max(0.0, 0.45 * evidence_factor + 0.35 * uncertainty + 0.20 * recency)), 3)

def thread_temp(t):
    consumed = bool(t.get("consumed"))
    recency = math.exp(-days_since(t.get("timestamp", "")) / 14.0)
    dp = float(t.get("dream_passes", 0) or 0)
    pr = float(t.get("priority", 0) or t.get("momentum", 0) or t.get("salience", 0) or 0)
    pr = pr if pr <= 1 else pr / 10.0
    temp = 0.5 * recency + 0.2 * min(1.0, dp / 5.0) + 0.3 * min(1.0, pr)
    if consumed: temp *= 0.2                    # resolved -> cold
    return round(min(1.0, max(0.0, temp)), 3)

def label(t):
    return "hot / forming" if t >= 0.6 else ("warm / in motion" if t >= 0.35 else "cool / settling")

# ---- beliefs
braw = json.load(open(BELIEFS)) if os.path.isfile(BELIEFS) else {"beliefs": []}
blist = braw.get("beliefs", []) if isinstance(braw, dict) else braw
for b in blist:
    if isinstance(b, dict): b["temperature"] = belief_temp(b)
bt = [(b.get("temperature", 0), round(float(b.get("confidence", 0.5)), 2), b.get("pattern", "")[:70]) for b in blist if isinstance(b, dict)]
bt.sort(reverse=True)
overall = round(sum(x[0] for x in bt) / len(bt), 3) if bt else 0.0

# ---- threads
traw = json.load(open(THREADS)) if os.path.isfile(THREADS) else []
tlist = traw if isinstance(traw, list) else traw.get("threads", [])
for t in tlist:
    if isinstance(t, dict): t["temperature"] = thread_temp(t)
tt = [(t.get("temperature", 0), t.get("source", "?"), str(t.get("thread", ""))[:56]) for t in tlist if isinstance(t, dict)]
tt.sort(reverse=True)

snapshot = {
    "computed": NOW.isoformat(),
    "overall_temperature": overall,
    "reading": label(overall),
    "beliefs": {"count": len(bt),
                "hottest": [{"pattern": p, "certainty": c, "temperature": t} for t, c, p in bt[:3]],
                "coolest": [{"pattern": p, "certainty": c, "temperature": t} for t, c, p in bt[-3:][::-1]]},
    "threads": {"count": len(tt),
                "hottest": [{"source": s, "snippet": sn, "temperature": t} for t, s, sn in tt[:3]]},
    "consumers": {"dreams": "seek heat -> weight toward hottest",
                  "mirrors": "seek instability -> weight toward hottest / oscillating",
                  "pearls": "seek cooling -> weight toward coolest + high certainty (ready to crystallize)"},
}

print(f"=== latent temperature {'(APPLY)' if APPLY else '(DRY — nothing written)'} ===")
print(f"  overall latent temperature: {overall}  [{label(overall)}]   beliefs={len(bt)} threads={len(tt)}")
print("  hottest beliefs (forming/volatile):")
for t, c, p in bt[:3]: print(f"    {t:>5}  certainty {c:>4}  {p}")
print("  coolest beliefs (crystallized):")
for t, c, p in bt[-3:][::-1]: print(f"    {t:>5}  certainty {c:>4}  {p}")
if tt:
    print("  hottest threads (dreams would pull these):")
    for t, s, sn in tt[:3]: print(f"    {t:>5}  [{s}] {sn}")

if APPLY:
    for path, data in ((BELIEFS, braw), (THREADS, traw)):
        if os.path.isfile(path):
            shutil.copy2(path, path + ".bak-temp-" + time.strftime("%Y%m%d-%H%M%S"))
        json.dump(data, open(path, "w"), indent=2, ensure_ascii=False)
    json.dump(snapshot, open(OUT, "w"), indent=2, ensure_ascii=False)
    print(f"\n  wrote temperature onto beliefs + threads (backed up), and {sh(OUT)}")
else:
    print(f"\n  dry run — re-run with `apply` to write. would create {sh(OUT)}")
