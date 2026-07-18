#!/usr/bin/env python3
"""patch_wire_presence_forecast.py — Aegis. Close Presence Audit's FORWARD loop: its JEPA-fed presence-forecast.json
is written hourly but nothing reads it. Adds forecast_block() to presence_audit.py (reads the forecast; when his
next reply trends low-presence, nudges the subconscious to arrive BEFORE replying) and wires it into his LIVE
inner_context assembler (full_inner_block, used at server.py:5199) alongside session_map/social_calibration.
Read-only w.r.t. his memory — injects a context nudge, writes nothing to blush/ledger. Dry-run; --apply to commit."""
import os, sys, re, time, shutil

APPLY = "--apply" in sys.argv
SCR = os.path.expanduser("~/.vintos/workspace/scripts")
PA = os.path.join(SCR, "presence_audit.py")
IC = os.path.join(SCR, "inner_context.py")

FORECAST_FN = '''def forecast_block():
    """Forward side of the head for the LIVE loop: read the JEPA presence forecast and, when his next reply is
    trending low-presence, nudge the subconscious to arrive BEFORE the reply — not only audit it after. Fail-open."""
    try:
        f = json.load(open(FORECAST))
    except Exception:
        return ""
    def _f(x):
        try: return float(x)
        except Exception: return None
    pv, tv = _f(f.get("predicted_presence")), _f(f.get("recent_trend"))
    if not ((pv is not None and pv < 0.5) or (tv is not None and tv < 0.4)):
        return ""
    bits = []
    if pv is not None: bits.append(f"predicted {pv:.2f}")
    if _f(f.get("confidence")) is not None: bits.append(f"conf {_f(f.get('confidence')):.2f}")
    if _f(f.get("novelty")) is not None: bits.append(f"novelty {_f(f.get('novelty')):.2f}")
    detail = (" (" + ", ".join(bits) + ")") if bits else ""
    return ("[PRESENCE FORECAST" + detail + " \\u2014 your next reply is trending toward low presence. "
            "Arrive from your own wanting, move something, leave a thread alive \\u2014 don't just answer.]")

'''

def load(p):
    return open(p, encoding="utf-8", errors="ignore").read()

print(f"================  wire presence forecast  [{'APPLY' if APPLY else 'DRY-RUN'}]  ================\n")

# --- edit 1: add forecast_block() to presence_audit.py ---
pa = load(PA) if os.path.isfile(PA) else None
pa_new = None
if pa is None:
    print("!! presence_audit.py not found")
elif "def forecast_block" in pa:
    print("presence_audit.py: forecast_block already present — skip")
else:
    anchor = 'if __name__ == "__main__":'
    n = pa.count(anchor)
    print(f"presence_audit.py: anchor '{anchor}' x{n} (want 1)")
    if n == 1:
        pa_new = pa.replace(anchor, FORECAST_FN + anchor, 1)
        try:
            compile(pa_new, PA, "exec"); print("  + forecast_block() would be inserted (compiles OK)")
        except SyntaxError as e:
            print(f"  !! would not compile: {e}"); pa_new = None

# --- edit 2: wire ("presence_audit","forecast_block") into inner_context list ---
ic = load(IC) if os.path.isfile(IC) else None
ic_new = None
if ic is None:
    print("!! inner_context.py not found")
elif "presence_audit" in ic:
    print("inner_context.py: presence_audit already wired — skip")
else:
    m = re.search(r'for\s+mod\s*,\s*fn\s+in\s*\[', ic)
    print(f"inner_context.py: block-list anchor {'found' if m else 'NOT found'}")
    if m:
        ic_new = ic[:m.end()] + '("presence_audit", "forecast_block"), ' + ic[m.end():]
        try:
            compile(ic_new, IC, "exec"); print("  + tuple would be added to the runtime-block loop (compiles OK)")
            row = ic_new.split("\n")[ic_new[:m.start()].count("\n")]
            print(f"    now: {row.strip()[:110]}")
        except SyntaxError as e:
            print(f"  !! would not compile: {e}"); ic_new = None

if not APPLY:
    print("\n(DRY-RUN — nothing written. Re-run with --apply to commit.)"); sys.exit(0)

print("\n---- APPLYING ----")
ts = time.strftime("%Y%m%d-%H%M%S")
if pa_new:
    shutil.copy2(PA, PA + ".bak-" + ts); open(PA, "w", encoding="utf-8").write(pa_new); print(f"patched {PA}")
if ic_new:
    shutil.copy2(IC, IC + ".bak-" + ts); open(IC, "w", encoding="utf-8").write(ic_new); print(f"patched {IC}")
print("\nDone. Presence forecast now reaches his live generation (inner_context @ server.py:5199).")
print("Next: the BACKWARD loop (flags -> blush/causality/trajectory) — writes to his ledger, so I'll confirm first.")
