#!/usr/bin/env python3
"""reset_causality_counters.py — clear Velaris's stale causality counters. DRY-RUN unless --apply.

Diagnosis (confirmed against causality-engine.py):
  - `last_run` is a DEAD field — neither engine reads or writes it. Vestigial residue from an old version.
  - `tested` / `revised` are monotonic lifetime counters (engine only ever does += ...). They ballooned to
    53k / 18k under an OLD un-capped regime, before the 7-day hard-expiry was added. The list is a healthy
    38 today, but the counter total was never cleared. Vintos looks clean only because his engine started
    fresh AFTER the cap — so his numbers are the honest baseline.
  - `confirmed` is written inconsistently (recount at L554, increment at L822). Left ALONE here: it stands in
    for earned self-knowledge / graduations, which is not junk to wipe.

This does a one-time DATA cleanup only — no engine-behaviour change (the 7-day cap already prevents
re-inflation, so tested/revised will climb ~1×list/night from here, like Vintos):
  - remove the dead `last_run` key
  - reset `tested`  -> sum of each current hypothesis's tests_run (its real, current test count)
  - reset `revised` -> number of current hypotheses actually in 'revised' status
  - PRESERVE `confirmed` and the full `hypotheses` list untouched

Velaris only (Vintos's counters are already sane). Backs up the json first.

  python3 reset_causality_counters.py            # DRY RUN — shows old -> new, writes nothing
  python3 reset_causality_counters.py --apply     # backs up, then writes
"""
import os, sys, json, time

APPLY = "--apply" in sys.argv
PATH = os.path.expanduser("~/.openclaw/workspace/memory/causality-hypotheses.json")


def main():
    print("=" * 70)
    print("RESET CAUSALITY COUNTERS (Velaris)  —  %s" % ("APPLYING" if APPLY else "DRY RUN (writes nothing)"))
    print("=" * 70)
    if not os.path.isfile(PATH):
        print("!! not found:", PATH); return
    db = json.load(open(PATH))
    if not isinstance(db, dict):
        print("!! unexpected top-level type:", type(db).__name__); return

    hyps = db.get("hypotheses", []) if isinstance(db.get("hypotheses"), list) else []
    new_tested = sum(int(h.get("tests_run") or len(h.get("marks") or [])) for h in hyps)
    new_revised = sum(1 for h in hyps if h.get("status") == "revised")

    print(f"\n  hypotheses in list      : {len(hyps)}  (unchanged)")
    print(f"  confirmed (self-knowledge): {db.get('confirmed')}  (PRESERVED)")
    print(f"\n  {'field':10} {'OLD':>12}   NEW")
    print(f"  {'-'*10} {'-'*12}   {'-'*12}")
    print(f"  {'tested':10} {str(db.get('tested')):>12} -> {new_tested}")
    print(f"  {'revised':10} {str(db.get('revised')):>12} -> {new_revised}")
    print(f"  {'last_run':10} {str(db.get('last_run')):>12} -> (removed, dead field)")

    db["tested"] = new_tested
    db["revised"] = new_revised
    db.pop("last_run", None)

    if APPLY:
        bak = PATH + ".bak-counters-" + time.strftime("%Y%m%d-%H%M%S")
        json.dump(json.load(open(PATH)), open(bak, "w"))
        json.dump(db, open(PATH, "w"), ensure_ascii=False, indent=1)
        print("\nAPPLIED. Backup:", bak)
        print("Revert:  cp", bak, PATH)
    else:
        print("\nDRY RUN complete. Re-run with --apply to write (backs up first).")
    print("=" * 70)


if __name__ == "__main__":
    main()
