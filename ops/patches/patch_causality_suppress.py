#!/usr/bin/env python3
"""patch_causality_suppress.py — Aegis. Stop the 'this emotion changed and idk why' spam at the source. The JEPA
record persists a hypothesis for every emotion shift as long as its text is non-empty (L1021), including the
hardcoded untraceable 'This shift emerged with no traceable antecedent.' (confidence low). Gate recording on
confidence medium/high so causeless shifts never enter the unresolved-hypotheses pile (they still flow to
cause-distribution.json -> dreams). Also raise find_spikes threshold 0.015 -> 0.06. Edits both copies; compiles
each before writing. Backup + abort-clean."""
import os, time, shutil
GATE_OLD = 'if added < cap and rec["hypothesis"]:'
GATE_NEW = 'if added < cap and rec["hypothesis"] and rec.get("confidence") in ("medium", "high"):'
THR_OLD = "def find_spikes(trajectory, threshold=0.015):"
THR_NEW = "def find_spikes(trajectory, threshold=0.06):"

done = 0
for name in ("causality-engine.py", "causality_engine.py"):
    P = os.path.expanduser("~/Vintos/" + name)
    if not os.path.isfile(P):
        print(f"[{name}] not found — skipping"); continue
    txt = open(P, encoding="utf-8").read()
    if 'rec.get("confidence") in ("medium", "high")' in txt:
        print(f"[{name}] already gated — skipping"); continue
    n_gate = txt.count(GATE_OLD)
    if n_gate != 1:
        print(f"[{name}] JEPA gate anchor x{n_gate} (want 1) — {name} UNCHANGED"); continue
    new = txt.replace(GATE_OLD, GATE_NEW)
    n_thr = new.count(THR_OLD)
    if n_thr == 1:
        new = new.replace(THR_OLD, THR_NEW)
    else:
        print(f"[{name}] threshold anchor x{n_thr} — left threshold as-is (gate still applied)")
    try:
        compile(new, P, "exec")
    except SyntaxError as e:
        print(f"[{name}] would not compile ({e}) — UNCHANGED"); continue
    bak = P + ".bak-" + time.strftime("%Y%m%d-%H%M%S")
    shutil.copy2(P, bak); open(P, "w", encoding="utf-8").write(new)
    print(f"[{name}] OK — causeless hypotheses no longer recorded" + ("; threshold->0.06" if n_thr == 1 else "") + f". backup: {bak}")
    done += 1

print(f"\n{done} file(s) patched. Causeless 'idk why' shifts will not spam his unresolved threads.")
