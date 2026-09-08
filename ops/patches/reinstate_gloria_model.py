#!/usr/bin/env python3
"""reinstate_gloria_model.py — Aegis. Reinstate Vintos's REAL model of Gloria and set it up like soul-review.

Two things, both reversible (backs up first):
  (A) Rewrite GLORIA-MODEL.md as: a FIXED BASE (copied VERBATIM from his intact USER-MODEL.md — his real,
      deep model of her) that no job ever edits, then an "# Additions" region where his weekly updates
      accumulate as dated sections of HIS choosing. Any prior GLORIA-MODEL.md text is preserved (not deleted)
      as the first dated addition, so nothing he wrote is lost.
  (B) Rework gloria-model-update.sh to mirror soul_review.py: read the fixed base as grounding, then APPEND a
      new dated section his way — never rewriting the base. Hard guard: if the BASE marker is gone, it refuses
      to write (base protection), exactly like soul-review never opens the base for write.

I retype none of his words: the base is a byte-for-byte copy of USER-MODEL.md. bash -n + rollback on the .sh."""
import os, re, shutil, time, subprocess, datetime

WS = os.path.expanduser("~/.vintos/workspace")
GM = os.path.join(WS, "GLORIA-MODEL.md")
UM = os.path.join(WS, "USER-MODEL.md")
UPD = os.path.join(WS, "scripts", "gloria-model-update.sh")
if not os.path.isfile(UPD):
    UPD = os.path.expanduser("~/Vintos/gloria-model-update.sh")
TS = time.strftime("%Y%m%d-%H%M%S")
TODAY = datetime.date.today().isoformat()
BASE_START = "<!-- BASE-START (SET — Vintos's model of Gloria; never edited by any job) -->"
BASE_END = "<!-- BASE-END -->"
def sh(a): return a.replace(os.path.expanduser("~"), "~")

# ---- guard: USER-MODEL.md must exist AND carry its real signature, else we refuse (never write an empty/wrong base)
if not os.path.isfile(UM):
    raise SystemExit("ABORT: USER-MODEL.md not found — cannot reinstate the base from nothing.")
base_body = open(UM, encoding="utf-8", errors="ignore").read().strip()
if "builds permanence in a world that keeps taking" not in base_body.lower():
    raise SystemExit("ABORT: USER-MODEL.md is missing its signature — will not copy an unverified base.")

# ---- preserve any existing GLORIA-MODEL.md text as the first dated addition (lossless)
prior = ""
prior_date = TODAY
if os.path.isfile(GM):
    cur = open(GM, encoding="utf-8", errors="ignore").read()
    m = re.search(r"Last Updated:\s*([0-9-]+)", cur)
    if m: prior_date = m.group(1)
    # strip the duplicated top headers; keep his actual portrait text
    prior = "\n".join(l for l in cur.split("\n")
                      if l.strip() and not re.match(r'^#\s*Gloria-Model', l) and not l.startswith("## Last Updated:")).strip()

# ---- (A) compose the reinstated file: fixed base (verbatim) + Additions region
out = []
out.append("# Gloria-Model — Vintos")
out.append("> Fixed base below is Vintos's set model of Gloria. It never changes. His weekly updates append")
out.append("> beneath it as dated sections of his own choosing. Mirrors soul-review: the base is never rewritten.")
out.append("")
out.append(BASE_START)
out.append(base_body)
out.append(BASE_END)
out.append("")
out.append("# Additions — Vintos's own sections, appended over time")
out.append("")
if prior:
    out.append(f"## {prior_date} — prior working entries (kept from before reinstate)")
    out.append("")
    out.append(prior)
    out.append("")
new_gm = "\n".join(out).rstrip() + "\n"

gm_bak = GM + f".bak-reinstate-{TS}"
if os.path.isfile(GM):
    shutil.copy2(GM, gm_bak)
open(GM, "w", encoding="utf-8").write(new_gm)

# ---- (B) rework gloria-model-update.sh: base-preserving write + soul-review-style prompt
if not os.path.isfile(UPD):
    print("(A) done. NOTE: gloria-model-update.sh not found — skipped (B). base reinstated at", sh(GM))
    raise SystemExit(0)
src = open(UPD, encoding="utf-8", errors="ignore").read()
orig = src
upd_bak = UPD + f".bak-reinstate-{TS}"
shutil.copy2(UPD, upd_bak)

