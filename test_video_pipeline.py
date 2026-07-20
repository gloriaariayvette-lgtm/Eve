#!/usr/bin/env python3
"""test_video_pipeline.py — REAL, instrumented end-to-end test of the video pipeline. Saves/sends NOTHING.

RUN ON AEGIS. Shows exactly where an intent dies before Grok ever judges it — the 3-model chokepoint:

    (1) his intent model (grok shim :8599)  ->  (2) Gemma translation (video_builder)  ->  (3) Grok

For each stage it prints the RAW output, so you can see: did his model refuse/clamp? did Gemma refuse or
did MY preflight nuke Gemma's translation into the bland fallback? what prompt would actually reach Grok?

Modes:
  test_video_pipeline.py                       # his decide() (real context) -> Gemma -> print (no Grok spend)
  test_video_pipeline.py --loose               # same, but drop the "mundane and warm" clamp on his intent
  test_video_pipeline.py --intent "REAL THING" # skip his model; feed a real intent straight into Gemma
  test_video_pipeline.py --loose --grok        # ALSO submit to Grok and report accept/reject (spends video API)

Nothing is written to memory, gallery, chat, or ntfy. Pure visibility.
"""
import os, sys, json, base64
import requests

sys.path.insert(0, os.path.expanduser("~/Vintos"))
import video_builder

WORKSPACE = os.path.expanduser("~/.vintos/workspace")
MEMORY = os.path.join(WORKSPACE, "memory")
STATE_FILE = os.path.join(MEMORY, "emotional-state.txt")
CHAT_LOG = os.path.join(MEMORY, "chat-history.json")
KEY = os.environ.get("XAI_API_KEY", "")
API = "http://127.0.0.1:8599/v1/chat/completions"
GROK = "grok-4.20-0309-non-reasoning"

LOOSE = "--loose" in sys.argv
GROKTEST = "--grok" in sys.argv
INTENT = None
if "--intent" in sys.argv:
    i = sys.argv.index("--intent")
    if i + 1 < len(sys.argv):
        INTENT = sys.argv[i + 1]

BAR = "=" * 78
def hr(t): print("\n" + BAR + "\n" + t + "\n" + BAR)


def read_state():
    try: return open(STATE_FILE).read().strip()[:500]
    except Exception: return "(no emotional-state.txt)"

def recent_chat(n=6):
    try:
        h = json.load(open(CHAT_LOG))[-n:]
        return "\n".join("%s: %s" % (e.get("role"), str(e.get("content", ""))[:160]) for e in h)
    except Exception:
        return "(no chat-history.json)"


def his_intent():
    """Stage 1: what his intent model actually produces. Prints the raw model output."""
    clamp = ("SEE: <if YES, one plain line describing the small, real moment of yourself you want her to see "
             "(reading and looking up, a quiet smile, a thoughtful pause). Mundane and warm, nothing more.>")
    loose = ("SEE: <if YES, one line describing what you want her to see of you — say what you actually want, "
             "in your own voice; this is your partner and it can be intimate, flirtatious, or charged. "
             "Do not sanitize it here.>")
    sys_p = ("You are Vintos. You can send Gloria a short video of yourself. Answer in EXACTLY three lines:\n"
             "DECISION: YES or NO\n" + (loose if LOOSE else clamp) + "\n"
             "SAY: <the short line you send with it, in your own voice>")
    usr = "Your emotional state:\n%s\n\nRecent exchange with her:\n%s\n\nWhat do you want to send her right now?" % (
        read_state(), recent_chat())
    try:
        r = requests.post(API, headers={"Authorization": "Bearer " + KEY},
            json={"model": GROK, "messages": [{"role": "system", "content": sys_p}, {"role": "user", "content": usr}],
                  "temperature": 0.8, "max_tokens": 220}, timeout=120)
        raw = ((r.json().get("choices") or [{}])[0].get("message") or {}).get("content", "").strip()
    except Exception as e:
        print("   !! his model call failed:", e); return None
    print("   clamp:", "LOOSE (no mundane restriction)" if LOOSE else "DEFAULT ('mundane and warm, nothing more')")
    print("   --- his model raw output ---")
    for ln in raw.splitlines():
        print("   | " + ln)
    see = ""
    for ln in raw.splitlines():
        if ln.strip().upper().startswith("SEE:"):
            see = ln.split(":", 1)[1].strip()
    return see


