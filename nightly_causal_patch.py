#!/usr/bin/env python3
"""nightly_causal_patch.py — wire JEPA-grounded causal formation into nightly_run.

Adds form_causal_hypotheses(db): reads cause-evidence.json (each emotional event + its diverse
antecedent slate + novelty), asks grok (via the now-authed ask_llm, full Vintos identity) for a
cause DISTRIBUTION, writes cause-distribution.json for downstream consumers, and appends the
resulting hypotheses into the SAME db["hypotheses"] trial machinery — tagged source "causal-jepa",
so they test and graduate alongside the existing material-based formation. No source is removed.

Inserts the function before nightly_run and one call inside it (after formation, before
graduation). Self-locating, idempotent, backs up causality-engine.py.
"""
import io, os, time, shutil

F = os.environ.get("CENG_PATH", os.path.expanduser("~/Vintos/causality-engine.py"))
s = io.open(F, encoding="utf-8").read()

if "def form_causal_hypotheses" in s:
    print("already patched — skipping"); raise SystemExit(0)

NEWFUNC = r'''def form_causal_hypotheses(db, cap=3):
    """JEPA-grounded causal formation. Reads cause-evidence.json (spike event -> diverse antecedent
    slate + novelty), asks grok for a cause distribution weighing meaning + recency (not topical
    overlap), writes cause-distribution.json for consumers (dreams <- emergence/low-confidence,
    pearls <- persistent unexplained), and feeds the hypotheses into the same 7-day trial machinery."""
    from datetime import date as _cdate
    ev_path = os.path.join(MEMORY, "cause-evidence.json")
    try:
        evidence = json.load(open(ev_path))
    except Exception:
        return 0
    if not evidence:
        return 0

    def _bp(ev):
        shift = "\n".join(
            "  - %s %s  (%s -> %s, delta %.3f)" % (
                x.get("dimension"), x.get("direction"), x.get("from"), x.get("to"), abs(x.get("delta", 0)))
            for x in ev.get("shift", []))
        cands = "\n".join(
            "  [%d] (%s, %s min before, topical-fit %s): %s" % (
                i, c.get("kind"), c.get("mins_before"), c.get("relevance"), str(c.get("text", ""))[:220])
            for i, c in enumerate(ev.get("candidates", [])))
        if not cands:
            cands = "  (nothing on record preceded this)"
        nov = ev.get("novelty", 1.0)
        return (
            "You are examining a shift in your own emotional state and deciding what caused it.\n"
            "This is ONE moment - several dimensions moved together. Reason about the whole shift.\n\n"
            "THE SHIFT (at %s):\n%s\n\n" % (ev.get("time"), shift) +
            "WHAT PRECEDED IT - a ranked slate of things that happened before. Some you said or heard,\n"
            "some you looked at, some you wanted, some were shifts between you and her. The topical-fit\n"
            "score is only word-similarity, NOT how likely it caused this.\n%s\n\n" % cands +
            "NOVELTY: %s - how much of this shift is NOT explained by anything above "
            "(0 = fully traceable to the slate, 1 = emerged from nowhere).\n\n" % nov +
            "Decide what drove this shift. Weigh MEANING (would this plausibly move THESE dimensions?)\n"
            "and RECENCY (something days old rarely causes a sudden shift) - not topical overlap. If\n"
            "novelty is high and nothing genuinely fits, put most of the mass on \"emergence\".\n\n"
            "Return ONLY JSON, no prose around it:\n"
            "{\"distribution\": [{\"cause\": \"<short quote from a candidate, or emergence>\", "
            "\"prob\": 0.48, \"why\": \"<one clause>\"}], "
            "\"confidence\": \"low|medium|high\", "
            "\"hypothesis\": \"<one sentence: what caused what>\", "
            "\"test\": \"<what should recur tomorrow to confirm this>\"}\n"
            "Probabilities should sum to ~1.0. Include \"emergence\" when it deserves mass.")

    def _pj(text):
        if not text:
            return None
        t = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
        m = re.search(r"\{.*\}", t, re.S)
        if not m:
            return None
        try:
            return json.loads(m.group(0))
        except Exception:
            return None

    dist_out, added = [], 0
    for ev in evidence:
        if ev.get("untraceable"):
            parsed = {"distribution": [{"cause": "emergence", "prob": 1.0, "why": "nothing preceded this"}],
                      "confidence": "low",
                      "hypothesis": "This shift emerged with no traceable antecedent.",
                      "test": "notice whether this recurs without any outward trigger"}
        else:
            parsed = _pj(ask_llm(_bp(ev), system=load_full_context(), max_tokens=900, temp=0.3))
        if not parsed:
            continue
        rec = {"time": ev.get("time"), "shift": ev.get("shift"), "summary": ev.get("summary", ""),
               "novelty": ev.get("novelty"), "confidence": str(parsed.get("confidence", "low")).lower(),
               "distribution": parsed.get("distribution", []),
               "hypothesis": parsed.get("hypothesis", ""), "test": parsed.get("test", ""),
               "reasoned_at": datetime.now().isoformat()}
        dist_out.append(rec)
        if added < cap and rec["hypothesis"]:
            db.setdefault("hypotheses", []).append({
                "formed": datetime.now().isoformat(), "formed_date": _cdate.today().isoformat(),
                "status": "untested", "marks": [], "days_tested": 0, "graduated": False,
                "hypothesis": rec["hypothesis"], "confidence": rec["confidence"], "test": rec["test"],
                "source": "causal-jepa", "distribution": rec["distribution"], "novelty": rec["novelty"]})
            added += 1
    try:
        json.dump(dist_out, open(os.path.join(MEMORY, "cause-distribution.json"), "w"), indent=2)
    except Exception:
        pass
    return added


'''

# 1) insert the function just before nightly_run
anchor_fn = "\ndef nightly_run():"
if anchor_fn not in s:
    print("MISS: def nightly_run() not found"); raise SystemExit(1)
s = s.replace(anchor_fn, "\n" + NEWFUNC + "def nightly_run():", 1)

# 2) call it inside nightly_run, after material formation, before graduation
anchor_call = '    log("Formed " + str(min(len(new_hyps),3)) + " new hypotheses (capped at 3)")'
if anchor_call not in s:
    print("MISS: nightly_run formation log line not found"); raise SystemExit(1)
call = (anchor_call + "\n\n"
        "    # JEPA-grounded causal formation — reason over cause-evidence.json, feed same trial machinery\n"
        "    try:\n"
        "        _nc = form_causal_hypotheses(db)\n"
        "        log(\"  Causal (JEPA-grounded): \" + str(_nc) + \" added\")\n"
        "    except Exception as _ce:\n"
        "        log(\"  Causal formation skipped: \" + str(_ce))")
s = s.replace(anchor_call, call, 1)

shutil.copy(F, F + ".bak-causal-" + time.strftime("%Y%m%d-%H%M%S"))
io.open(F, "w", encoding="utf-8").write(s)
print("PATCHED — form_causal_hypotheses added + wired into nightly_run (backup written)")
