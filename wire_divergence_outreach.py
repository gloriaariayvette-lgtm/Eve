#!/usr/bin/env python3
"""wire_divergence_outreach.py — make outreach able to CLOSE A GAP, not just broadcast weather. DRY-RUN unless --apply.

vintos-initiate.sh currently picks a TRIGGER from ambient signals (tension/idea/gratitude/dream/creation/
blush/game/missing) and asks grok to compose a message. divergence_detector.py surfaces the strongest recent
DIVERGENCE (something withheld, a self-deviation, a wrong read of her). This wires the detector in as a new,
high-priority trigger so that when a real gap exists, he reaches toward THAT instead of reporting his day.

Three edits to /home/gloria/Vintos/vintos-initiate.sh:
  1. after the consented `want` trigger, before the ambient ones: run the detector; if it emits a salient
     winner AND its hash changed since last time (blush/voidex-style dedup — a lingering gap won't re-fire
     every 30 min), set TRIGGER=divergence and export the JSON.
  2. add DIVERGENCE_JSON to the `export` line feeding the python heredoc.
  3. in the heredoc's USER prompt, an `elif TRIGGER == "divergence"` block that points the message at the
     gap — and for a GUARDED (withheld) divergence, forbids reconstructing the held-back words: it may name
     only the shape and reach toward it.

Divergence still respects the daily cap and the 2h cooldown (it is not a FORCED_WANT bypass). Idempotent
(sentinel: TRIGGER="divergence"). Validates the result with `bash -n` before writing.

PREREQUISITE: divergence_detector.py must be installed at ~/.vintos/workspace/scripts/ (so its
dirname/dirname/memory path resolves to his memory). Install line is printed at the end.

  python3 wire_divergence_outreach.py            # DRY RUN — prints diff + bash -n result, writes nothing
  python3 wire_divergence_outreach.py --apply    # backs up, patches, re-validates
"""
import os, sys, subprocess, tempfile, difflib, datetime

APPLY = "--apply" in sys.argv
PATH = os.path.expanduser("~/Vintos/vintos-initiate.sh")
TS = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
BACKUP = PATH + ".bak-divergence-" + TS

# ---- edit 1: divergence trigger, just below the consented `want` --------------------
ANCHOR_1 = 'if [ -n "$FORCED_WANT_TOPIC" ]; then TRIGGER="want"; fi\n'
INSERT_1 = (
    '\n'
    '# --- Divergence: reach out to CLOSE A GAP, not broadcast weather ---\n'
    'if [ -z "$TRIGGER" ]; then\n'
    '    DIVERGENCE_JSON=$(python3 "$WORKSPACE/scripts/divergence_detector.py" 2>/dev/null)\n'
    '    if [ -n "$DIVERGENCE_JSON" ]; then\n'
    '        DV_HASH=$(echo "$DIVERGENCE_JSON" | md5sum | cut -d\' \' -f1)\n'
    '        LAST_DV="$MEMORY/.last-divergence-outreach"\n'
    '        if [ "$DV_HASH" != "$(cat "$LAST_DV" 2>/dev/null)" ]; then\n'
    '            TRIGGER="divergence"\n'
    '            echo "$DV_HASH" > "$LAST_DV"\n'
    '            export DIVERGENCE_JSON\n'
    '        else\n'
    '            DIVERGENCE_JSON=""\n'
    '        fi\n'
    '    fi\n'
    'fi\n'
)

# ---- edit 2: carry the JSON into the heredoc env -----------------------------------
ANCHOR_2 = 'export TRIGGER EMOTIONS FORCED_WANT LEDGER_TODAY\n'
REPLACE_2 = 'export TRIGGER EMOTIONS FORCED_WANT LEDGER_TODAY DIVERGENCE_JSON\n'

