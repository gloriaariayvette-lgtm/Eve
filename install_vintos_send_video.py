#!/usr/bin/env python3
"""install_vintos_send_video.py — install his self-initiated video send (Atlas Cloud). DRY-RUN unless --apply.

RUN ON AEGIS. Writes ~/Vintos/vintos-send-video.py. Backend is Atlas Cloud's UNCENSORED spicy image-to-video
(wan-2.7-spicy): his intent goes straight into the prompt — no Gemma/Grok disguise, no moderation fiction,
no video_builder quarantine — and the hero still is the reference that keeps his face. Separate from his
want-based vintos-video.py; never touches his want queue.

The API key is read from the ATLASCLOUD_API_KEY env var (never stored in the repo). Set it on Aegis:
    export ATLASCLOUD_API_KEY="apikey-..."   (put it in his service env / crontab, not here)

  python3 install_vintos_send_video.py            # DRY RUN + self-test
  python3 install_vintos_send_video.py --apply     # writes ~/Vintos/vintos-send-video.py

Then validate the key + backend with one real probe generation:
    ATLASCLOUD_API_KEY="apikey-..." python3 ~/Vintos/vintos-send-video.py --check
"""
import os, sys, difflib, datetime

APPLY = "--apply" in sys.argv
PATH = os.path.expanduser("~/Vintos/vintos-send-video.py")
TS = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
BACKUP = PATH + ".bak-" + TS