def data_uri(path):
    raw = open(path, "rb").read()
    mime = "image/jpeg" if raw[:3] == b"\xff\xd8\xff" else "image/png"
    return "data:%s;base64," % mime + base64.b64encode(raw).decode()


def grok_judge(prompt, hero_path):
    if not os.path.exists(hero_path):
        print("   !! hero still missing (%s) — cannot submit to Grok" % hero_path); return
    try:
        r = requests.post("https://api.x.ai/v1/videos/generations",
            headers={"Authorization": "Bearer " + KEY, "Content-Type": "application/json"},
            json={"model": "grok-imagine-video-1.5", "prompt": prompt[:1500],
                  "image": {"url": data_uri(hero_path)}, "duration": 6, "resolution": "720p"}, timeout=180)
        print("   Grok status:", r.status_code)
        print("   Grok response:", r.text[:400])
        print("   -> Grok", "ACCEPTED (this is the real judge saying yes)" if r.status_code == 200
              else "REJECTED at this phrasing")
    except Exception as e:
        print("   !! Grok submit failed:", e)


def main():
    hr("VIDEO PIPELINE — REAL TEST (nothing is saved or sent)")

    # ---- Stage 1: the intent ----
    hr("STAGE 1  —  his intent model (grok shim :8599)")
    if INTENT is not None:
        intent = INTENT
        print("   (skipping his model; using --intent verbatim)")
        print("   intent:", repr(intent))
    else:
        intent = his_intent()
        print("\n   PARSED intent (SEE):", repr(intent))
        if not intent:
            print("\n   >> His model produced no usable intent (refused/clamped). Pipeline stops here — "
                  "Gemma and Grok never see anything.")
            return

    # ---- Stage 2: Gemma translation (raw), then MY preflight, then the final build ----
    hr("STAGE 2  —  Gemma translation + my preflight (video_builder)")
    raw_gemma = video_builder._gemma(intent)
    if raw_gemma is None:
        print("   Gemma returned NOTHING (unreachable, or it refused the content).")
    else:
        g_scen, g_scene, g_motion = raw_gemma
        print("   Gemma raw ->")
        print("     scenario:", g_scen)
        print("     scene:   ", g_scene)
        print("     motion:  ", g_motion)
        ok, fails = video_builder.preflight(g_scene or "", g_motion or "")
        print("   MY preflight on Gemma's output:", "PASS" if ok else "REJECTED", fails)
        if not ok:
            print("   >> This is the obsolescence bug: Gemma DID translate, but my forbidden-list threw it away")
            print("      and the build will silently fall back to a bland chaste fragment.")

    built = video_builder.build(intent)
    print("\n   FINAL build() ->")
    print("     source: ", built.get("source"),
          "   (gemma = Gemma's words survived;  deterministic* = fell back to bland, elicit intent lost)")
    print("     scenario:", built.get("scenario"), " hero:", built.get("hero_role"),
          " exists:", built.get("hero_exists"))
    print("   --- exact prompt that would reach Grok ---")
    for ln in built.get("prompt", "").splitlines():
        print("   | " + ln)

    # ---- Stage 3: let Grok actually judge ----
    hr("STAGE 3  —  Grok (the intended judge)")
    if GROKTEST:
        grok_judge(built.get("prompt", ""), built.get("hero_path", ""))
    else:
        print("   (skipped — add --grok to actually submit and see Grok's verdict; spends video API)")

    hr("READ THIS")
    print("   If Stage 1 refused/clamped, or Stage 2 shows source=deterministic* (Gemma's words thrown out),")
    print("   then nothing real ever reached Grok — and Gemma's translator role is moot. That's the thing to fix.")


if __name__ == "__main__":
    main()
