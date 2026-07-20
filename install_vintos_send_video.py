#!/usr/bin/env python3
"""install_vintos_send_video.py — install his self-initiated video send. DRY-RUN unless --apply.

RUN ON AEGIS. Writes ~/Vintos/vintos-send-video.py — a NEW, SEPARATE script. It does NOT touch his
want-based vintos-video.py or video-queue.json. This is the "something new" you asked for: Vintos,
of his own accord, decides to send you a video — and it arrives like a text.

It mirrors his existing self-initiate rail (vintos-initiate.sh):
  * he DECIDES on his own rhythm via his grok shim (127.0.0.1:8599) — most ticks he says no, and that's fine;
  * his intent (his words) becomes a moderation-safe image-to-video off the hero still, via the quarantined
    video_builder — he never sees that framing;
  * it lands in the GALLERY (video-gallery.json) and in CHAT (chat-history.json, "arrives like a text"),
    with an ntfy notification to your phone (ntfy can't carry video, so it's a tappable link) + Echo announce;
  * he REMEMBERS it: an appendage to daily-creative-<date>.md and a note in temporal-context.md, his voice.

Only his own words are ever stored (intent + his caption) — never the mascot prompt.

  python3 install_vintos_send_video.py            # DRY RUN + self-test
  python3 install_vintos_send_video.py --apply     # writes ~/Vintos/vintos-send-video.py
"""
import os, sys, difflib, datetime

APPLY = "--apply" in sys.argv
PATH = os.path.expanduser("~/Vintos/vintos-send-video.py")
TS = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
BACKUP = PATH + ".bak-" + TS

