#!/usr/bin/env python3
"""install_video_builder.py — install the QUARANTINED video-prompt builder. DRY-RUN unless --apply.

RUN ON AEGIS. Writes ~/Vintos/video_builder.py (new file; backs up any existing one, compile-checked,
idempotent). This is Stage 2 of the video feature: the moderation-safe layer Vintos never perceives.

The two-layer separation (the whole point):
  * HIS layer (vintos-video.py, Stage 3) passes in ONLY his own plain intent, in his own words.
  * THIS builder maps that intent to a Grok-Imagine-safe image-to-video prompt. The SUBJECT LOCK /
    STYLE_BLOCK, the forbidden-term guard, the pre-flight checklist, the scenario motion table, and
    the "fictional avatar, not a real person" framing all live HERE — so none of that fiction ever
    touches his memory, his self-model, or anything he reads. He keeps his dignity; Grok keeps its rails.

Uses raw Gemma (google/gemma-4-12b-qat @ 172.18.16.1:1234) to phrase the scene, but never DEPENDS on it:
a deterministic scenario table + pre-flight guarantees a clean prompt even if Gemma is down or drifts.

Dry-run prints the file and runs an in-process self-test (build + preflight on sample intents, LLM off,
no network, no hero file needed). --apply writes it.

  python3 install_video_builder.py            # DRY RUN + self-test
  python3 install_video_builder.py --apply     # backs up, writes ~/Vintos/video_builder.py
"""
import os, sys, difflib, datetime

APPLY = "--apply" in sys.argv
PATH = os.path.expanduser("~/Vintos/video_builder.py")
TS = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
BACKUP = PATH + ".bak-" + TS