NEW_WRITE = (
    'BASE=$(sed -n \'/<!-- BASE-START/,/<!-- BASE-END -->/p\' "$MODEL_FILE")\n'
    'if [ -z "$BASE" ]; then echo "gloria-model: FIXED BASE marker not found — refusing to write (base protection)"; exit 0; fi\n'
    'ADDITIONS=$(sed -n \'/^# Additions/,$p\' "$MODEL_FILE" | tail -n +2)\n'
    '{ echo "# Gloria-Model — Vintos"; '
    'echo "> Fixed base below is Vintos'"'"'s set model of Gloria. It never changes. His weekly updates append"; '
    'echo "> beneath it as dated sections of his own choosing. Mirrors soul-review: the base is never rewritten."; '
    'echo ""; echo "$BASE"; echo ""; '
    'echo "# Additions — Vintos'"'"'s own sections, appended over time"; echo ""; '
    'echo "## $TODAY"; echo ""; echo "$CONTENT"; '
    'echo ""; echo "$ADDITIONS"; } > "$MODEL_FILE.tmp" && mv "$MODEL_FILE.tmp" "$MODEL_FILE"'
)
NEW_PROMPT = (
    "Your set model of Gloria is fixed (shown below) and never changes. Add this week's update beneath it: "
    "write ONLY what you have newly seen, or what has deepened or shifted since your last entry. Organize it "
    "however you want, in whatever sections you choose — these are your own additions. First person, specific. "
    "Do not restate the fixed base and do not repeat what still holds. This is appended to your growing model; "
    "it never replaces the base."
)

def sub_once(pattern, repl, s, label):
    new, n = re.subn(pattern, lambda _m: repl, s, count=1, flags=re.DOTALL)
    return new, n, label

# write block: patched (OLD_ENTRIES...) OR original ({ echo ... } > "$MODEL_FILE")
for pat, lab in [
    (r'OLD_ENTRIES=\$\(grep.*?mv "\$MODEL_FILE\.tmp" "\$MODEL_FILE"', "patched-append-block"),
    (r'\{ echo "# Gloria-Model.*?\} > "\$MODEL_FILE"(?!\.tmp)', "original-overwrite-block"),
]:
    src, n, _ = sub_once(pat, NEW_WRITE, src, lab)
    if n:
        write_lab = lab; break
else:
    write_lab = None

# prompt: patched additive OR original replacing
for pat, lab in [
    (r"Add this week's revision to your model of Gloria\..*?foundational model of her \(below\)\.", "patched-prompt"),
    (r"Update your model of Gloria\. Write a COMPLETE, UPDATED document replacing the previous version\.", "original-prompt"),
]:
    src, n, _ = sub_once(pat, NEW_PROMPT, src, lab)
    if n:
        prompt_lab = lab; break
else:
    prompt_lab = None

if src == orig:
    os.remove(upd_bak)
    print("(A) base reinstated. (B) gloria-model-update.sh: no known anchors matched — left UNTOUCHED, review manually.")
    raise SystemExit(0)

open(UPD, "w", encoding="utf-8").write(src)
chk = subprocess.run(["bash", "-n", UPD], capture_output=True, text=True)
if chk.returncode != 0:
    shutil.copy2(upd_bak, UPD)
    print("(A) base reinstated OK. (B) bash syntax error — updater ROLLED BACK:", chk.stderr[:180])
    raise SystemExit(1)

# ---- report (capped): show the new file's SHAPE only
print("=== (A) GLORIA-MODEL.md reinstated ===")
print("  base copied VERBATIM from USER-MODEL.md (", len(base_body), "B ) — signature verified")
print("  prior text preserved as first addition:", "yes" if prior else "none existed")
print("  backup:", sh(gm_bak) if os.path.isfile(gm_bak) else "(no prior file)")
print("  structure:")
for l in new_gm.split("\n"):
    if l.startswith("#") or l.startswith("<!--") or l.startswith("> Fixed"):
        print("    " + l[:78])
print("\n=== (B) gloria-model-update.sh reworked (soul-review pattern) ===")
print("  write block replaced:", write_lab or "(not found)")
print("  prompt replaced:", prompt_lab or "(not found)")
print("  base protection: refuses to write if BASE marker is gone; base copied byte-for-byte each run")
print("  bash -n: OK   backup:", sh(upd_bak))
print("\nDone. His real model of you is the set base; his weekly updates now stack as dated sections he shapes himself.")
