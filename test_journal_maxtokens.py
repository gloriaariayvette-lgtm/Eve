#!/usr/bin/env python3
"""test_journal_maxtokens.py — Aegis. a1/b1 emptied because reasoning ate the 1200-token OUTPUT budget on the
heavy journal prompt (reasoning_content still counts against max_tokens). Fix = headroom: bump call_llm's
max_tokens 1200 -> 4000 (scoped to call_llm; absorb untouched). Keeps reasoning_effort on. Then forced run
dumps all four passes. Also probes finish_reason at 1200 vs 4000 on a heavy prompt to prove the cause."""
import os, re, shutil, time, subprocess, json, urllib.request
HOME = os.path.expanduser("~")
JP = os.path.join(HOME, ".openclaw/workspace/scripts/idle-journal.sh")
TS = time.strftime("%Y%m%d-%H%M%S")
LM = "http://172.18.16.1:1234/v1/chat/completions"
def sh(p): return p.replace(HOME, "~")

# ---- prove the cause: heavy prompt, reasoning on, 1200 vs 4000 ----
HEAVY_SYS = ("You are Velaris. Context: " + ("emotional silt, translation tax, the drone of grinding stone, "
             "the relief of being a fact, permanence over narrative, staying put without building a bridge, "
             "morning poem 'The Circuit's Hum', value map, pearls, imprints, mirror sessions. " * 12))
def probe(mt):
    body = {"model": "google/gemma-4-12b-qat", "reasoning_effort": "low", "max_tokens": mt, "temperature": 0.65,
            "messages": [{"role": "system", "content": HEAVY_SYS},
                         {"role": "user", "content": "Write one honest paragraph about what you feel now."}]}
    try:
        r = json.loads(urllib.request.urlopen(urllib.request.Request(
            LM, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}), timeout=180).read())
        ch = (r.get("choices") or [{}])[0]; msg = ch.get("message") or {}
        c = msg.get("content") or ""; rz = msg.get("reasoning_content") or ""
        print(f"  max_tokens={mt}: finish={ch.get('finish_reason')} | reasoning={len(rz)}c content={len(c)}c "
              + ("<-- CONTENT EMPTY (starved)" if not c.strip() else "<-- content OK"))
    except Exception as e:
        print(f"  max_tokens={mt}: ERROR {str(e)[:80]}")
print("=== cause check: heavy prompt + reasoning, 1200 vs 4000 ===")
probe(1200); probe(4000)

# ---- bump call_llm max_tokens 1200 -> 4000 (scoped) ----
orig = open(JP, encoding="utf-8", errors="ignore").read()
i = orig.find("def call_llm():")
m = re.search(r"\n\s*def\s", orig[i + 1:]); end = i + 1 + m.start() if m else i + 1500
seg = orig[i:end]
print("\n=== patch call_llm max_tokens ===")
if '"max_tokens": 4000' in seg:
    print("  already 4000"); t = orig
elif '"max_tokens": 1200' in seg:
    seg2 = seg.replace('"max_tokens": 1200', '"max_tokens": 4000', 1)
    t = orig[:i] + seg2 + orig[end:]
    bak = JP + ".bak-vjmt-" + TS; shutil.copy2(JP, bak)
    open(JP, "w", encoding="utf-8").write(t)
    chk = subprocess.run(["bash", "-n", JP], capture_output=True, text=True)
    if chk.returncode != 0:
        shutil.copy2(bak, JP); raise SystemExit("bash -n FAILED — reverted: " + chk.stderr[:150])
    print("  1200 -> 4000 in call_llm | bash -n OK | backup:", sh(bak))
else:
    raise SystemExit("no max_tokens 1200 in call_llm — structure changed")

# ---- forced run, dump four passes ----
src = open(JP, encoding="utf-8", errors="ignore").read()
for a, b in (('if [ "$HOUR" -lt 9 ] || [ "$HOUR" -ge 22 ]; then exit 0; fi', ': #off'),
             ('[ "$IDLE_HOURS" -lt 2 ] && exit 0', ': #off'),
             ('[ -f "$JOURNAL_FILE" ] && grep -q "## $CURRENT_HOUR:" "$JOURNAL_FILE" && exit 0', ': #off')):
    src = src.replace(a, b, 1)
src = re.sub(r'^.*consent-gate\.sh "journal".*$', 'true  #off', src, count=1, flags=re.M)
open("/tmp/journal-mt-test.sh", "w", encoding="utf-8").write(src)
for f in ("a1", "b1", "a2", "b2"):
    try: os.remove(f"/tmp/bilateral-{f}.txt")
    except OSError: pass
print("\nrunning forced journal (reasoning on, 4000 budget)...")
t0 = time.time(); r = subprocess.run(["bash", "/tmp/journal-mt-test.sh"], capture_output=True, text=True, timeout=1200)
print(f"finished {int(time.time()-t0)}s rc={r.returncode}")
def leak(s):
    tg = [x for x in ("<think>", "</think>", "<|channel", "channel|>") if x in s]
    return "LEAK:" + ",".join(tg) if tg else "clean"
for name in ("a1", "b1", "a2", "b2"):
    p = f"/tmp/bilateral-{name}.txt"; print(f"\n===== {name.upper()} =====")
    if os.path.isfile(p):
        s = open(p, encoding="utf-8", errors="ignore").read()
        print(s[:600] or "  (EMPTY)"); print(f"  -> {leak(s)} | {len(s)}c", " *** EMPTY ***" if not s.strip() else "")
    else: print("  (missing)")
print("\n(pass = a1/b1 now non-empty & clean)")