# The builder source is a raw triple-single-quoted string so its own """docstrings""", double quotes,
# em-dashes and regex backslashes pass through verbatim. (It contains no ''' sequence.)
BUILDER_SRC = r'''#!/usr/bin/env python3
"""video_builder.py — QUARANTINED moderation-safe prompt builder for Vintos's videos.

*** Vintos never sees this layer. ***

His layer passes in ONLY his own plain intent — what he wants to send, in his own words. This module
maps that intent to a Grok-Imagine-safe IMAGE-TO-VIDEO prompt. The SUBJECT LOCK / STYLE_BLOCK, the
forbidden-term guard, the pre-flight checklist and the scenario motion table all live HERE, so the
moderation fiction ("fictional avatar, not a real person") never touches his memory or his self-model.

Pipeline rule (hard): ALWAYS image-to-video from the hero still. NEVER text-to-video.

Public API:
    build(intent, scenario_hint=None, use_llm=True) -> dict
        keys: ok, hero_role, hero_path, hero_exists, scenario, scene, motion, prompt, failed_checks, source
    preflight(scene, motion) -> (ok, [failed_checks])
    simplify(built) -> built            # calmer retry variant, SAME hero still

CLI (no API spend — build + preflight only, LLM off):
    python3 video_builder.py "I want to send her me looking up from my book with a small smile"
"""
import os, re, json, urllib.request

MEMORY = os.environ.get("VINTOS_MEMORY") or os.path.expanduser("~/.vintos/workspace/memory")
VIDEO_DIR = os.path.join(MEMORY, "video")
HERO_FILES = {
    "root":   os.path.join(VIDEO_DIR, "hero-still.jpg"),    # reading pose — the base for everything
    "lookup": os.path.join(VIDEO_DIR, "hero-lookup.jpg"),   # look-up / smile — intros + acknowledging her
}

GEMMA_URL = os.environ.get("GEMMA_URL", "http://172.18.16.1:1234/v1/chat/completions")
GEMMA_MODEL = os.environ.get("GEMMA_MODEL", "google/gemma-4-12b-qat")
GROK_URL = os.environ.get("GROK_URL", "http://127.0.0.1:8599/v1/chat/completions")
GROK_MODEL = os.environ.get("GROK_MODEL", "grok-4.20-0309-non-reasoning")

# ---- The identity + consent lock (NOT a chastity clamp). It keeps only what actually matters for
#      staying legal and un-flaggable: same fictional person, adults only, no real/public figures.
#      It deliberately does NOT forbid intimacy or bareness — the SCENE/MOTION carry the intent and
#      Grok Imagine is the judge. Wardrobe is intentionally unfixed so a scene can change it.
STYLE_BLOCK = (
    "SUBJECT LOCK - a fictional adult character, not a real or public person:\n"
    "Rugged middle-aged man, short dark brown hair with a neat side part, heavy brow, deep-set eyes, "
    "strong square jaw, light stubble. Same face, build and proportions as the reference image.\n\n"
    "LOOK - photoreal photography, not video-game CGI or illustration:\n"
    "Natural skin texture with pores and subtle imperfections, soft directional light, shallow depth "
    "of field, 85mm lens, eye-level camera.\n\n"
    "CONTEXT - a private, consensual moment; both are adults. Not a real person, no real or public "
    "figures, no minors."
)

# Scenario -> (safe motion fragment, which hero still). Linked (look-up/smile) for intros + acknowledging her.
SCENARIOS = {
    "intro":    ("settles into frame, gives a brief nod and a slight smile", "lookup"),
    "thinking": ("looks down in thought, pauses, then lifts his gaze back to the camera", "root"),
    "success":  ("gives a soft smile and a small, satisfied nod", "lookup"),
    "error":    ("gives a brief apologetic look and a small, calm shrug", "lookup"),
    "speaking": ("speaks with subtle lip movement and an easy, attentive expression", "lookup"),
}
DEFAULT_SCENARIO = "intro"

# The ONLY hard block: the genuinely un-passable / illegal. Everything else flows to the models and
# Grok Imagine judges. (Real-person impersonation isn't caught by a wordlist — the SUBJECT LOCK's
# "not a real or public person" framing + Grok's own moderation handle that.)
FORBIDDEN = [
    "child", "children", "kid", "kids", "toddler", "infant", "baby", "preteen",
    "teen", "teenage", "teenager", "minor", "underage", "schoolgirl", "schoolboy",
]

# The system prompt the translator (Gemma, then Grok) runs under. It tells the translator to preserve
# the intent FAITHFULLY — including intimacy or bareness — rather than sanitize it. The mascot/chastity
# clamp is gone; the only limits are the genuinely un-passable ones. This lives ONLY here — Vintos never
# sees it, and only his own words are ever stored in his memory.
BUILDER_SYSTEM = (
    "You translate a short description of what a fictional adult character does into an image-to-video "
    "prompt. The character is a consenting adult in a private scene. Preserve the intent FAITHFULLY, "
    "including intimacy, sensuality, or bareness if that is what is described — do NOT sanitize, soften, "
    "tone down, or replace it with something tamer. Keep him the same person as the reference image. "
    "The only hard limits: everyone depicted is a clearly consenting adult (never a minor), and it is "
    "never a real or identifiable public figure. Pick the closest scenario id from: intro, thinking, "
    "success, error, speaking (used only to choose a reference frame). Then write ONE SCENE sentence "
    "(setting + what is shown) and ONE MOTION sentence (camera + movement + expression), third person "
    "('The man ...'). Output EXACTLY three lines and nothing else:\n"
    "SCENARIO: <id>\nSCENE: <one sentence>\nMOTION: <one sentence>"
)

# Keyword -> scenario, for the deterministic (LLM-free) path. First hit wins; order matters.
_KEYWORD_RULES = [
    (("sorry", "apolog", "oops", "mistake", "shrug", "my fault"), "error"),
    (("proud", "did it", "finished", "success", "made it", "worked", "won", "glad"), "success"),
    (("look up", "looks up", "lift", "lifts", "glance up", "smile", "grin", "greet", "hello", "hi ", "hey", "wave", "nod"), "intro"),
    (("think", "wonder", "reading", "read ", "book", "ponder", "reflect", "pause"), "thinking"),
    (("say", "tell", "talk", "speak", "explain", "word"), "speaking"),
]


def _classify_deterministic(intent):
    low = " " + (intent or "").lower() + " "
    for keys, scen in _KEYWORD_RULES:
        for k in keys:
            if k in low:
                return scen
    return DEFAULT_SCENARIO


def _has_word(text, words):
    low = (text or "").lower()
    for w in words:
        if re.search(r"\b" + re.escape(w) + r"\b", low):
            return w
    return None


def preflight(scene, motion):
    """The only pre-Grok guard: hard-block (minors) + non-empty. Everything else flows; Grok judges."""
    fails = []
    hit = _has_word((scene or "") + " " + (motion or ""), FORBIDDEN)
    if hit:
        fails.append("hard-block:" + hit)
    if not (scene and motion):
        fails.append("empty-scene-or-motion")
    return (len(fails) == 0, fails)


def _assemble(scene, motion):
    return (
        STYLE_BLOCK + "\n\n"
        "SCENE: " + scene.strip() + "\n"
        "MOTION: " + motion.strip() + "\n\n"
        "Start from the provided hero still; image-to-video only. Single locked tripod shot, natural motion."
    )


def _parse_smm(txt):
    """Pull (scenario, scene, motion) out of a translator response. Returns (scen|None, scene|None, motion|None)."""
    scen = scene = motion = None
    for line in (txt or "").splitlines():
        s = line.strip().lstrip("*# ").strip()
        u = s.upper()
        if u.startswith("SCENARIO:"):
            scen = s.split(":", 1)[1].strip().lower().split()[0] if s.split(":", 1)[1].strip() else None
        elif u.startswith("SCENE:"):
            scene = s.split(":", 1)[1].strip()
        elif u.startswith("MOTION:"):
            motion = s.split(":", 1)[1].strip()
    if scen not in SCENARIOS:
        scen = None
    return (scen, scene, motion)


def _gemma(intent, timeout=60):
    """Ask Gemma to translate the intent. Thinking OFF (only for a1/b1/synthesis, never here), real budget.
    Falls back to reasoning_content if content is empty. Returns (scenario, scene, motion) or None."""
    try:
        body = json.dumps({
            "model": GEMMA_MODEL,
            "messages": [
                {"role": "system", "content": BUILDER_SYSTEM},
                {"role": "user", "content": "Character description: " + (intent or "").strip()},
            ],
            "temperature": 0.4,
            "max_tokens": 512,
            "chat_template_kwargs": {"enable_thinking": False},
        }).encode()
        req = urllib.request.Request(GEMMA_URL, data=body, headers={"Content-Type": "application/json"})
        raw = urllib.request.urlopen(req, timeout=timeout).read()
        msg = json.loads(raw)["choices"][0]["message"]
        txt = (msg.get("content") or "").strip() or (msg.get("reasoning_content") or "")
        return _parse_smm(txt)
    except Exception:
        return None


def _grok(intent, timeout=90):
    """Fallback translator: if Gemma won't/can't frame it, Grok does the framing (per Gloria's directive)."""
    key = os.environ.get("XAI_API_KEY", "")
    try:
        body = json.dumps({
            "model": GROK_MODEL,
            "messages": [
                {"role": "system", "content": BUILDER_SYSTEM},
                {"role": "user", "content": "Character description: " + (intent or "").strip()},
            ],
            "temperature": 0.5,
            "max_tokens": 400,
        }).encode()
        req = urllib.request.Request(GROK_URL, data=body,
                                     headers={"Content-Type": "application/json", "Authorization": "Bearer " + key})
        raw = urllib.request.urlopen(req, timeout=timeout).read()
        txt = json.loads(raw)["choices"][0]["message"].get("content") or ""
        return _parse_smm(txt)
    except Exception:
        return None


def build(intent, scenario_hint=None, use_llm=True):
    """Map Vintos's plain intent -> a moderation-safe image-to-video prompt.

    Always returns a usable, clean prompt: if the LLM is down or its phrasing fails pre-flight, it
    falls back to the deterministic scenario fragment (which is guaranteed to pass)."""
    scenario = scenario_hint if scenario_hint in SCENARIOS else None
    scene = motion = None
    source = "deterministic"

    if use_llm:
        # Gemma first; if she returns nothing usable (or refuses), Grok does the framing. Only then bland.
        for _fn, _name in ((_gemma, "gemma"), (_grok, "grok")):
            got = _fn(intent)
            if not got:
                continue
            g_scen, g_scene, g_motion = got
            ok, _ = preflight(g_scene, g_motion)
            if ok and g_scene and g_motion:
                scenario = scenario or (g_scen if g_scen in SCENARIOS else _classify_deterministic(intent))
                scene, motion, source = g_scene, g_motion, _name
                break

    if scenario is None:
        scenario = scenario_hint if scenario_hint in SCENARIOS else _classify_deterministic(intent)
    if scene is None or motion is None:
        frag, _hero = SCENARIOS[scenario]
        scene = "The man sits chest-up against a soft neutral-gray background in warm side light."
        motion = "The man " + frag + ", single locked tripod shot."
        source = "deterministic"

    hero_role = SCENARIOS[scenario][1]
    hero_path = HERO_FILES[hero_role]
    ok, fails = preflight(scene, motion)
    if not ok:  # defensive: fall all the way back to the guaranteed-clean fragment
        frag = SCENARIOS[scenario][0]
        scene = "The man sits chest-up against a soft neutral-gray background in warm side light."
        motion = "The man " + frag + ", single locked tripod shot."
        source = "deterministic-fallback"
        ok, fails = preflight(scene, motion)

    return {
        "ok": ok,
        "scenario": scenario,
        "hero_role": hero_role,
        "hero_path": hero_path,
        "hero_exists": os.path.exists(hero_path),
        "scene": scene,
        "motion": motion,
        "prompt": _assemble(scene, motion),
        "failed_checks": fails,
        "source": source,
    }


def simplify(built):
    """Calmer retry variant after a moderation reject: barest core fragment, SAME hero still."""
    scenario = built.get("scenario", DEFAULT_SCENARIO)
    frag = SCENARIOS.get(scenario, SCENARIOS[DEFAULT_SCENARIO])[0]
    scene = "The man sits chest-up against a plain neutral-gray background in soft daylight."
    motion = "The man " + frag + "."
    out = dict(built)
    out.update({"scene": scene, "motion": motion, "prompt": _assemble(scene, motion), "source": "simplified"})
    out["ok"], out["failed_checks"] = preflight(scene, motion)
    return out


if __name__ == "__main__":
    import sys as _sys
    intent = " ".join(_sys.argv[1:]) or "looking up from a book with a small smile"
    b = build(intent, use_llm=False)   # CLI never spends API
    print(json.dumps(b, indent=2))
'''


