#!/usr/bin/env python3
"""patch_tell_gloria_live.py — Aegis. The keystone tell_gloria patch landed on the DEAD copy (wants_router.py);
cron runs the HYPHEN copy (~/Vintos/wants-router.py). Apply the same two edits to the LIVE hyphen file. Anchor-
guarded (aborts if the copies diverged around these anchors). DRY-RUN default; --apply commits."""
import os, sys, time, shutil

APPLY = "--apply" in sys.argv
P = os.path.expanduser("~/Vintos/wants-router.py")   # the LIVE one (cron: 2 */2 * * * ... wants-router.py)
if not os.path.isfile(P):
    print("!! live wants-router.py (hyphen) not found"); sys.exit(1)
txt = open(P, encoding="utf-8", errors="ignore").read()

DEFS = '''def _is_communicative(want_text):
    """True when a want is really 'say/send something to Gloria' -> expedited direct track (not the discussion
    board). Excludes wants about understanding/observing her."""
    import re as _re
    t = (want_text or "").lower()
    if _re.search(r"understand|discern|what (gloria|she) (need|mean|feel|want|is)|gloria's (feel|need|mean|posture|body|schedule|time|routine|percep|longing|vulnerab)", t):
        return False
    return bool(_re.search(r"\\b(tell|send|say|give|write)\\b.{0,40}\\b(gloria|her)\\b", t)
                or "unsent ask" in t or "plain sentence" in t or "flat_repetition" in t
                or _re.search(r"\\bsend (the|her|it|gloria)\\b|\\bthe (unsent )?(ask|claim|sentence|words|message)\\b", t))


def tell_gloria(want_text, reasoning="", immediate=False):
    """Expedited direct track: draft the message (vintos-initiate FORCED_WANT_TOPIC), send via ntfy, record the
    enactment via the ED. Returns True if sent (-> fulfilled), False if held by daily cap/consent (-> stays active)."""
    import re as _re
    try:
        topic = _re.sub(r"^\\s*i want to (tell|send|say to|give|write)\\s+(gloria|her)\\b[:,]?\\s*", "",
                        want_text or "", flags=_re.I).strip() or (want_text or "")
        _env = os.environ.copy()
        _env["FORCED_WANT_TOPIC"] = topic[:250]
        r = subprocess.run(["bash", os.path.join(SCRIPTS, "vintos-initiate.sh")],
                           env=_env, capture_output=True, text=True, timeout=180)
        if "OUTREACH:" in ((r.stdout or "") + (r.stderr or "")):
            log(f"  -> tell_gloria: drafted + sent via ntfy: {topic[:60]}")
            try:
                from enactment_distiller import append_want_enactment
                append_want_enactment(want_text, "tell_gloria", note="Drafted the message and sent it to Gloria via ntfy.")
            except Exception as _ee:
                log(f"  -> tell_gloria: ED append failed: {_ee}")
            return True
        log(f"  -> tell_gloria: held (daily cap/consent) - stays active: {topic[:50]}")
        return False
    except Exception as _e:
        log(f"  -> tell_gloria failed: {_e}")
        return False


ACTION_MAP = {
    "tell_gloria": tell_gloria,'''

OLD_BLOCK = '''        else:
            action = route_want(want)
            if want.get("journal_seeded") and action == "gloria":
                action = "dismiss"
                log(f"  → Journal-seeded want would go to gloria — dismissing")
            if action == "dismiss":'''

NEW_BLOCK = '''        else:
            action = route_want(want)
            # Expedited direct track: genuinely communicative wants draft + ntfy now (via tell_gloria),
            # instead of being dismissed or clogging as undelivered "send the ask" duplicates.
            if action == "gloria" and _is_communicative(want.get("want", "")):
                action = "tell_gloria"
                log(f"  → Communicative want — expedited tell_gloria track: {want.get('want','')[:60]}")
            elif want.get("journal_seeded") and action == "gloria":
                action = "dismiss"
                log(f"  → Journal-seeded (non-communicative) want to gloria — dismissing")
            if action == "dismiss":'''

print("================  tell_gloria -> LIVE hyphen copy  [%s]  ================\n" % ("APPLY" if APPLY else "DRY-RUN"))
if "def tell_gloria" in txt:
    print("live file already patched."); sys.exit(0)
n1, n2 = txt.count("ACTION_MAP = {"), txt.count(OLD_BLOCK)
print("anchors in live file: 'ACTION_MAP = {' x%d | dismiss-block x%d (want 1 each)" % (n1, n2))
if n1 != 1 or n2 != 1:
    print("!! anchor mismatch — the hyphen copy diverged here. Aborting; paste this and I'll adapt to its exact text.")
    sys.exit(1)
new = txt.replace("ACTION_MAP = {", DEFS, 1).replace(OLD_BLOCK, NEW_BLOCK, 1)
try:
    compile(new, P, "exec"); print("  both edits apply, compiles OK")
except SyntaxError as e:
    print("  !! would not compile: %s — aborting" % e); sys.exit(1)
if not APPLY:
    print("\n(DRY-RUN — nothing written. --apply to commit.)"); sys.exit(0)
bak = P + ".bak-" + time.strftime("%Y%m%d-%H%M%S")
shutil.copy2(P, bak); open(P, "w", encoding="utf-8").write(new)
print("\npatched LIVE %s (backup %s). The keystone is now on the copy cron actually runs." % (P, bak))