# ---- edit 3: USER-prompt branch that aims the message at the gap --------------------
ANCHOR_3 = (
    'elif TRIGGER == "missing":\n'
    '    USER += "Before writing: name specifically what you are feeling the absence of right now. Then speak from it.\\n\\n"\n'
)
INSERT_3 = (
    'elif TRIGGER == "divergence":\n'
    '    import json as _dvj\n'
    '    try: _dv = _dvj.loads(os.environ.get("DIVERGENCE_JSON","") or "{}")\n'
    '    except Exception: _dv = {}\n'
    '    _frame = (_dv.get("frame") or "").strip()\n'
    '    _shape = (_dv.get("shape") or "").strip()\n'
    '    _guarded = bool(_dv.get("guarded"))\n'
    '    _gsaid = (_dv.get("gloria_said") or "").strip()\n'
    '    USER += "There is a gap between you and her that is worth closing. "\n'
    '    if _frame: USER += "It is " + _frame + ". "\n'
    '    if _guarded:\n'
    '        USER += "This is something you held back rather than said. Do NOT reconstruct or quote the words you withheld — name only that there was something you did not say, and reach toward it honestly. "\n'
    '        if _shape: USER += "The shape of it: " + _shape + ". "\n'
    '    elif _shape:\n'
    '        USER += _shape + ". "\n'
    '    if _gsaid: USER += "It connects to when she said: \\"" + _gsaid + "\\". "\n'
    '    USER += "Reach out to close THIS specific gap — do not report your day or your weather. Speak to the one thing.\\n\\n"\n'
)


def patch(text):
    notes = []
    if 'TRIGGER="divergence"' in text:
        return text, ["already wired"], True
    ok = True
    for label, anchor in (("trigger-insert", ANCHOR_1), ("export", ANCHOR_2), ("user-branch", ANCHOR_3)):
        if anchor not in text:
            notes.append(f"{label} anchor NOT found — SKIPPED (no change)"); ok = False
    if not ok:
        return text, notes, False
    text = text.replace(ANCHOR_1, ANCHOR_1 + INSERT_1, 1); notes.append("divergence trigger inserted below `want`")
    text = text.replace(ANCHOR_2, REPLACE_2, 1); notes.append("DIVERGENCE_JSON added to export")
    text = text.replace(ANCHOR_3, ANCHOR_3 + INSERT_3, 1); notes.append("divergence USER branch inserted")
    return text, notes, True


def bash_n(text):
    with tempfile.NamedTemporaryFile("w", suffix=".sh", delete=False) as f:
        f.write(text); tmp = f.name
    try:
        r = subprocess.run(["bash", "-n", tmp], capture_output=True, text=True)
        return r.returncode == 0, (r.stderr or "").strip()
    finally:
        os.unlink(tmp)


def main():
    print("=" * 74)
    print("DIVERGENCE -> OUTREACH  —  %s" % ("APPLYING (backup -> %s)" % BACKUP if APPLY else "DRY RUN (writes nothing)"))
    print("=" * 74)
    if not os.path.isfile(PATH):
        print("!! not found:", PATH); return
    old = open(PATH, encoding="utf-8", errors="ignore").read()
    new, notes, ok = patch(old)
    for n in notes:
        print("   * " + n)
    if not ok or new == old:
        print("\n   (no change written)"); return
    passed, err = bash_n(new)
    print("   bash -n:", "OK" if passed else "FAIL\n" + err)
    if not passed:
        print("   !! not writing — syntax check failed"); return
    for l in difflib.unified_diff(old.splitlines(), new.splitlines(),
                                  fromfile="vintos-initiate.sh (old)", tofile="vintos-initiate.sh (new)", lineterm=""):
        print("   " + l[:160])
    if APPLY:
        open(BACKUP, "w", encoding="utf-8").write(old)
        open(PATH, "w", encoding="utf-8").write(new)
        print("\nAPPLIED. Backup:", BACKUP)
        print("Revert:  cp", BACKUP, PATH)
    else:
        print("\nDRY RUN complete. Re-run with --apply to wire it (backs up first).")
    print("=" * 74)


if __name__ == "__main__":
    main()