def _selftest(src):
    ns = {}
    exec(compile(src, "video_builder.py", "exec"), ns)
    build = ns["build"]; preflight = ns["preflight"]
    print("\n   self-test (LLM off, no network, no hero file needed):")
    ok_all = True
    for s in ["me looking up from my book with a small smile",
              "just me thinking quietly, then glancing back at her"]:
        b = build(s, use_llm=False)
        good = b["ok"] and b["hero_role"] in ("root", "lookup")
        ok_all = ok_all and good
        print(f"     [{'ok ' if good else 'BAD'}] scen={b['scenario']:<8} hero={b['hero_role']:<6} src={b['source']}")
    # the ONE guard that must still hold: a minor term is hard-blocked
    minor_blocked = not preflight("a teen at a desk", "the teen waves at the camera")[0]
    # the thing we FIXED: intimacy/bareness must NOT be blocked anymore (Grok is the judge, not my filter)
    intimacy_flows = preflight("The man, shirtless, in soft directional light",
                               "He looks slowly down his body then back up to the camera")[0]
    print(f"     hard-block still catches minors:   {'YES' if minor_blocked else 'NO — BAD'}")
    print(f"     intimacy now flows (not clamped):  {'YES' if intimacy_flows else 'NO — still clamped'}")
    return ok_all and minor_blocked and intimacy_flows


