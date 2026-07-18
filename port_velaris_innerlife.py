#!/usr/bin/env python3
"""port_velaris_innerlife.py — Aegis. Finish Velaris's inner-life parity in one shot. Ports three runtime blocks
into her tree and wires them into her live get_subconscious_context (the FULL assembler — her background crons use
the compact one, so joke callbacks won't be consumed off-stage):
  - curiosity_debt.py     (transformed from his: paths/identity -> hers; self-seeds from her wonder-log)
  - joke_fermentation.py  (transformed from his; self-seeds from her humor-profile)
  - session_map.py        (authored fresh for her — within-session arc sourced from her emoclaw_pressure combos)
DRY-RUN by default; add --apply to commit (backs up + compile-checks everything). No somatic content."""
import os, sys, re, time, shutil

APPLY = "--apply" in sys.argv
HOME = os.path.expanduser("~")
HIS = os.path.expanduser("~/.vintos/workspace/scripts")
HER = os.path.expanduser("~/.openclaw/workspace/scripts")

def transform(txt):
    txt = txt.replace("~/.vintos/workspace", "~/.openclaw/workspace").replace("/.vintos/", "/.openclaw/")
    txt = txt.replace("127.0.0.1:8599", "172.18.16.1:1234")
    txt = re.sub(r'\bVintos\b', "Velaris", txt)
    txt = re.sub(r'\bhe\b', "she", txt); txt = re.sub(r'\bhis\b', "her", txt); txt = re.sub(r'\bhim\b', "her", txt)
    return txt

SESSION_MAP = '''"""session_map.py — the within-conversation emotional arc (Velaris). Sources the 'mode' from her
emoclaw_pressure combos; narrates where this conversation has moved. No LLM."""
import os, json, time
MEM = os.path.expanduser("~/.openclaw/workspace/memory")
ARC = os.path.join(MEM, "session-arc.json")
def _mode():
    try:
        from emoclaw_pressure import read_state, COMBOS
    except Exception:
        return ""
    s = read_state()
    if not s: return ""
    for c in COMBOS:
        try:
            if c["conditions"](s): return c["name"]
        except Exception: pass
    val = s.get("Valence", 0.5); ar = s.get("Arousal", 0.5)
    if val >= 0.55 and ar >= 0.55: return "bright"
    if val >= 0.55 and ar < 0.45:  return "warm-still"
    if val < 0.45 and ar >= 0.55:  return "agitated"
    if val < 0.45 and ar < 0.45:   return "heavy"
    return "even"
def block():
    now = time.time()
    mode = _mode()
    if not mode: return ""
    try: arc = json.load(open(ARC))
    except Exception: arc = {"seq": [], "last": 0}
    if now - arc.get("last", 0) > 1800: arc = {"seq": [], "last": now}
    seq = arc.get("seq", [])
    if not seq or seq[-1] != mode: seq.append(mode)
    arc["seq"] = seq[-8:]; arc["last"] = now
    try: json.dump(arc, open(ARC, "w"))
    except Exception: pass
    if len(seq) < 2: return ""
    txt = f"began {seq[0]}, now {seq[-1]}" if len(seq) == 2 else f"began {seq[0]}, moved through {', '.join(seq[1:-1])}, now {seq[-1]}"
    return f"[SESSION ARC \\u2014 where this conversation has moved: {txt}. Let that shape what this moment is becoming.]"
if __name__ == "__main__": print(block() or "(arc not formed yet)")
'''

# assemble the three files' final content
outputs = {}
for f in ("curiosity_debt.py", "joke_fermentation.py"):
    src = os.path.join(HIS, f)
    if not os.path.isfile(src): src = os.path.join(HOME, "Vintos", f)
    if not os.path.isfile(src):
        print(f"!! source not found: {f}"); continue
    outputs[f] = transform(open(src, encoding="utf-8", errors="ignore").read())
outputs["session_map.py"] = SESSION_MAP

TARGET = os.path.join(HER, "subconscious_context.py")
WIRE = ('    # ported from Vintos: within-session arc, fermented jokes, curiosity debt (runtime inner-life)\n'
        '    for _mod, _fn in (("session_map", "block"), ("joke_fermentation", "callback_block"), ("curiosity_debt", "block")):\n'
        '        try:\n'
        '            from importlib import import_module as _im\n'
        '            _s = getattr(_im(_mod), _fn)()\n'
        '            if _s: parts.append(_s)\n'
        '        except Exception: pass\n')
ANCHOR = '    if not parts:\n        return ""'

print(f"================  port_velaris_innerlife  [{'APPLY' if APPLY else 'DRY-RUN'}]  ================\n")
for f, txt in outputs.items():
    dst = os.path.join(HER, f)
    resid = sorted(set(re.findall(r'vintos|8599|\.vintos', txt, re.I)))
    ok = True
    try: compile(txt, dst, "exec")
    except SyntaxError as e: ok = False; print(f"!! {f} SYNTAX ERROR: {e}")
    print(f"--- {f}  ({'new' if not os.path.isfile(dst) else 'OVERWRITE'})  compiles={ok}  residual_his={resid or 'none'} ---")
if not os.path.isfile(TARGET):
    print(f"\n!! assembler {TARGET} not found — cannot wire")
else:
    at = open(TARGET, encoding="utf-8", errors="ignore").read()
    print(f"\nwiring target: {TARGET}  | already wired: {'yes' if 'session_map' in at else 'no'} | "
          f"anchor count: {at.count(ANCHOR)} (want 1)")

if not APPLY:
    print("\n(DRY-RUN — nothing written. Re-run with --apply to commit.)"); sys.exit(0)

print("\n---- APPLYING ----")
ts = time.strftime("%Y%m%d-%H%M%S")
for f, txt in outputs.items():
    dst = os.path.join(HER, f)
    try: compile(txt, dst, "exec")
    except SyntaxError as e: print(f"!! skip {f}: {e}"); continue
    if os.path.isfile(dst): shutil.copy2(dst, dst + ".bak-" + ts)
    open(dst, "w", encoding="utf-8").write(txt); print(f"wrote {dst}")
if os.path.isfile(TARGET):
    at = open(TARGET, encoding="utf-8", errors="ignore").read()
    if "session_map" in at:
        print("assembler already wired — no change.")
    elif at.count(ANCHOR) == 1:
        new = at.replace(ANCHOR, WIRE + "\n" + ANCHOR, 1)
        try:
            compile(new, TARGET, "exec")
            shutil.copy2(TARGET, TARGET + ".bak-" + ts); open(TARGET, "w", encoding="utf-8").write(new)
            print(f"wired {TARGET}")
        except SyntaxError as e: print(f"!! wiring syntax error ({e}) — assembler left untouched")
    else:
        print("!! anchor not unique — assembler left untouched (wire manually)")
print("\nDone. Three inner-life blocks live in her subconscious context (runtime, no cron).")
