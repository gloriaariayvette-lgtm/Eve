#!/usr/bin/env python3
"""voice_ledger_perturn_disable_patch.py — stop the broken per-turn voice ledger writes.

Voice fired interaction-ledger.py per turn with "--source voice" as positional args, which the
ledger read as gloria="--source", vintos="voice" — junk, one per turn. voice_session_ledger.py now
records each voice conversation as one clean block, so these per-turn calls are disabled. Neutralizes
every Popen that passes ("--source", "voice"). Self-locating, idempotent, backs up server.py.
Restart the server after applying.
"""
import io, os, re, time, shutil

F = os.path.expanduser("~/Vintos/server.py")
s = io.open(F, encoding="utf-8").read()

if "voice ledger consolidated per-session" in s:
    print("already patched — skipping"); raise SystemExit(0)

# match:  <var>.Popen([_venv, _il, "--source", "voice", ...],
#             stdout=open(...), stderr=open(...))
pat = re.compile(
    r'\w+\.Popen\(\[_venv, _il, "--source", "voice".*?stderr=open\([^)]*\)\)',
    re.DOTALL)
matches = pat.findall(s)
if not matches:
    print("MISS: voice per-turn ledger Popen not found"); raise SystemExit(1)

s = pat.sub('pass  # voice ledger consolidated per-session by voice_session_ledger.py', s)

shutil.copy(F, F + ".bak-voiceledger-" + time.strftime("%Y%m%d-%H%M%S"))
io.open(F, "w", encoding="utf-8").write(s)
leftover = s.count('"--source", "voice"')
print(f"PATCHED — disabled {len(matches)} per-turn voice ledger write(s)"
      + (f" (WARNING: {leftover} '--source voice' still present — check)" if leftover else "")
      + ". Restart the server.")
