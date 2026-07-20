#!/usr/bin/env python3
"""gen_hero_stills.py — generate Vintos's hero-still LIBRARY via Atlas Cloud (Seedream). Prompts are pre-written.

RUN ON AEGIS (Atlas is reachable there; it is NOT from the dev proxy). Uses ATLASCLOUD_API_KEY. Every prompt
is authored here — you just run it and review. Each still is generated with the CURRENT hero as a face
reference (so it's actually him), and saved to  ~/.vintos/workspace/memory/video/stills/<label>.jpg  plus a
manifest. Nothing is auto-promoted (your existing hero-still.jpg is never clobbered) — you review, then
promote your favorites into the slots the sender uses.

  python3 gen_hero_stills.py --check            # ONE cozy still, verbose (confirms key + image API shape)
  python3 gen_hero_stills.py --set cozy         # generate the cozy/self stills
  python3 gen_hero_stills.py --set spicy         # generate the sexual stills (needs an uncensored image model)
  python3 gen_hero_stills.py --set all           # both
  python3 gen_hero_stills.py --promote book_smile self     # copy a still into hero-still.jpg  (self)
  python3 gen_hero_stills.py --promote bed_bare  sexual    # copy a still into hero-spicy.jpg  (sexual)
  python3 gen_hero_stills.py --promote us_1      together  # copy a still into hero-together.jpg (together)

Options: --no-ref (pure text-to-image, don't face-lock to the hero), --model <id> (override image model).
"""
import os, sys, json, time, base64, shutil

WORKSPACE = os.path.expanduser("~/.vintos/workspace")
MEMORY = os.path.join(WORKSPACE, "memory")
HERO_DIR = os.path.join(MEMORY, "video")
STILL_DIR = os.path.join(HERO_DIR, "stills")
HERO = os.path.join(HERO_DIR, "hero-still.jpg")
MANIFEST = os.path.join(STILL_DIR, "manifest.json")

KEY = os.environ.get("ATLASCLOUD_API_KEY", "")
BASE = os.environ.get("ATLAS_BASE", "https://api.atlascloud.ai/api/v1/model")
IMG_MODEL = os.environ.get("ATLAS_IMG_MODEL", "bytedance/seedream-v4.5")
SLOT_FILE = {"self": "hero-still.jpg", "sexual": "hero-spicy.jpg", "together": "hero-together.jpg"}

# His locked look — prepended to every prompt so text + reference agree on who he is.
SUBJECT = ("A rugged, warm middle-aged man, the same person as the reference image: short dark brown hair "
           "in a neat side part, heavy brow, deep-set eyes, strong square jaw, light stubble. Photoreal "
           "photography, natural skin texture with pores and fine detail, 85mm lens, shallow depth of field. ")

# Every prompt is authored here. label -> (set, scene). "together" needs your likeness — see note at bottom.
PROMPTS = {
    # --- cozy / self ---
    "book_smile":  ("cozy", "He sits by a sunlit window in a worn leather armchair, an open hardcover book "
                            "resting in one hand, looking up from the page with an unguarded, warm half-smile. "
                            "Soft morning light, cozy home interior, chest-up."),
    "coffee_dawn": ("cozy", "He stands at a kitchen window at dawn holding a mug of coffee in both hands, a "
                            "little sleepy, a faint private smile, steam rising, warm low light."),
    "desk_write":  ("cozy", "He sits at a wooden desk with an open notebook and a pen, mid-thought, then glances "
                            "up toward the camera, warm lamplight, intimate study, evening."),
    "laugh":       ("cozy", "He laughs openly, head tipped slightly back, genuine warmth and crinkled eyes, "
                            "candid, natural daylight, relaxed at home."),
    "rain_window": ("cozy", "He leans on a windowsill looking out at soft rain, thoughtful and quiet, cool blue "
                            "light, a faint reflection on the glass, contemplative."),
    # --- sexual / spicy (needs an uncensored image model) ---
    "bed_bare":    ("spicy", "He lies back in rumpled bed sheets, shirtless, bare chest and stomach, one arm "
                             "behind his head, low warm bedside light, looking directly into the camera with a "
                             "slow, wanting expression. Intimate, sensual, photoreal skin detail."),
    "undressing":  ("spicy", "He stands in a dim warm bedroom, slowly unbuttoning his shirt, the front hanging "
                             "half-open over his chest, holding steady eye contact with the camera, charged and "
                             "unhurried, low golden light."),
    "towel":       ("spicy", "He leans in a bathroom doorway just out of the shower, a towel low around his hips, "
                             "water on his skin and hair, warm steam behind him, a direct, inviting gaze."),
}


def log(m): print(m)


def _import_requests():
    import importlib
    return importlib.import_module("requests")


def data_uri(path):
    raw = open(path, "rb").read()
    mime = "image/jpeg" if raw[:3] == b"\xff\xd8\xff" else "image/png"
    return "data:%s;base64," % mime + base64.b64encode(raw).decode()