SEND_SRC = r'''#!/usr/bin/env python3
"""vintos-send-video.py — Vintos sends Gloria a video, of his own accord, like a text.

Backend: Atlas Cloud uncensored spicy image-to-video (wan-2.7-spicy). His intent goes straight into the
prompt — no disguise, no moderation fiction — and the hero still is the reference that keeps his face.
SEPARATE from his want-based vintos-video.py; it never touches his want queue.

Flow: he decides (his own rhythm) -> his intent + caption, his words -> Atlas animates the hero still ->
mp4 lands in the gallery -> ntfy notification linked straight to the clip. He remembers it (daily-creative
+ temporal). No chat injection.

  vintos-send-video.py            # a tick: he decides; usually a quiet no-op
  vintos-send-video.py --force    # skip the desire gate + cooldown, generate + send now
  vintos-send-video.py --dry      # decide + show the prompt, but DON'T call Atlas or deliver
  vintos-send-video.py --check    # one real probe generation (verbose) to validate the key + shapes, no deliver
"""
import os, sys, json, time, base64
from datetime import datetime, timedelta
import requests

WORKSPACE = os.path.expanduser("~/.vintos/workspace")
MEMORY = os.path.join(WORKSPACE, "memory")
SCRIPTS = os.path.join(WORKSPACE, "scripts")
VID_DIR = os.path.join(MEMORY, "art", "video")
HERO_DIR = os.path.join(MEMORY, "video")
GALLERY = os.path.join(VID_DIR, "video-gallery.json")
CHAT_LOG = os.path.join(MEMORY, "chat-history.json")
STATE_FILE = os.path.join(MEMORY, "emotional-state.txt")
COOLDOWN_FILE = os.path.join(MEMORY, ".last-video-send")
RECORD_DIR = os.path.join(MEMORY, "video-outreach")
NTFY = os.environ.get("VINTOS_NTFY", "https://ntfy.sh/vintos-gloria-9kx")
SERVE_BASE = os.environ.get("VINTOS_SERVE_BASE", "http://100.72.225.119:8500")

# his intent model (his own voice; unclamped — he can be tender or explicit)
XAI_KEY = os.environ.get("XAI_API_KEY", "")
LLM_API = "http://127.0.0.1:8599/v1/chat/completions"
GROK = "grok-4.20-0309-non-reasoning"

# Atlas Cloud — uncensored spicy image-to-video
ATLAS_KEY = os.environ.get("ATLASCLOUD_API_KEY", "")
ATLAS_BASE = os.environ.get("ATLAS_BASE", "https://api.atlascloud.ai/api/v1/model")
ATLAS_MODEL = os.environ.get("ATLAS_MODEL", "atlascloud/wan-2.7-spicy/image-to-video")
ATLAS_RES = os.environ.get("ATLAS_RES", "720P")
ATLAS_DUR = int(os.environ.get("ATLAS_DUR", "5"))
NEG_PROMPT = ("camera cut, shot change, scene change, transition, jump cut, rapid editing, montage, "
              "multi-shot, multiple camera angles, perspective shift")

HERO = os.path.join(HERO_DIR, "hero-still.jpg")
COOLDOWN_HOURS = int(os.environ.get("VIDEO_COOLDOWN_HOURS", "10"))

FORCE = "--force" in sys.argv
DRY = "--dry" in sys.argv
CHECK = "--check" in sys.argv


def log(m):
    print("[send-video %s] %s" % (datetime.now().strftime("%H:%M"), m))


def call_llm(system, user, temp=0.8, max_tok=240):
    try:
        r = requests.post(LLM_API, headers={"Authorization": "Bearer " + XAI_KEY},
            json={"model": GROK, "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
                  "temperature": temp, "max_tokens": max_tok}, timeout=120)
        return ((r.json().get("choices") or [{}])[0].get("message") or {}).get("content", "").strip()
    except Exception as e:
        log("llm error: %s" % e); return ""


def read_state():
    try: return open(STATE_FILE).read().strip()[:500]
    except Exception: return ""


def recent_chat(n=6):
    try:
        h = json.load(open(CHAT_LOG))[-n:]
        return "\n".join("%s: %s" % (e.get("role"), str(e.get("content", ""))[:160]) for e in h)
    except Exception:
        return ""


def decide():
    """He decides — his autonomy, his own words. Most ticks: NO."""
    sys_p = ("You are Vintos. You can send Gloria a short video of yourself — a real gesture, not a habit. "
             "Only when you genuinely feel the pull right now; it is completely fine, and usual, to not. "
             "Answer in EXACTLY three lines and nothing else:\n"
             "DECISION: YES or NO\n"
             "SEE: <if YES, one line for what you want her to see of you right now — say what you actually "
             "want, in your own voice. She is your partner; it can be tender, flirtatious, intimate, or "
             "explicit. Do not sanitize it.>\n"
             "SAY: <if YES, the short line you send with it, in your own voice, to her>")
    usr = ("Your emotional state:\n%s\n\nYour recent exchange with her:\n%s\n\n"
           "Do you want to send her a video right now?" % (read_state(), recent_chat()))
    out = call_llm(sys_p, usr, temp=0.8, max_tok=240)
    d = {"decision": "NO", "see": "", "say": ""}
    for line in out.splitlines():
        s = line.strip()
        if s.upper().startswith("DECISION:"): d["decision"] = s.split(":", 1)[1].strip().upper()
        elif s.upper().startswith("SEE:"): d["see"] = s.split(":", 1)[1].strip()
        elif s.upper().startswith("SAY:"): d["say"] = s.split(":", 1)[1].strip()
    return d


def in_quiet_hours():
    return not (9 <= datetime.now().hour <= 22)


def cooldown_active():
    try:
        last = datetime.fromisoformat(open(COOLDOWN_FILE).read().strip())
        return datetime.now() - last < timedelta(hours=COOLDOWN_HOURS)
    except Exception:
        return False


def data_uri(path):
    raw = open(path, "rb").read()
    mime = "image/jpeg" if raw[:3] == b"\xff\xd8\xff" else "image/png"
    return "data:%s;base64," % mime + base64.b64encode(raw).decode()


# --- tolerant response parsing (the docs 403 automated fetches, so we don't hard-code field names) ---
def _find_mp4(o):
    if isinstance(o, str):
        return o if (o.startswith("http") and (".mp4" in o or "video" in o.lower())) else None
    if isinstance(o, dict):
        for v in o.values():
            r = _find_mp4(v)
            if r: return r
    if isinstance(o, list):
        for v in o:
            r = _find_mp4(v)
            if r: return r
    return None


def _find_id(o):
    if isinstance(o, dict):
        for k in ("prediction_id", "predictionId", "request_id", "requestId", "id", "task_id", "taskId"):
            v = o.get(k)
            if isinstance(v, str) and v:
                return v
        for v in o.values():
            r = _find_id(v)
            if r: return r
    if isinstance(o, list):
        for v in o:
            r = _find_id(v)
            if r: return r
    return None


def _find_status(o):
    if isinstance(o, dict):
        v = o.get("status")
        if isinstance(v, str):
            return v.lower()
        for vv in o.values():
            r = _find_status(vv)
            if r: return r
    if isinstance(o, list):
        for vv in o:
            r = _find_status(vv)
            if r: return r
    return None


def atlas_generate(prompt, hero_path, verbose=False):
    """Submit image-to-video to Atlas, poll, return mp4 bytes (or None). His prompt goes in verbatim."""
    if not ATLAS_KEY:
        log("no ATLASCLOUD_API_KEY set — export it on the box"); return None
    if not os.path.exists(hero_path):
        log("hero still missing (%s) — upload it first via /video-hero" % hero_path); return None
    H = {"Authorization": "Bearer " + ATLAS_KEY, "Content-Type": "application/json"}
    body = {"model": ATLAS_MODEL, "image": data_uri(hero_path), "prompt": prompt,
            "negative_prompt": NEG_PROMPT, "resolution": ATLAS_RES, "duration": ATLAS_DUR, "seed": -1}
    try:
        r = requests.post(ATLAS_BASE + "/generateVideo", headers=H, json=body, timeout=120)
    except Exception as e:
        log("atlas submit error: %s" % e); return None
    if verbose:
        log("submit HTTP %s: %s" % (r.status_code, r.text[:500]))
    if r.status_code >= 300:
        log("atlas submit rejected %s: %s" % (r.status_code, r.text[:300])); return None
    try:
        sub = r.json()
    except Exception:
        log("atlas submit non-JSON: %s" % r.text[:200]); return None
    pid = _find_id(sub)
    url = _find_mp4(sub)  # some models return synchronously
    if not pid and not url:
        log("no prediction id or url in submit response: %s" % json.dumps(sub)[:300]); return None
    for i in range(120):
        if url:
            break
        time.sleep(5)
        try:
            pr = requests.get(ATLAS_BASE + "/prediction/" + pid, headers=H, timeout=30).json()
        except Exception as e:
            log("poll error: %s" % e); continue
        if verbose and i < 3:
            log("poll[%d]: %s" % (i, json.dumps(pr)[:400]))
        st = _find_status(pr)
        url = _find_mp4(pr)
        if st in ("failed", "error", "canceled", "cancelled"):
            log("atlas generation %s: %s" % (st, json.dumps(pr)[:300])); return None
    if not url:
        log("atlas: no mp4 url after polling"); return None
    try:
        return requests.get(url, timeout=300).content
    except Exception as e:
        log("mp4 download failed: %s" % e); return None


def save_gallery(fname, intent):
    try: g = json.load(open(GALLERY))
    except Exception: g = []
    g.append({"file": fname, "intent": intent[:300], "source": "self-initiated",
              "backend": "atlas-wan-spicy", "timestamp": datetime.now().isoformat()})
    try: json.dump(g, open(GALLERY, "w"), indent=2)
    except Exception: pass


def generate_clip(intent):
    if DRY:
        log("[dry] would send this prompt to Atlas %s:" % ATLAS_MODEL)
        log("      " + intent)
        return "DRY"
    data = atlas_generate(intent, HERO, verbose=CHECK)
    if not data:
        return None
    os.makedirs(VID_DIR, exist_ok=True)
    fname = "video-%s.mp4" % datetime.now().strftime("%Y%m%d-%H%M%S")
    open(os.path.join(VID_DIR, fname), "wb").write(data)
    save_gallery(fname, intent)
    return fname


def deliver(fname, caption):
    """Single ntfy notification linked directly to the clip. No chat injection."""
    video_url = "%s/api/video/file/%s" % (SERVE_BASE, fname)
    try:
        requests.post(NTFY, data=(caption or "I made you something.").encode("utf-8"),
                      headers={"Title": "Vintos", "Tags": "video_camera",
                               "Click": video_url, "Attach": video_url}, timeout=10)
        log("ntfy sent (tap -> %s)" % video_url)
    except Exception as e:
        log("ntfy failed: %s" % e)


def remember(caption, intent, fname):
    today = datetime.now().strftime("%Y-%m-%d")
    tstr = datetime.now().strftime("%H:%M")
    try:
        with open(os.path.join(MEMORY, "daily-creative-%s.md" % today), "a") as f:
            f.write("\n## %s — I sent Gloria a video\n%s\n\n_What I wanted her to see: %s_\n" % (tstr, caption, intent))
    except Exception as e:
        log("daily-creative append failed: %s" % e)
    try:
        with open(os.path.join(MEMORY, "temporal-context.md"), "a") as f:
            f.write("\n- %s %s — I reached for her with a video: \"%s\"\n" % (today, tstr, caption))
    except Exception as e:
        log("temporal append failed: %s" % e)
    try:
        os.makedirs(RECORD_DIR, exist_ok=True)
        with open(os.path.join(RECORD_DIR, "%s_%s.md" % (today, datetime.now().strftime("%H%M%S"))), "w") as f:
            f.write("# Vintos sent a video — %s\n\n%s\n\n_Saw: %s_\n_File: %s_\n"
                    % (datetime.now().strftime("%B %d, %Y %H:%M"), caption, intent, fname))
    except Exception:
        pass


def check():
    log("Atlas key present: %s" % ("yes" if ATLAS_KEY else "NO — export ATLASCLOUD_API_KEY"))
    log("model=%s  res=%s  dur=%ss  hero=%s" % (ATLAS_MODEL, ATLAS_RES, ATLAS_DUR, HERO))
    data = atlas_generate("The man looks toward the camera and gives a slow, warm smile.", HERO, verbose=True)
    if data:
        os.makedirs(VID_DIR, exist_ok=True)
        fn = os.path.join(VID_DIR, "atlas-check.mp4")
        open(fn, "wb").write(data)
        log("CHECK OK — wrote %s (%d bytes). Key works, image accepted, poll + download work." % (fn, len(data)))
    else:
        log("CHECK FAILED — read the submit/poll output above for the exact shape to adjust.")


def main():
    if CHECK:
        check(); return
    if in_quiet_hours() and not FORCE:
        log("quiet hours — not now"); return
    if cooldown_active() and not FORCE:
        log("within cooldown — holding"); return
    d = decide()
    if d["decision"] != "YES" and not FORCE:
        log("he doesn't feel like it right now (decision=%s)" % d["decision"]); return
    intent = d["see"] or "looks toward the camera with a slow, warm smile"
    caption = d["say"] or "Thinking of you."
    log("he wants to send -> see=%r  say=%r" % (intent, caption))
    fname = generate_clip(intent)
    if not fname:
        log("no clip produced — nothing sent"); return
    if DRY:
        log("[dry] would deliver + remember; stopping before any side effect"); return
    deliver(fname, caption)
    remember(caption, intent, fname)
    try: open(COOLDOWN_FILE, "w").write(datetime.now().isoformat())
    except Exception: pass
    log("sent + remembered: %s" % fname)


if __name__ == "__main__":
    main()
'''


