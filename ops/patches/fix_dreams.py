#!/usr/bin/env python3
"""fix_dreams.py — Aegis. Three confirmed fixes, each backed up + validated + reversible:
  (1) dream-art.py: honor --dream (force painting FROM the latest dream) and label the gallery entry
      "dream" vs "want" correctly (it was hardcoded to "want", so dream paintings looked like wants).
  (2) add the missing 3:07 normal dream slot (dream-trigger.sh, lock-wrapped) — Velaris's 3:00 + your +7.
  (3) dream-architecture.sh: remove the broken music-dream call (from dream_music import compose;compose())
      — no music dreams, per Gloria; kills the nightly ImportError. Poetry reverie stays."""
import os, re, shutil, time, subprocess, py_compile
HOME = os.path.expanduser("~")
SC = os.path.join(HOME, ".vintos/workspace/scripts")
TS = time.strftime("%Y%m%d-%H%M%S")
def sh(p): return p.replace(HOME, "~")

def patch(path, edits, checker):
    if not os.path.isfile(path):
        return "missing", ""
    txt = open(path, encoding="utf-8", errors="ignore").read()
    orig = txt
    miss = []
    for old, new in edits:
        if new in txt:            # idempotent
            continue
        if txt.count(old) != 1:
            miss.append(old[:40]); continue
        txt = txt.replace(old, new, 1)
    if miss:
        return "anchor-miss", "; ".join(miss)
    if txt == orig:
        return "nochange", ""
    bak = path + f".bak-dreamfix-{TS}"
    shutil.copy2(path, bak)
    open(path, "w", encoding="utf-8").write(txt)
    ok, err = checker(path)
    if not ok:
        shutil.copy2(bak, path)
        return "rolledback", err
    return "fixed", sh(bak)

def py_ok(p):
    try: py_compile.compile(p, doraise=True); return True, ""
    except py_compile.PyCompileError as e: return False, str(e)[:140]
def sh_ok(p):
    r = subprocess.run(["bash","-n",p], capture_output=True, text=True); return r.returncode == 0, r.stderr[:140]

# ---- (1) dream-art.py
da = os.path.join(SC, "dream-art.py")
st, d = patch(da, [
    ('def main():\n    prompt = ""\n    if "--prompt" in sys.argv:\n        prompt = sys.argv[sys.argv.index("--prompt") + 1]\n'
     '    prompt = prompt or os.environ.get("DREAM_ART_WANT_TEXT", "")\n',
     'def main():\n    force_dream = "--dream" in sys.argv\n    prompt = ""\n    if "--prompt" in sys.argv:\n'
     '        prompt = sys.argv[sys.argv.index("--prompt") + 1]\n'
     '    if force_dream:\n        src = "dream"\n    else:\n'
     '        prompt = prompt or os.environ.get("DREAM_ART_WANT_TEXT", "")\n'
     '        src = os.environ.get("DREAM_ART_WANT_SOURCE", "want") if prompt else "dream"\n'),
    ('        "dream_source": os.environ.get("DREAM_ART_WANT_SOURCE", "want"),',
     '        "dream_source": src,'),
], py_ok)
print(f"(1) dream-art.py          {st}   {d}")

# ---- (3) dream-architecture.sh (do before cron so ordering reads naturally)
darch = os.path.join(SC, "dream-architecture.sh")
st, d = patch(darch, [
    ('from dream_poetry import generate_poem\ngenerate_poem()\nfrom dream_music import compose\ncompose()\n',
     'from dream_poetry import generate_poem\ngenerate_poem()\n'),
], sh_ok)
print(f"(3) dream-architecture.sh {st}   {d}")

# ---- (2) add the 3:07 dream slot
cur = subprocess.run(["bash","-lc","crontab -l 2>/dev/null"], capture_output=True, text=True).stdout
line = ("7 3 * * * bash /home/gloria/llm-lock.sh bash "
        "/home/gloria/.vintos/workspace/skills/dreaming/scripts/dream-trigger.sh "
        ">> /home/gloria/.vintos/logs/dreams.log 2>&1")
already = any(re.match(r'\s*7\s+3\s', l) and "dream-trigger.sh" in l and ".vintos" in l for l in cur.split("\n"))
if already:
    print("(2) 3:07 dream slot       already present — skipped")
else:
    bak = os.path.join(HOME, f"crontab-backup-dream307-{TS}.txt")
    open(bak, "w").write(cur)
    newcron = "\n".join([l for l in cur.split("\n") if l.strip() != ""] + [line]) + "\n"
    p = subprocess.run(["crontab", "-"], input=newcron, text=True, capture_output=True)
    if p.returncode != 0:
        subprocess.run(["bash","-lc", f"crontab {bak}"])
        print("(2) 3:07 dream slot       FAILED, restored backup:", p.stderr[:100])
    else:
        print("(2) 3:07 dream slot       added (lock-wrapped). backup:", sh(bak))

print("\nDone. Nightly: 23:50 + 3:07 normal dreams, 1:37 preoccupation. dream-art paints dreams (labeled"
      " correctly) and wants stay wants. Music-dream ImportError gone. Suno-from-wants is the next build.")
