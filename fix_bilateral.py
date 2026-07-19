#!/usr/bin/env python3
"""fix_bilateral.py — the two verified bilateral fixes, BOTH beings. READ-ONLY unless --apply.

Verified live on 2026-07-19 with a full-context, save-nowhere test:

  1. REPETITION PENALTY (the real break-fix). Gemma's reasoning degenerates into a loop
     ("check banned word... no" x hundreds), burns the 11k-token budget, and leaves a1's
     content EMPTY — which is what breaks the pass. Adding frequency_penalty + repeat_penalty
     to the bilateral Gemma call stopped it cold: loop count 0, a1 content 0 -> 1364 chars,
     b1 filled too.

  2. REASONING CAPTURE. a1/b1/a2/b2 currently keep only `content` (the tidy conclusion) and
     discard `reasoning_content` — which is exactly where the two hemispheres DIVERGE (a1 went
     relational: finish the prose + share a sentence; b1 went analytical: quantify the
     translation tax). This carries the reasoning into those passes ONLY:
        - _safe_extract additionally stashes the reasoning in a module global (nothing else
          about its behaviour changes — every existing caller still gets clean `content`);
        - right after each a1/b1/a2/b2 assignment, the stashed reasoning is prepended.
     The final synthesized journal entry stays clean prose — it is a fresh generation FROM the
     passes, not a verbatim carry of them.

Targets both beings' journals:
    ~/.openclaw/workspace/scripts/idle-journal.sh   (Velaris)
    ~/Vintos/idle-journal.sh                         (Vintos)

  python3 fix_bilateral.py            # DRY RUN — prints diffs, writes nothing
  python3 fix_bilateral.py --apply    # backs up each file (timestamped), then applies
"""
import os, re, sys, difflib, datetime

APPLY = "--apply" in sys.argv
TS = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
BACKUP = os.path.expanduser(f"~/.bilateral-backups/{TS}")

TARGETS = [
    os.path.expanduser("~/.openclaw/workspace/scripts/idle-journal.sh"),  # Velaris
    os.path.expanduser("~/Vintos/idle-journal.sh"),                        # Vintos
]

PENALTY = '"frequency_penalty":0.6,"repeat_penalty":1.15,'
SEP = r'\n\n─── reasoning ───\n\n'   # written into the file as an escaped literal

# ---------------------------------------------------------------------------
def rd(p):
    try:
        return open(p, encoding="utf-8", errors="ignore").read()
    except Exception:
        return None

def show_diff(path, old, new):
    if old == new:
        print("   (no change)"); return
    for l in difflib.unified_diff(old.splitlines(), new.splitlines(),
                                  fromfile=path + " (old)", tofile=path + " (new)", lineterm=""):
        print("   " + l[:150])

def backup_then_write(path, old, new):
    if not APPLY:
        return
    rel = os.path.relpath(path, os.path.expanduser("~"))
    bp = os.path.join(BACKUP, rel)
    os.makedirs(os.path.dirname(bp), exist_ok=True)
    open(bp, "w", encoding="utf-8").write(old)
    open(path, "w", encoding="utf-8").write(new)

# ---------------------------------------------------------------------------
def patch_text(text):
    """Return (new_text, notes[]). Idempotent — re-running is a no-op."""
    notes = []

    # --- fix 1: repetition penalty on every bilateral reasoning call ------------
    if PENALTY in text:
        notes.append("penalty: already present")
    else:
        n = text.count('"reasoning_effort":"low",')
        if n:
            text = text.replace('"reasoning_effort":"low",',
                                '"reasoning_effort":"low",' + PENALTY)
            notes.append(f"penalty: added to {n} reasoning call(s)")
        else:
            notes.append("penalty: no 'reasoning_effort:low' request found — SKIPPED")

    # --- fix 2a: _safe_extract stashes the reasoning (additive, behaviour-preserving) ---
    old_ret = 'return data["choices"][0]["message"]["content"].strip()'
    new_ret = ('_m = data["choices"][0]["message"]; '
               'globals()["_BILAT_REASON"] = (_m.get("reasoning_content") or "").strip(); '
               'return (_m.get("content") or "").strip()')
    if "_BILAT_REASON" in text:
        notes.append("reason-stash: already present")
    elif old_ret in text:
        text = text.replace(old_ret, new_ret, 1)
        notes.append("reason-stash: added to _safe_extract")
    else:
        notes.append("reason-stash: extraction line not found — SKIPPED (reasoning capture off)")

    # --- fix 2b: prepend the stashed reasoning at the a1/b1/a2/b2 assignments ----
    if "_BILAT_REASON" in text:
        prepend_added = 0
        for var, pat in (("a1", r'^([ \t]*)a1 = call_llm\(\)[ \t]*$'),
                         ("b1", r'^([ \t]*)b1 = call_llm\(\)[ \t]*$'),
                         ("a2", r'^([ \t]*)a2 = absorb\(a1, b1\)[ \t]*$'),
                         ("b2", r'^([ \t]*)b2 = absorb\(b1, a1\)[ \t]*$')):
            m = re.search(pat, text, re.M)
            if not m:
                notes.append(f"prepend {var}: assignment not found — SKIPPED")
                continue
            indent = m.group(1)
            inject = (f'{indent}{var} = ((globals().get("_BILAT_REASON","") + "{SEP}" + {var}).strip() '
                      f'if globals().get("_BILAT_REASON") else {var})')
            if inject in text:
                notes.append(f"prepend {var}: already present")
                continue
            text = text[:m.end()] + "\n" + inject + text[m.end():]
            prepend_added += 1
        if prepend_added:
            notes.append(f"prepend: reasoning now carried into {prepend_added} pass(es)")

    return text, notes

# ---------------------------------------------------------------------------
def main():
    print("=" * 74)
    print("BILATERAL FIX  —  %s" % ("APPLYING (backup -> %s)" % BACKUP if APPLY else "DRY RUN (writes nothing)"))
    print("=" * 74)
    for path in TARGETS:
        being = "Velaris" if ".openclaw" in path else "Vintos"
        print(f"\n### {being}  ({path})")
        old = rd(path)
        if old is None:
            print("   !! not found — skipped"); continue
        new, notes = patch_text(old)
        for nnote in notes:
            print("   * " + nnote)
        print("   bash -n note: .sh with embedded python — validate with the smoke test below after --apply")
        show_diff(path, old, new)
        backup_then_write(path, old, new)

    print("\n" + "=" * 74)
    if APPLY:
        print("APPLIED. Backups at", BACKUP)
        print("Revert:  cp -r %s/* ~/    (or per-file from that dir)" % BACKUP)
        print("\nSMOKE TEST (save-nowhere, confirms no syntax break + reasoning present):")
        print("  the /tmp/vel-rt2.sh style run, or just let the next scheduled journal fire and check")
        print("  /tmp/bilateral-a1.txt has both reasoning and content.")
    else:
        print("DRY RUN complete. Review the diffs, then re-run with --apply.")
    print("=" * 74)

if __name__ == "__main__":
    main()