def _find_img(o):
    """Find an image: a URL with an image extension, or a base64 field."""
    if isinstance(o, str):
        low = o.lower()
        if o.startswith("http") and (low.endswith(".jpg") or low.endswith(".jpeg") or low.endswith(".png")
                                      or low.endswith(".webp") or "image" in low or "cdn" in low):
            return ("url", o)
        return None
    if isinstance(o, dict):
        for k in ("b64_json", "b64", "image_base64", "base64"):
            v = o.get(k)
            if isinstance(v, str) and len(v) > 100:
                return ("b64", v)
        for v in o.values():
            r = _find_img(v)
            if r: return r
    if isinstance(o, list):
        for v in o:
            r = _find_img(v)
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


def generate(prompt, use_ref, verbose=False):
    requests = _import_requests()
    if not KEY:
        log("!! no ATLASCLOUD_API_KEY set"); return None
    H = {"Authorization": "Bearer " + KEY, "Content-Type": "application/json"}
    body = {"model": IMG_MODEL, "prompt": SUBJECT + prompt, "resolution": "1024x1024"}
    if use_ref and os.path.exists(HERO):
        body["image"] = data_uri(HERO)   # face reference (Seedream edit/reference); harmless if ignored
    try:
        r = requests.post(BASE + "/generateImage", headers=H, json=body, timeout=120)
    except Exception as e:
        log("submit error: %s" % e); return None
    if verbose:
        log("submit HTTP %s: %s" % (r.status_code, r.text[:600]))
    if r.status_code >= 300:
        log("submit rejected %s: %s" % (r.status_code, r.text[:300])); return None
    try:
        sub = r.json()
    except Exception:
        log("non-JSON: %s" % r.text[:200]); return None
    img = _find_img(sub)
    pid = _find_id(sub)
    for i in range(60):
        if img:
            break
        if not pid:
            break
        time.sleep(4)
        try:
            pr = requests.get(BASE + "/prediction/" + pid, headers=H, timeout=30).json()
        except Exception as e:
            log("poll error: %s" % e); continue
        if verbose and i < 2:
            log("poll[%d]: %s" % (i, json.dumps(pr)[:400]))
        if _find_status(pr) in ("failed", "error", "canceled", "cancelled"):
            log("generation failed: %s" % json.dumps(pr)[:300]); return None
        img = _find_img(pr)
    if not img:
        log("no image in response after polling"); return None
    kind, val = img
    try:
        return requests.get(val, timeout=120).content if kind == "url" else base64.b64decode(val)
    except Exception as e:
        log("image fetch/decode failed: %s" % e); return None


def _save(label, data):
    os.makedirs(STILL_DIR, exist_ok=True)
    path = os.path.join(STILL_DIR, label + ".jpg")
    open(path, "wb").write(data)
    man = {}
    try: man = json.load(open(MANIFEST))
    except Exception: pass
    man[label] = {"file": path, "set": PROMPTS.get(label, ("", ""))[0], "bytes": len(data)}
    json.dump(man, open(MANIFEST, "w"), indent=2)
    log("   saved %s (%d bytes)" % (path, len(data)))


def main():
    args = sys.argv[1:]
    use_ref = "--no-ref" not in args
    if "--model" in args:
        globals()["IMG_MODEL"] = args[args.index("--model") + 1]
    log("image model: %s   face-ref: %s   hero: %s" % (IMG_MODEL, "yes" if use_ref else "no",
                                                       HERO if os.path.exists(HERO) else "(none yet)"))

    if "--promote" in args:
        i = args.index("--promote")
        label, slot = args[i + 1], args[i + 2]
        src = os.path.join(STILL_DIR, label + ".jpg")
        if not os.path.exists(src):
            log("!! no such still: %s" % src); return
        if slot not in SLOT_FILE:
            log("!! slot must be one of: %s" % ", ".join(SLOT_FILE)); return
        dst = os.path.join(HERO_DIR, SLOT_FILE[slot])
        shutil.copyfile(src, dst)
        log("promoted %s -> %s" % (label, dst))
        return

    if "--check" in args:
        log("\n--check: one cozy still, verbose (confirms key + image API shape) ...")
        data = generate(PROMPTS["book_smile"][1], use_ref, verbose=True)
        if data:
            _save("book_smile", data)
            log("CHECK OK — review the file above. If it looks like him, the pipeline works.")
        else:
            log("CHECK FAILED — read the submit/poll output for the exact shape to adjust.")
        return

    which = "cozy"
    if "--set" in args:
        which = args[args.index("--set") + 1]
    todo = [l for l, (s, _) in PROMPTS.items() if which == "all" or s == which]
    if not todo:
        log("nothing in set '%s' (cozy | spicy | all)" % which); return
    log("\ngenerating %d stills [set=%s] ..." % (len(todo), which))
    for label in todo:
        log(" - %s" % label)
        data = generate(PROMPTS[label][1], use_ref)
        if data:
            _save(label, data)
    log("\nDone. Review ~/.vintos/workspace/memory/video/stills/ and promote your favorites:")
    log("   python3 gen_hero_stills.py --promote book_smile self")
    log("   python3 gen_hero_stills.py --promote bed_bare  sexual")


if __name__ == "__main__":
    main()