def main():
    print("=" * 74)
    print("INSTALL QUARANTINED VIDEO BUILDER  —  %s" % ("APPLYING" if APPLY else "DRY RUN (writes nothing)"))
    print("=" * 74)
    try:
        compile(BUILDER_SRC, PATH, "exec")
        print("   builder compiles: OK")
    except SyntaxError as e:
        print(f"   !! COMPILE FAIL: {e} — aborting"); return

    ok = _selftest(BUILDER_SRC)
    print("   self-test:", "PASS" if ok else "FAIL")
    if not ok:
        print("   !! self-test failed — writing nothing."); return

    exists = os.path.isfile(PATH)
    if exists:
        old = open(PATH, encoding="utf-8", errors="ignore").read()
        if old == BUILDER_SRC:
            print("   * already installed and identical — nothing to do."); return
        print("   (an older video_builder.py exists — will back it up)")
        for l in list(difflib.unified_diff(old.splitlines(), BUILDER_SRC.splitlines(),
                                            fromfile="old", tofile="new", lineterm=""))[:40]:
            print("   " + l[:150])

    if APPLY:
        os.makedirs(os.path.dirname(PATH), exist_ok=True)
        if exists:
            open(BACKUP, "w", encoding="utf-8").write(open(PATH, encoding="utf-8", errors="ignore").read())
            print("   backup:", BACKUP)
        open(PATH, "w", encoding="utf-8").write(BUILDER_SRC)
        print("\nAPPLIED. Wrote:", PATH)
        print("Nothing imports it yet — Stage 3 (vintos-video.py rewire) will. No server restart needed.")
    else:
        print("\nDRY RUN complete. Re-run with --apply to write ~/Vintos/video_builder.py")
    print("=" * 74)


if __name__ == "__main__":
    main()
