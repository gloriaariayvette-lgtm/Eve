#!/usr/bin/env python3
"""test_journal_reasoning_retry.py — Aegis. Reasoning parses fine on this LMS (probe proved it); the empty
a1/b1 was the odd call blipping under load. Fix is code-side: turn reasoning on for a1/b1 (reasoning_effort,
the on-switch — value barely matters) AND retry if a call comes back empty. Only touches call_llm (a1/b1;
absorb is separate). Then run a forced journal (temp copy past the gates) and DUMP all four passes so Gloria
can see a1/a2/b1/b2. Backup + bash -n + revert-on-failure. Live file stays patched (test bed)."""
import os, re, shutil, time, subprocess
HOME = os.path.expanduser("~")
JP = os.path.join(HOME, ".openclaw/workspace/scripts/idle-journal.sh")
TS = time.strftime("%Y%m%d-%H%M%S")
def sh(p): return p.replace(HOME, "~")

orig = open(JP, encoding="utf-8", errors="ignore").read()
t = orig
notes = []

# (a) reasoning ON for call_llm (scoped to its own model line)
i = t.find("def call_llm():")
if i < 0:
    raise SystemExit("def call_llm() not found")
m = re.search(r"\n\s*def\s", t[i + 1:]); end = i + 1 + m.start() if m else i + 1500
seg = t[i:end]
if "reasoning_effort" in seg:
    notes.append("reasoning_effort already on call_llm")
else:
    mm = re.search(r'"model":\s*"google/gemma-4-12b-qat",', seg)
    if not mm:
        raise SystemExit("no model line inside call_llm()")
    seg = seg[:mm.end()] + '"reasoning_effort":"low",' + seg[mm.end():]
    t = t[:i] + seg + t[end:]
    notes.append("reasoning_effort:low added to call_llm (the on-switch)")

# (b) retry on empty — ONLY the a1/b1 first-pass call sites
for var in ("a1", "b1"):
    old = f"{var} = call_llm()"
    new = f"{var} = (call_llm() or call_llm() or call_llm())"
    if new in t:
        notes.append(f"{var} retry already present")
    elif t.count(old) == 1:
        t = t.replace(old, new, 1); notes.append(f"{var}: retry-on-empty added (up to 3 tries)")
    else:
        notes.append(f"!! {var} call-site anchor {t.count(old)}x — skipped")

print("=== patch idle-journal.sh ===")
for n in notes: print("  -", n)
if t != orig:
    bak = JP + ".bak-vjretry-" + TS
    shutil.copy2(JP, bak)
    open(JP, "w", encoding="utf-8").write(t)
    chk = subprocess.run(["bash", "-n", JP], capture_output=True, text=True)
    if chk.returncode != 0:
        shutil.copy2(bak, JP); raise SystemExit("bash -n FAILED — reverted: " + chk.stderr[:160])
    print("  bash -n OK | backup:", sh(bak), "| revert: cp that backup over idle-journal.sh")

# ---- forced test run (temp copy, gates neutralized) ----
src = open(JP, encoding="utf-8", errors="ignore").read()
for old, new in (
    ('if [ "$HOUR" -lt 9 ] || [ "$HOUR" -ge 22 ]; then exit 0; fi', ': # hour gate off'),
    ('[ "$IDLE_HOURS" -lt 2 ] && exit 0', ': # idle gate off'),
    ('[ -f "$JOURNAL_FILE" ] && grep -q "## $CURRENT_HOUR:" "$JOURNAL_FILE" && exit 0', ': # hour-dup off')):
    src = src.replace(old, new, 1)
src = re.sub(r'^.*consent-gate\.sh "journal".*$', 'true  # consent off', src, count=1, flags=re.M)
TMP = "/tmp/journal-retry-test.sh"
open(TMP, "w", encoding="utf-8").write(src)
for f in ("a1", "b1", "a2", "b2"):
    try: os.remove(f"/tmp/bilateral-{f}.txt")
    except OSError: pass

print("\nrunning forced journal (reasoning on + retry; may take several min)...")
t0 = time.time()
r = subprocess.run(["bash", TMP], capture_output=True, text=True, timeout=1200)
print(f"finished {int(time.time()-t0)}s rc={r.returncode}")
if r.stderr.strip(): print("stderr tail:", r.stderr.strip()[-300:])

def leak(s):
    tg = [x for x in ("<think>", "</think>", "channel|>", "|channel>", "<|channel") if x in s]
    return "LEAK: " + ",".join(tg) if tg else "clean"

for name in ("a1", "b1", "a2", "b2"):
    p = f"/tmp/bilateral-{name}.txt"
    print(f"\n===== {name.upper()} ({p}) =====")
    if os.path.isfile(p):
        s = open(p, encoding="utf-8", errors="ignore").read()
        print(s[:650] or "  (EMPTY)")
        print(f"  -> {leak(s)} | {len(s)} chars", "  *** EMPTY ***" if not s.strip() else "")
    else:
        print("  (file missing)")
print("\n(pass = all four non-empty + clean; a1/b1 are the reasoned first-passes)")
