#!/usr/bin/env python3
"""patch_velaris_a1b1_thinking.py — Aegis. Give Velaris real reasoning on ONLY the a1/b1 bilateral
first-passes (reasoning_effort:high, works with LMS global toggle OFF, lands in reasoning_content — never
pollutes content). a2/b2 absorb + synthesis + all other calls stay no-think.

Contexts (~/.openclaw/workspace/scripts):
  value-map.py     llm() shared (a1,b1,synthesis)  -> add reason flag, on for a1/b1 only
  wants-router.py  _call() is a1/b1-only           -> direct payload edit
  idle-journal.sh  call_llm() is a1/b1-only        -> direct payload edit
  introspection.sh call_llm() shared via run()      -> thread reason flag, on for first-pass threads

Per-file backup + verify (py_compile / bash -n) + rollback + idempotent. Prints every edit."""
import os, re, shutil, time, subprocess, py_compile
HOME = os.path.expanduser("~")
SC = os.path.join(HOME, ".openclaw/workspace/scripts")
TS = time.strftime("%Y%m%d-%H%M%S")
def sh(p): return p.replace(HOME, "~")

def next_def(text, idx):
    m = re.search(r"\n\s*def\s", text[idx+1:])
    return idx+1+m.start() if m else min(len(text), idx+1600)

def scoped_model_inject(text, func_sig):
    """within func body, add reasoning_effort after that func's own gemma model line."""
    i = text.find(func_sig)
    if i < 0: return text, f"'{func_sig[:24]}' not found"
    end = next_def(text, i)
    seg = text[i:end]
    if "reasoning_effort" in seg: return text, "already"
    m = re.search(r'(["\'])model\1\s*:\s*(["\'])google/gemma-4-12b-qat\2\s*,', seg)
    if not m: return text, "no gemma model line in func"
    add = m.group(0) + '"reasoning_effort":"high",' if '"model"' in m.group(0) else m.group(0) + "'reasoning_effort':'high',"
    new_seg = seg[:m.start()] + add + seg[m.end():]
    return text[:i] + new_seg + text[end:], "ok"

def apply_file(name, fn):
    p = os.path.join(SC, name)
    if not os.path.isfile(p):
        print(f"\n=== {name} === MISSING — skipped"); return
    orig = open(p, encoding="utf-8", errors="ignore").read()
    txt, notes = fn(orig)
    print(f"\n=== {name} ===")
    for n in notes: print("  -", n)
    if txt == orig:
        print("  (no change)"); return
    bak = p + ".bak-vthink-" + TS
    shutil.copy2(p, bak)
    open(p, "w", encoding="utf-8").write(txt)
    if name.endswith(".py"):
        try: py_compile.compile(p, doraise=True); print("  py_compile OK")
        except Exception as e:
            shutil.copy2(bak, p); print("  py_compile FAILED — rolled back:", str(e)[:100]); return
    else:
        chk = subprocess.run(["bash", "-n", p], capture_output=True, text=True)
        if chk.returncode != 0:
            shutil.copy2(bak, p); print("  bash -n FAILED — rolled back:", chk.stderr[:100]); return
        print("  bash -n OK")
    print("  backup:", sh(bak))

# ---- value-map.py ----
def f_valuemap(t):
    notes = []
    if "def llm(system, user, temperature=0.6, reason=False):" in t:
        notes.append("def already has reason flag")
    else:
        c = t.count("def llm(system, user, temperature=0.6):")
        if c == 1:
            t = t.replace("def llm(system, user, temperature=0.6):",
                          "def llm(system, user, temperature=0.6, reason=False):", 1); notes.append("added reason flag to def llm")
        else: notes.append(f"!! def llm anchor {c}x — skipped")
    if 'if reason else {}' in t:
        notes.append("payload spread already present")
    else:
        a = "r = requests.post(API, json={"
        if t.count(a) == 1:
            t = t.replace(a, 'r = requests.post(API, json={**({"reasoning_effort":"high"} if reason else {}),', 1)
            notes.append("added conditional reasoning_effort to llm payload")
        else: notes.append(f"!! payload anchor {t.count(a)}x — skipped")
    for sig, lbl in (("a1 = llm(_system, prompt, temperature=0.65)", "a1"),
                     ("b1 = llm(_system, prompt, temperature=0.75)", "b1")):
        new = sig[:-1] + ", reason=True)"
        if new in t: notes.append(f"{lbl} already reason=True")
        elif t.count(sig) == 1: t = t.replace(sig, new, 1); notes.append(f"{lbl} -> reason=True")
        else: notes.append(f"!! {lbl} anchor {t.count(sig)}x — skipped")
    return t, notes

