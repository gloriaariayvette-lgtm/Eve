#!/usr/bin/env python3
"""patch_velaris_chat_thinking.py — Aegis. Velaris CHAT context: give reasoning_effort:high to ONLY the
bilateral a1/b1 first-passes in her chat server (~/velaris-server/server.py). absorb/held/integration and
everything else stay no-think. Two helpers (_llm_call x2 defs, _llm_call_full x2 defs); four a1/b1 gather
sites (2557, 7595 via _llm_call; 4881, 11475 via _llm_call_full).

Steps: (1) add reason=False to both helper signatures, (2) inject conditional reasoning_effort into each
helper's json payload, (3) flip reason=True on the four gather() first-pass calls only.
Backup + py_compile + rollback + idempotent. Prints every step."""
import os, re, shutil, time, py_compile
P = "/home/gloria/velaris-server/server.py"
TS = time.strftime("%Y%m%d-%H%M%S")
def sh(p): return p.replace(os.path.expanduser("~"), "~")
if not os.path.isfile(P):
    raise SystemExit("not found: " + P)
orig = open(P, encoding="utf-8", errors="ignore").read()
t = orig
notes = []

# (1) helper signatures -> add reason=False
a = "async def _llm_call(msgs, temp=None):"
if "async def _llm_call(msgs, temp=None, reason=False):" in t:
    notes.append("_llm_call def already has reason")
    llm_ok = True
else:
    c = t.count(a)
    t = t.replace(a, "async def _llm_call(msgs, temp=None, reason=False):")
    notes.append(f"_llm_call def: added reason to {c} def(s)")
    llm_ok = c >= 1

# _llm_call_full: unknown signature -> regex add reason=False before the closing ):
full_defs = re.findall(r'async def _llm_call_full\([^)]*\):', t)
if any("reason=False" in d for d in full_defs):
    notes.append("_llm_call_full def already has reason")
    full_ok = True
elif full_defs:
    t = re.sub(r'(async def _llm_call_full\([^)]*?)\):', r'\1, reason=False):', t)
    notes.append(f"_llm_call_full def: added reason to {len(full_defs)} def(s)")
    full_ok = True
else:
    notes.append("!! no _llm_call_full def found"); full_ok = False

# (2) inject conditional reasoning_effort into each helper's json payload (recompute offsets each pass)
def inject_payload(text, defname):
    changed = 0
    while True:
        did = False
        for m in re.finditer(r'async def ' + re.escape(defname) + r'\(', text):
            start = m.end()
            win = text[start:start + 1600]
            j = win.find("json={")
            if j < 0:
                continue
            if "if reason else" in win[j:j + 70]:
                continue
            ai = start + j + len("json={")
            text = text[:ai] + '**({"reasoning_effort":"high"} if reason else {}),' + text[ai:]
            changed += 1; did = True; break
        if not did:
            break
    return text, changed

t, n1 = inject_payload(t, "_llm_call")
t, n2 = inject_payload(t, "_llm_call_full")
notes.append(f"payload spread injected: _llm_call={n1}, _llm_call_full={n2}")

# (3) flip reason=True on the four gather() first-pass calls only
GATHERS = [
    ("_asyncio.gather(_llm_call(_marked_messages), _llm_call(_marked_messages))",
     "_asyncio.gather(_llm_call(_marked_messages, reason=True), _llm_call(_marked_messages, reason=True))", llm_ok),
    ("_asyncio.gather(_llm_call_full(messages), _llm_call_full(messages))",
     "_asyncio.gather(_llm_call_full(messages, reason=True), _llm_call_full(messages, reason=True))", full_ok),
    ("_asyncio.gather(_llm_call_full(_marked_messages_full), _llm_call_full(_marked_messages_full))",
     "_asyncio.gather(_llm_call_full(_marked_messages_full, reason=True), _llm_call_full(_marked_messages_full, reason=True))", full_ok),
]
for old, new, ok in GATHERS:
    if new in t:
        notes.append(f"gather already flipped: …{old[-40:]}")
    elif not ok:
        notes.append(f"!! skipped gather (helper def not patched): …{old[-40:]}")
    else:
        c = t.count(old)
        if c >= 1:
            t = t.replace(old, new)
            notes.append(f"gather flipped reason=True ({c}x): …{old[-46:]}")
        else:
            notes.append(f"!! gather anchor 0x: …{old[-46:]}")

print("=== ~/velaris-server/server.py ===")
for n in notes:
    print("  -", n)
if t == orig:
    print("\n(no change)"); raise SystemExit(0)
bak = P + ".bak-vchat-" + TS
shutil.copy2(P, bak)
open(P, "w", encoding="utf-8").write(t)
try:
    py_compile.compile(P, doraise=True)
    print("\npy_compile OK — backup:", sh(bak))
    print("Restart her server for it to take effect (uvicorn on :8400, pid was 357).")
except Exception as e:
    shutil.copy2(bak, P)
    print("\npy_compile FAILED — rolled back:", str(e)[:140])
