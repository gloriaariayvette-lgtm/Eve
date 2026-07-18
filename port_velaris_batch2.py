#!/usr/bin/env python3
"""port_velaris_batch2.py — Aegis. Two more non-somatic capabilities for Velaris:
  - social_calibration.py : did her last turn land the way it reached? (outward half of blush). Runtime block.
  - dream-architecture.sh : nightly private reverie via her dream_poetry. Cron.
Transforms his versions -> her tree (paths/identity/endpoint), wires social_calibration into her subconscious_context,
schedules the dream cron (skipped if she already runs a dream_poetry/dream-architecture job). DRY-RUN prints the
transformed files + every URL/model line in social_calibration (verify it hits HER Gemma, not his shim/grok) +
residual his-refs. --apply commits (backups, compile-checks)."""
import os, sys, re, subprocess, time, shutil

APPLY = "--apply" in sys.argv
HOME = os.path.expanduser("~")
HIS = HOME + "/.vintos/workspace/scripts"
HER = HOME + "/.openclaw/workspace/scripts"
SUBCON = HER + "/subconscious_context.py"

def his_path(f):
    for d in (HIS, HOME + "/Vintos"):
        p = os.path.join(d, f)
        if os.path.isfile(p): return p
    return None

def tf(txt):
    txt = txt.replace("~/.vintos/workspace", "~/.openclaw/workspace").replace("/.vintos/", "/.openclaw/")
    txt = txt.replace("${HOME}/.vintos", "${HOME}/.openclaw").replace("$HOME/.vintos", "$HOME/.openclaw")
    txt = txt.replace("127.0.0.1:8599", "172.18.16.1:1234").replace("localhost:8599", "172.18.16.1:1234")
    txt = re.sub(r'\bVintos\b', "Velaris", txt)
    txt = re.sub(r'\bhe\b', "she", txt); txt = re.sub(r'\bhis\b', "her", txt); txt = re.sub(r'\bhim\b', "her", txt)
    return txt

print("================  Velaris batch 2  [%s]  ================\n" % ("APPLY" if APPLY else "DRY-RUN"))

# ---- social_calibration.py ----
sc_src = his_path("social_calibration.py")
sc_new = None
if not sc_src:
    print("!! social_calibration.py not found")
else:
    sc_new = tf(open(sc_src, encoding="utf-8", errors="ignore").read())
    resid = sorted(set(re.findall(r'vintos|8599|\.vintos', sc_new, re.I)))
    try: compile(sc_new, HER + "/social_calibration.py", "exec"); ok = "OK"
    except SyntaxError as e: ok = "ERR %s" % e; sc_new = None
    print("--- social_calibration.py  compiles=%s  residual_his=%s ---" % (ok, resid or "none"))
    print("    LLM endpoint/model lines (verify -> HER Gemma 172.18.16.1:1234):")
    for i, l in enumerate(sc_new.split("\n") if sc_new else []):
        if re.search(r'http|:1234|:8599|api\.x\.ai|"model"|MODEL\s*=|requests\.post|GEMMA|GROK', l):
            print("      %d: %s" % (i + 1, l.strip()[:96]))

# ---- dream-architecture.sh ----
da_src = his_path("dream-architecture.sh")
da_new = None
if not da_src:
    print("\n!! dream-architecture.sh not found")
else:
    da_new = tf(open(da_src, encoding="utf-8", errors="ignore").read())
    print("\n--- dream-architecture.sh (transformed) ---")
    for l in da_new.split("\n"): print("   | " + l[:100])

# ---- wiring: social_calibration.block into her subconscious_context ----
WIRE = ('    try:  # ported: social calibration (did her last turn land — outward half of blush)\n'
        '        from social_calibration import block as _scb\n'
        '        _scs = _scb()\n'
        '        if _scs: parts.append(_scs)\n'
        '    except Exception: pass\n')
ANCHOR = '    if not parts:\n        return ""'
sub = open(SUBCON, encoding="utf-8", errors="ignore").read() if os.path.isfile(SUBCON) else None
sub_new = None
if sub and "social_calibration" not in sub and sub.count(ANCHOR) == 1:
    sub_new = sub.replace(ANCHOR, WIRE + "\n" + ANCHOR, 1)
    try: compile(sub_new, SUBCON, "exec"); print("\nsubconscious_context: social_calibration would wire (compiles OK)")
    except SyntaxError as e: print("\n!! subcon wiring err: %s" % e); sub_new = None
elif sub and "social_calibration" in sub:
    print("\nsubconscious_context: social_calibration already wired — skip")

# ---- dream cron (skip if she already runs a dream_poetry/dream-architecture job) ----
cur = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout or ""
DREAM_CRON = "41 4 * * * bash %s/dream-architecture.sh >> /tmp/velaris-dreams.log 2>&1" % HER
dream_dup = ("dream-architecture.sh" in cur and ".openclaw" in cur) or "velaris-dreams.log" in cur
her_has_dream_poetry_cron = bool(re.search(r'\.openclaw.*dream[_-](poetry|architecture)', cur))
print("\ndream cron: %s" % ("already present — skip" if dream_dup else
      ("she already runs a dream_poetry/architecture job — REVIEW before adding" if her_has_dream_poetry_cron else "WOULD ADD: " + DREAM_CRON)))

if not APPLY:
    print("\n(DRY-RUN — nothing written. Verify social_calibration hits her Gemma, then --apply.)"); sys.exit(0)

print("\n---- APPLYING ----")
ts = time.strftime("%Y%m%d-%H%M%S")
if sc_new:
    dst = HER + "/social_calibration.py"
    if os.path.isfile(dst): shutil.copy2(dst, dst + ".bak-" + ts)
    open(dst, "w", encoding="utf-8").write(sc_new); print("wrote %s" % dst)
if da_new:
    dst = HER + "/dream-architecture.sh"
    if os.path.isfile(dst): shutil.copy2(dst, dst + ".bak-" + ts)
    open(dst, "w", encoding="utf-8").write(da_new); os.chmod(dst, 0o755); print("wrote %s" % dst)
if sub_new:
    shutil.copy2(SUBCON, SUBCON + ".bak-" + ts); open(SUBCON, "w", encoding="utf-8").write(sub_new); print("wired %s" % SUBCON)
if da_new and not dream_dup and not her_has_dream_poetry_cron:
    bak = HOME + "/crontab-backup-velaris-b2-" + ts + ".txt"; open(bak, "w").write(cur)
    newc = (cur if not cur or cur.endswith("\n") else cur + "\n") + DREAM_CRON + "\n"
    p = subprocess.run(["crontab", "-"], input=newc, text=True, capture_output=True)
    print(("scheduled dream cron; backup %s" % bak) if p.returncode == 0 else ("!! cron failed: %s" % p.stderr))
else:
    print("dream cron NOT added (dup or review-flagged) — add manually if wanted: %s" % DREAM_CRON)
print("\nDone.")