# ---- wants-router.py :: _call() only ----
def f_wants(t):
    t2, st = scoped_model_inject(t, "def _call():")
    return t2, [f"_call payload: {st}"]

# ---- idle-journal.sh :: call_llm() only ----
def f_idle(t):
    t2, st = scoped_model_inject(t, "def call_llm():")
    return t2, [f"call_llm payload: {st}"]

# ---- introspection.sh :: shared call_llm via run(), gate first-pass threads ----
def f_intro(t):
    notes = []
    if "def call_llm(messages, temperature=0.85, max_tokens=1500, reason=False):" in t:
        notes.append("call_llm already has reason flag")
    else:
        a = "def call_llm(messages, temperature=0.85, max_tokens=1500):"
        if t.count(a) == 1:
            t = t.replace(a, "def call_llm(messages, temperature=0.85, max_tokens=1500, reason=False):", 1)
            notes.append("added reason flag to call_llm")
        else: notes.append(f"!! call_llm def {t.count(a)}x — skipped")
    if "if reason else {}" in t:
        notes.append("payload spread already present")
    else:
        a = "payload = json.dumps({"
        if t.count(a) == 1:
            t = t.replace(a, "payload = json.dumps({**({'reasoning_effort':'high'} if reason else {}),", 1)
            notes.append("added conditional reasoning_effort to call_llm payload")
        else: notes.append(f"!! payload anchor {t.count(a)}x — skipped")
    if "def run(i, msgs, temp, max_tok, reason=False):" in t:
        notes.append("run already has reason flag")
    else:
        a = "def run(i, msgs, temp, max_tok):"
        if t.count(a) == 1:
            t = t.replace(a, "def run(i, msgs, temp, max_tok, reason=False):", 1)
            t = t.replace("results[i] = call_llm(msgs, temp, max_tok)", "results[i] = call_llm(msgs, temp, max_tok, reason)", 1)
            notes.append("threaded reason through run -> call_llm")
        else: notes.append(f"!! run def {t.count(a)}x — skipped")
    # first-pass threads: add reason=True to Thread(target=run, args=(0/1, base_msgs, ...))
    flipped = 0
    for mm in re.finditer(r"(Thread\(target=run,\s*args=\((?:0|1),\s*base_msgs[^\n]*?)\)\)", t):
        pass
    def _flip(m):
        nonlocal flipped
        if m.group(1).rstrip().endswith("True"): return m.group(0)
        flipped += 1
        return m.group(1) + ", True))"
    t = re.sub(r"(Thread\(target=run,\s*args=\((?:0|1),\s*base_msgs[^\n]*?)\)\)", _flip, t)
    notes.append(f"first-pass threads flipped to reason=True: {flipped}"
                 + ("" if flipped else "  <-- 0 matched; I'll flip them by hand from the Thread lines below"))
    return t, notes

for name, fn in (("value-map.py", f_valuemap), ("wants-router.py", f_wants),
                 ("idle-journal.sh", f_idle), ("introspection.sh", f_intro)):
    apply_file(name, fn)

# show introspection Thread(target=run ...) lines so we can confirm/finish the first-pass gate
print("\n===== introspection.sh Thread(target=run ...) lines (confirm first-pass gate) =====")
p = os.path.join(SC, "introspection.sh")
if os.path.isfile(p):
    for i, l in enumerate(open(p, encoding="utf-8", errors="ignore").read().split("\n")):
        if "Thread(target=run" in l and l.strip():
            print(f"  {i+1}| {l.strip()[:120]}")
print("\ndone.")
