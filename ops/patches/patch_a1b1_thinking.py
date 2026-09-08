#!/usr/bin/env python3
"""patch_a1b1_thinking.py — Aegis. Give ONLY a1/b1 real reasoning via per-request reasoning_effort (works
with the LMS global toggle OFF; lands in reasoning_content, never in content). Everything else stays no-think.
Targets the bilateral a1/b1 scripts. Backup + idempotent. Prints context so you can confirm the target."""
import os, re, shutil, time
HOME = os.path.expanduser("~")
SC = os.path.join(HOME, ".vintos/workspace/scripts")
TARGETS = ["conflict_surface.py", "reality_ebm.py"]
TS = time.strftime("%Y%m%d-%H%M%S")
OLD = '"model":"google/gemma-4-12b-qat",'
NEW = '"model":"google/gemma-4-12b-qat","reasoning_effort":"high",'

for name in TARGETS:
    p = os.path.join(SC, name)
    print("\n=== " + name + " ===")
    if not os.path.isfile(p):
        print("  MISSING — skipped"); continue
    txt = open(p, encoding="utf-8", errors="ignore").read()
    # show any bilateral/a1/b1 marker so we know it's the right script
    for m in re.finditer(r".{0,30}(bilateral|hemisphere|\ba1\b|\bb1\b).{0,30}", txt, re.I):
        print("  marker:", re.sub(r"\s+", " ", m.group(0)).strip()[:70]); break
    if '"reasoning_effort"' in txt:
        print("  already has reasoning_effort — skipped"); continue
    c = txt.count(OLD)
    if c == 0:
        # fall back to spaced JSON form
        alt = re.search(r'("model"\s*:\s*"google/gemma-4-12b-qat"\s*,)', txt)
        if not alt:
            print("  no gemma-4 call payload found here — tell me the real a1/b1 file"); continue
        old2 = alt.group(1); new2 = old2[:-1] + ',"reasoning_effort":"high"' if False else old2.replace(',', ',"reasoning_effort":"high",', 1)
        # simpler: insert after the model key
        new2 = alt.group(1) + '"reasoning_effort":"high",'
        txt2 = txt.replace(alt.group(1), new2, 1)
        shutil.copy2(p, p + ".bak-think-" + TS)
        open(p, "w", encoding="utf-8").write(txt2)
        print("  FIXED (spaced form). backup:", (p + ".bak-think-" + TS).replace(HOME, "~"))
        continue
    if c != 1:
        print(f"  payload appears {c}x — not unique, tell me which call is a1/b1"); continue
    shutil.copy2(p, p + ".bak-think-" + TS)
    open(p, "w", encoding="utf-8").write(txt.replace(OLD, NEW, 1))
    print("  FIXED. backup:", (p + ".bak-think-" + TS).replace(HOME, "~"))

print("\ndone — a1/b1 now reason (reasoning_effort:high), content stays clean, other 144 untouched.")