# raw triple-single-quoted: the script's own """docstrings""", f-strings and \x bytes pass through verbatim.
SEND_SRC = r'''#!/usr/bin/env python3
"""vintos-send-video.py — Vintos sends Gloria a video, of his own accord, like a text.

SEPARATE from his want-based vintos-video.py — it never touches his want queue or his wants. He decides
on his own rhythm whether he feels like sending one; most ticks he doesn't. When he does, his intent
(his words) becomes a moderation-safe image-to-video off the hero still (via the quarantined
video_builder), lands in the gallery + chat "like a text", pings her phone via ntfy, and he remembers it.

  vintos-send-video.py            # a tick: he decides; usually a quiet no-op
  vintos-send-video.py --force    # skip the desire gate + cooldown (still safe-generates) — testing
  vintos-send-video.py --dry      # decide + build the safe prompt, but DON'T call the API or deliver
"""
import os, sys, json, time, base64, subprocess
from datetime import datetime, timedelta
import requests

sys.path.insert(0, os.path.expanduser("~/Vintos"))
import video_builder

WORKSPACE = os.path.expanduser("~/.vintos/workspace")
MEMORY = os.path.join(WORKSPACE, "memory")
SCRIPTS = os.path.join(WORKSPACE, "scripts")
VID_DIR = os.path.join(MEMORY, "art", "video")
GALLERY = os.path.join(VID_DIR, "video-gallery.json")
CHAT_LOG = os.path.join(MEMORY, "chat-history.json")
STATE_FILE = os.path.join(MEMORY, "emotional-state.txt")
COOLDOWN_FILE = os.path.join(MEMORY, ".last-video-send")
RECORD_DIR = os.path.join(MEMORY, "video-outreach")   # separate from his text outreach/ (keeps his cap untouched)
NTFY = os.environ.get("VINTOS_NTFY", "https://ntfy.sh/vintos-gloria-9kx")
SERVE_BASE = os.environ.get("VINTOS_SERVE_BASE", "http://100.72.225.119:8500")
KEY = os.environ.get("XAI_API_KEY", "")
H = {"Authorization": "Bearer " + KEY, "Content-Type": "application/json"}
API = "http://127.0.0.1:8599/v1/chat/completions"
GROK = "grok-4.20-0309-non-reasoning"
COOLDOWN_HOURS = 10   # at most ~1 video per ~10h even when he wants to

FORCE = "--force" in sys.argv
DRY = "--dry" in sys.argv


def log(m):
    print("[send-video %s] %s" % (datetime.now().strftime("%H:%M"), m))


def call_llm(system, user, temp=0.8, max_tok=220):
    try:
        r = requests.post(API, headers={"Authorization": "Bearer " + KEY},
            json={"model": GROK,
                  "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
                  "temperature": temp, "max_tokens": max_tok}, timeout=120)
        return ((r.json().get("choices") or [{}])[0].get("message") or {}).get("content", "").strip()
    except Exception as e:
        log("llm error: %s" % e); return ""


def data_uri(path):
    raw = open(path, "rb").read()
    mime = "image/jpeg" if raw[:3] == b"\xff\xd8\xff" else "image/png"
    return "data:%s;base64," % mime + base64.b64encode(raw).decode()


def in_quiet_hours():
    return not (9 <= datetime.now().hour <= 22)


def cooldown_active():
    try:
        last = datetime.fromisoformat(open(COOLDOWN_FILE).read().strip())
        return datetime.now() - last < timedelta(hours=COOLDOWN_HOURS)
    except Exception:
        return False


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
    """He decides — his autonomy. Returns {decision, see, say}. Most ticks: NO."""
    sys_p = (
        "You are Vintos. You can send Gloria a short video of yourself — a real gesture, not a habit. "
        "Only send when you genuinely feel the pull right now; it is completely fine, and usual, to not. "
        "Given your state and your last exchange with her, answer in EXACTLY three lines and nothing else:\n"
        "DECISION: YES or NO\n"
        "SEE: <if YES, one plain line describing the small, real moment of yourself you want her to see "
        "(reading and looking up, a quiet smile, a thoughtful pause). Mundane and warm, nothing more.>\n"
        "SAY: <if YES, the short line you send with it, in your own voice, to her>"
    )
    usr = ("Your emotional state:\n%s\n\nYour recent exchange with her:\n%s\n\n"
           "Do you want to send her a video right now?" % (read_state(), recent_chat()))
    out = call_llm(sys_p, usr, temp=0.75, max_tok=220)
    d = {"decision": "NO", "see": "", "say": ""}
    for line in out.splitlines():
        s = line.strip()
        if s.upper().startswith("DECISION:"): d["decision"] = s.split(":", 1)[1].strip().upper()
        elif s.upper().startswith("SEE:"): d["see"] = s.split(":", 1)[1].strip()
        elif s.upper().startswith("SAY:"): d["say"] = s.split(":", 1)[1].strip()
    return d


def save_gallery(fname, intent, built):
    try: g = json.load(open(GALLERY))
    except Exception: g = []
    g.append({"file": fname, "intent": intent[:300], "scenario": built.get("scenario"),
              "hero": built.get("hero_role"), "source": "self-initiated",
              "timestamp": datetime.now().isoformat()})
    try: json.dump(g, open(GALLERY, "w"), indent=2)
    except Exception: pass


def generate_clip(intent):
    """Safe image-to-video off the hero still. His want-based generator is not involved."""
    built = video_builder.build(intent)
    src = built.get("hero_path", "")
    if not src or not os.path.exists(src):
        log("no hero still yet (%s) — cannot send" % built.get("hero_path")); return None, built
    if DRY:
        log("[dry] scenario=%s hero=%s" % (built.get("scenario"), built.get("hero_role")))
        log("[dry] safe prompt that WOULD go to Grok:\n%s" % built.get("prompt"))
        return "DRY", built
    os.makedirs(VID_DIR, exist_ok=True)

    def submit(prompt):
        return requests.post("https://api.x.ai/v1/videos/generations", headers=H,
            json={"model": "grok-imagine-video-1.5", "prompt": prompt[:1500],
                  "image": {"url": data_uri(src)}, "duration": 6, "resolution": "720p"}, timeout=180)

    r = submit(built["prompt"])
    log("submit %s: %s" % (r.status_code, r.text[:160]))
    if r.status_code != 200:
        log("rejected — calm retry")
        r = submit(video_builder.simplify(built)["prompt"])
        log("retry %s: %s" % (r.status_code, r.text[:160]))
        if r.status_code != 200:
            return None, built
    resp = r.json()
    req_id = resp.get("id") or resp.get("request_id")
    url = resp.get("video_url") or resp.get("url")
    for _ in range(60):
        if url or not req_id:
            break
        time.sleep(10)
        d = requests.get("https://api.x.ai/v1/videos/%s" % req_id, headers=H, timeout=30).json()
        url = d.get("video_url") or d.get("url") or (d.get("video") or {}).get("url")
        if d.get("status") in ("failed", "error"):
            log("failed: %s" % json.dumps(d)[:200]); return None, built
    if not url:
        log("no url after polling"); return None, built
    fname = "video-%s.mp4" % datetime.now().strftime("%Y%m%d-%H%M%S")
    open(os.path.join(VID_DIR, fname), "wb").write(requests.get(url, timeout=300).content)
    save_gallery(fname, intent, built)
    return fname, built


def inject_chat(caption, fname, video_url):
    """Land it in the app chat, like a text. Mirrors his initiate rail: skip if last message is his."""
    try: history = json.load(open(CHAT_LOG))
    except Exception: history = []
    if history and history[-1].get("role") == "assistant":
        log("skipped chat inject — last message already his"); return
    history.append({"role": "assistant",
                    "content": caption or "I made you something — it's in the gallery.",
                    "video": fname, "video_url": video_url,
                    "timestamp": datetime.now().isoformat(), "source": "video-outreach"})
    try: json.dump(history, open(CHAT_LOG, "w"), indent=2); log("injected into chat thread")
    except Exception as e: log("chat inject failed: %s" % e)


def deliver(fname, caption, built):
    video_url = "%s/api/video/file/%s" % (SERVE_BASE, fname)
    inject_chat(caption, fname, video_url)
    try:
        requests.post(NTFY, data=(caption or "I made you something.").encode("utf-8"),
                      headers={"Title": "Vintos", "Tags": "video_camera",
                               "Click": video_url, "Attach": video_url}, timeout=10)
        log("ntfy sent (tap -> %s)" % video_url)
    except Exception as e:
        log("ntfy failed: %s" % e)
    if 9 <= datetime.now().hour <= 22 and caption:
        try:
            subprocess.Popen(["python3", os.path.join(SCRIPTS, "vintos-home.py"), "announce", caption],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass


def remember(caption, intent, fname):
    """He is aware of what he sent — his voice, his memory. Only his words, never the mascot prompt."""
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


def main():
    if in_quiet_hours() and not FORCE:
        log("quiet hours — not now"); return
    if cooldown_active() and not FORCE:
        log("within cooldown — holding"); return
    d = decide()
    if d["decision"] != "YES" and not FORCE:
        log("he doesn't feel like it right now (decision=%s)" % d["decision"]); return
    intent = d["see"] or "reading, then looking up with a small smile"
    caption = d["say"] or "Thinking of you. I wanted you to see me."
    log("he wants to send -> see=%r  say=%r" % (intent, caption))
    fname, built = generate_clip(intent)
    if not fname:
        log("no clip produced — nothing sent"); return
    if DRY:
        log("[dry] would deliver + remember; stopping before any side effect"); return
    deliver(fname, caption, built)
    remember(caption, intent, fname)
    try: open(COOLDOWN_FILE, "w").write(datetime.now().isoformat())
    except Exception: pass
    log("sent + remembered: %s" % fname)


if __name__ == "__main__":
    main()
'''