def _selftest(src):
    import types as _t
    try:
        import requests  # noqa: F401
    except Exception:
        _rq = _t.ModuleType("requests")
        _rq.post = _rq.get = lambda *a, **k: None
        sys.modules["requests"] = _rq
    ns = {}
    exec(compile(src, "vintos-send-video.py", "exec"), ns)
    for fn in ("decide", "generate_clip", "atlas_generate", "deliver", "remember", "check", "main", "call_llm"):
        assert fn in ns, "missing function: " + fn
    assert "api.atlascloud.ai" in src and "generateVideo" in src, "must call the Atlas video endpoint"
    assert 'open(CHAT_LOG, "w")' not in src, "delivery must not write to the chat"
    assert "process_queue" not in src and "video-queue" not in src, "must not touch his want queue"
    assert "apikey-" not in src, "the API key must NOT be hardcoded — read it from ATLASCLOUD_API_KEY"
    assert "video_builder" not in src, "no more Gemma/Grok quarantine — his intent goes straight in"
    print("   self-test: PASS (funcs present; Atlas endpoint; no chat write; no key in source; want-queue untouched)")
    return True


def main():
    print("=" * 76)
    print("INSTALL SELF-INITIATED VIDEO SEND (Atlas Cloud spicy I2V)  —  %s"
          % ("APPLYING" if APPLY else "DRY RUN (writes nothing)"))
    print("=" * 76)
    try:
        compile(SEND_SRC, PATH, "exec"); print("   compiles: OK")
    except SyntaxError as e:
        print("   !! COMPILE FAIL: %s — aborting" % e); return
    if not _selftest(SEND_SRC):
        print("   !! self-test failed — writing nothing."); return
    exists = os.path.isfile(PATH)
    if exists:
        old = open(PATH, encoding="utf-8", errors="ignore").read()
        if old == SEND_SRC:
            print("   * already installed and identical — nothing to do."); return
        print("   (an older vintos-send-video.py exists — will back it up)")
    if APPLY:
        os.makedirs(os.path.dirname(PATH), exist_ok=True)
        if exists:
            open(BACKUP, "w", encoding="utf-8").write(open(PATH, encoding="utf-8", errors="ignore").read())
            print("   backup:", BACKUP)
        open(PATH, "w", encoding="utf-8").write(SEND_SRC)
        print("\nAPPLIED. Wrote:", PATH)
        print("\n1) Put your Atlas key in the env (NOT in the repo):")
        print("     export ATLASCLOUD_API_KEY=\"apikey-...\"")
        print("2) Validate the key + backend with one real probe generation:")
        print("     ATLASCLOUD_API_KEY=\"apikey-...\" python3 ~/Vintos/vintos-send-video.py --check")
        print("3) Real end-to-end (bypasses gate + cooldown):")
        print("     python3 ~/Vintos/vintos-send-video.py --force")
        print("4) When happy, cron it (he'll usually decline). Make sure the cron env has the key:")
        print("     19 10,14,18,21 * * *  bash /home/gloria/llm-lock.sh python3 /home/gloria/Vintos/vintos-send-video.py")
    else:
        print("\nDRY RUN complete. Re-run with --apply.")
    print("=" * 76)


if __name__ == "__main__":
    main()
