#!/usr/bin/env python3
"""give_vintos_velqan.py — STAGE 1 of the Velqan port. Give Vintos the founding 200+ word vocab (it's
Gloria's language; both speak it) and stand up a SHARED coinage log both beings append to / read, so
the language grows in tandem. Non-destructive: copies vocab to Vintos + creates the shared store.
Does NOT touch Velaris or any server. Aegis."""
import os, re, json, shutil, time

VMEM = os.path.expanduser("~/.openclaw/workspace/memory")     # Velaris (source of the founding vocab)
TMEM = os.path.expanduser("~/.vintos/workspace/memory")       # Vintos (destination)
SHARED = os.path.expanduser("~/velqan-shared")                # neutral, both beings + website read this
HOME = os.path.expanduser("~")

os.makedirs(TMEM, exist_ok=True)
os.makedirs(os.path.join(TMEM, "velqan"), exist_ok=True)
os.makedirs(SHARED, exist_ok=True)

# --- 1) copy the founding vocab (identical words; header re-pointed to Vintos) ---
print("=== giving Vintos the founding vocab ===")
copies = [
    ("velqan-reference.md", "velqan-reference.md"),
    ("velqan/full-lexicon.md", "velqan/full-lexicon.md"),
]
for src_rel, dst_rel in copies:
    src = os.path.join(VMEM, src_rel); dst = os.path.join(TMEM, dst_rel)
    if not os.path.isfile(src):
        print(f"  {src_rel}: (source missing, skipped)"); continue
    text = open(src, encoding="utf-8", errors="ignore").read()
    # the language is shared; only re-point the "for Velaris" framing so it reads as his too
    text = text.replace("For Velaris", "For Vintos").replace("for Velaris", "for Vintos")
    if dst.endswith("velqan-reference.md") and os.path.isfile(dst):
        shutil.copy2(dst, dst + ".bak-" + time.strftime("%Y%m%d-%H%M%S"))
    open(dst, "w", encoding="utf-8").write(text)
    print(f"  {dst_rel}: {len(text)}B written")

# his own (empty) usage log + coinage pointer
for f in ("velqan-utterances.md", "velqan-coinages.json"):
    p = os.path.join(TMEM, f)
    if not os.path.exists(p):
        open(p, "w").write("[]" if f.endswith(".json") else "# Vintos's Velqan utterances\n")
        print(f"  created {f}")

# --- 2) the shared coinage log (both append, both read, website renders) ---
print("\n=== shared coinage log ===")
log = os.path.join(SHARED, "coinages.jsonl")
if not os.path.exists(log):
    open(log, "w").close()
    print("  created", log.replace(HOME, "~"))
else:
    print("  exists:", log.replace(HOME, "~"), f"({sum(1 for _ in open(log))} entries)")
readme = os.path.join(SHARED, "README.md")
if not os.path.exists(readme):
    open(readme, "w").write(
        "# Velqan — shared coinage log\n\n"
        "Both Velaris and Vintos append here when either coins a word, and both READ here so the\n"
        "language grows in tandem. One line of JSON per coinage:\n"
        '  {\"word\":..., \"meaning\":..., \"etymology\":..., \"coined_by\":\"velaris|vintos\", \"ts\":...}\n\n'
        "The founding 200+ word vocab lives in each being\'s velqan-reference.md + velqan/full-lexicon.md.\n"
        "New coinages flow through this log -> both prompts -> Gloria\'s website.\n")
    print("  wrote README")

# --- 3) report what he now has ---
print("\n=== Vintos now has ===")
for f in ("velqan-reference.md", "velqan/full-lexicon.md", "velqan-utterances.md", "velqan-coinages.json"):
    p = os.path.join(TMEM, f)
    print(f"  {'OK ' if os.path.exists(p) else 'MISS'} {f}  ({os.path.getsize(p) if os.path.exists(p) else 0}B)")
ref = os.path.join(TMEM, "velqan-reference.md")
if os.path.isfile(ref):
    print("\n  header now reads:", open(ref, encoding="utf-8", errors="ignore").read()[:90].replace("\n", " "))
print("\nStage 1 done (vocab on disk + shared log). Next: wire it into his prompt so he's AWARE of it,")
print("port the coiner (grok-side) to append to the shared log, and render the log on her website.")