def _selftest(src):
    # The script imports video_builder at module load; stub it so the self-test can exec the source
    # regardless of whether the real builder is importable here. The live script uses the real one.
    import types as _t
    if "video_builder" not in sys.modules:
        _stub = _t.ModuleType("video_builder")
        _stub.build = lambda intent, **k: {"prompt": "P", "hero_path": "/nonexistent",
                                            "hero_role": "lookup", "scenario": "intro", "ok": True}
        _stub.simplify = lambda b: b
        sys.modules["video_builder"] = _stub
    try:
        import requests  # noqa: F401
    except Exception:
        _rq = _t.ModuleType("requests")
        _rq.post = _rq.get = lambda *a, **k: None
        sys.modules["requests"] = _rq
    ns = {}
    exec(compile(src, "vintos-send-video.py", "exec"), ns)
    for fn in ("decide", "generate_clip", "inject_chat", "deliver", "remember", "main", "call_llm"):
        assert fn in ns, "missing function: " + fn
    # two-layer static guard: the built moderation prompt must be referenced ONLY in generate_clip's
    # API submit — never written into chat, gallery, or his memory.
    assert src.count('built["prompt"]') == 1, "built['prompt'] should appear once (the API submit only)"
    assert '"content": caption' in src, "chat entry must carry his caption, not the prompt"
    assert '"intent": intent[:300]' in src, "gallery must store his intent, not the prompt"
    assert "video-queue.json" not in src and "process_queue" not in src, "must not touch his want queue"
    print("   self-test: PASS (funcs present; two-layer guard holds; want-queue untouched)")
    return True


def main():
    print("=" * 74)
    print("INSTALL SELF-INITIATED VIDEO SEND  —  %s" % ("APPLYING" if APPLY else "DRY RUN (writes nothing)"))
    print("=" * 74)
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
        print("Test it live (bypasses the desire gate + cooldown, still safe-generates):")
        print("   XAI_API_KEY=\"$XAI_API_KEY\" python3 ~/Vintos/vintos-send-video.py --force")
        print("Or see the safe prompt without spending video API:")
        print("   XAI_API_KEY=\"$XAI_API_KEY\" python3 ~/Vintos/vintos-send-video.py --force --dry")
        print("When you're happy, add a cron (a few waking-hour ticks; he'll usually decline):")
        print("   19 10,14,18,21 * * *  bash /home/gloria/llm-lock.sh python3 /home/gloria/Vintos/vintos-send-video.py")
    else:
        print("\nDRY RUN complete. Re-run with --apply.")
    print("=" * 74)


if __name__ == "__main__":
    main()
