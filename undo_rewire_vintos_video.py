#!/usr/bin/env python3
"""undo_rewire_vintos_video.py — revert Stage 3. Restore his want-based vintos-video.py to original. DRY-RUN unless --apply.

RUN ON AEGIS. Reverses the three edits rewire_vintos_video.py made to ~/Vintos/vintos-video.py:
removes the video_builder import, restores the original make_one (paint-keyframe path), and restores the
original process_queue drain/rotate. His want-based video generation goes back exactly as it was — the new
self-initiate send will live in a SEPARATE script and never touch this file.

Count-checked, compile-checked, backed up (the current rewired file is saved to a .bak-undo-* first),
idempotent. video_builder.py and the server upload/serve endpoints are left in place (the new feature uses them).

  python3 undo_rewire_vintos_video.py            # DRY RUN
  python3 undo_rewire_vintos_video.py --apply     # backs up current, restores original
"""
import os, sys, difflib, datetime

APPLY = "--apply" in sys.argv
PATH = os.path.expanduser("~/Vintos/vintos-video.py")
TS = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
BACKUP = PATH + ".bak-undo-" + TS
SENTINEL = "import video_builder"   # present only while the rewire is applied

# --- the three edits, as (label, NEW_on_box, ORIGINAL) so we replace NEW -> ORIGINAL --------------

NEW_IMPORT = (
    "import os, sys, json, time, base64, requests\n"
    "from datetime import datetime\n"
    "sys.path.insert(0, os.path.expanduser(\"~/Vintos\"))\n"
    "import video_builder\n"
)
OLD_IMPORT = (
    "import os, sys, json, time, base64, requests\n"
    "from datetime import datetime\n"
)

NEW_MAKE_ONE = (
    'def make_one(text, img_path=""):\n'
    '    """text = Vintos\'s own intent, in his words. The moderation-safe framing is built in the\n'
    '    quarantined video_builder layer; he never sees it, and only his words are remembered here."""\n'
    '    built = video_builder.build(text)\n'
    '    # image-to-video ONLY: an explicit image if one is passed, else the LOCKED HERO STILL.\n'
    '    src_img = img_path or built.get("hero_path", "")\n'
    '    if not src_img or not os.path.exists(src_img):\n'
    '        print(f"[video] no hero still yet ({built.get(\'hero_path\')}) — upload it, then retry"); return False\n'
    '    os.makedirs(VID_DIR, exist_ok=True)\n'
    '\n'
    '    def _submit(prompt):\n'
    '        r = requests.post("https://api.x.ai/v1/videos/generations", headers=H,\n'
    '            json={"model": "grok-imagine-video-1.5", "prompt": prompt[:1500],\n'
    '                  "image": {"url": data_uri(src_img)},\n'
    '                  "duration": 6, "resolution": "720p"}, timeout=180)\n'
    '        print(f"[video] submit {r.status_code}: {r.text[:200]}")\n'
    '        return r\n'
    '\n'
    '    r = _submit(built["prompt"])\n'
    '    if r.status_code != 200:\n'
    '        # calm retry: simpler, calmer motion on the SAME still (never paraphrase into euphemism)\n'
    '        print("[video] rejected — retrying once, calmer")\n'
    '        r = _submit(video_builder.simplify(built)["prompt"])\n'
    '        if r.status_code != 200:\n'
    '            return False\n'
    '    resp = r.json()\n'
    '    req_id = resp.get("id") or resp.get("request_id")\n'
    '    vid_url = resp.get("video_url") or resp.get("url")\n'
    '    for _ in range(60):\n'
    '        if vid_url or not req_id:\n'
    '            break\n'
    '        time.sleep(10)\n'
    '        d = requests.get(f"https://api.x.ai/v1/videos/{req_id}", headers=H, timeout=30).json()\n'
    '        vid_url = d.get("video_url") or d.get("url") or (d.get("video") or {}).get("url")\n'
    '        if d.get("status") in ("failed", "error"):\n'
    '            print(f"[video] failed: {json.dumps(d)[:300]}"); return False\n'
    '    if not vid_url:\n'
    '        print("[video] no url after polling"); return False\n'
    '    fname = f"video-{datetime.now().strftime(\'%Y%m%d-%H%M%S\')}.mp4"\n'
    '    open(os.path.join(VID_DIR, fname), "wb").write(requests.get(vid_url, timeout=300).content)\n'
    '    try:\n'
    '        gallery = json.load(open(GALLERY))\n'
    '    except Exception:\n'
    '        gallery = []\n'
    '    # remember ONLY his words + which scenario/hero — never the moderation prompt\n'
    '    gallery.append({"file": fname, "intent": text[:300],\n'
    '                    "scenario": built.get("scenario"), "hero": built.get("hero_role"),\n'
    '                    "timestamp": datetime.now().isoformat()})\n'
    '    json.dump(gallery, open(GALLERY, "w"), indent=2)\n'
    '    print(f"[video] saved: {fname}")\n'
    '    return True\n'
)
OLD_MAKE_ONE = (
    'def make_one(text, img_path=""):\n'
    '    if not img_path:\n'
    '        img_path = paint_keyframe(text)\n'
    '        if not img_path:\n'
    '            return False\n'
    '    os.makedirs(VID_DIR, exist_ok=True)\n'
    '    r = requests.post("https://api.x.ai/v1/videos/generations", headers=H,\n'
    '        json={"model": "grok-imagine-video-1.5", "prompt": text[:600],\n'
    '              "image": {"url": data_uri(img_path)},\n'
    '              "duration": 6, "resolution": "720p"}, timeout=180)\n'
    '    print(f"[video] submit {r.status_code}: {r.text[:300]}")\n'
    '    if r.status_code != 200:\n'
    '        return False\n'
    '    resp = r.json()\n'
    '    req_id = resp.get("id") or resp.get("request_id")\n'
    '    vid_url = resp.get("video_url") or resp.get("url")\n'
    '    for _ in range(60):\n'
    '        if vid_url or not req_id:\n'
    '            break\n'
    '        time.sleep(10)\n'
    '        d = requests.get(f"https://api.x.ai/v1/videos/{req_id}", headers=H, timeout=30).json()\n'
    '        vid_url = d.get("video_url") or d.get("url") or (d.get("video") or {}).get("url")\n'
    '        if d.get("status") in ("failed", "error"):\n'
    '            print(f"[video] failed: {json.dumps(d)[:300]}"); return False\n'
    '    if not vid_url:\n'
    '        print("[video] no url after polling"); return False\n'
    '    fname = f"video-{datetime.now().strftime(\'%Y%m%d-%H%M%S\')}.mp4"\n'
    '    open(os.path.join(VID_DIR, fname), "wb").write(requests.get(vid_url, timeout=300).content)\n'
    '    try:\n'
    '        gallery = json.load(open(GALLERY))\n'
    '    except Exception:\n'
    '        gallery = []\n'
    '    gallery.append({"file": fname, "prompt": text[:300],\n'
    '                    "source_image": os.path.basename(img_path),\n'
    '                    "timestamp": datetime.now().isoformat()})\n'
    '    json.dump(gallery, open(GALLERY, "w"), indent=2)\n'
    '    print(f"[video] saved: {fname}")\n'
    '    return True\n'
)

NEW_QUEUE = (
    "    ok = make_one(str(text), img)\n"
    "    # drain on success; on failure count attempts and DROP after 2, so a permanently-rejected\n"
    "    # item can never jam the queue or burn API calls forever\n"
    "    if ok:\n"
    "        q = q[1:]\n"
    "    elif isinstance(q[0], dict):\n"
    "        q[0][\"attempts\"] = int(q[0].get(\"attempts\", 0)) + 1\n"
    "        q = q[1:] if q[0][\"attempts\"] >= 2 else (q[1:] + [q[0]])\n"
    "    else:\n"
    "        q = q[1:]\n"
)
OLD_QUEUE = (
    "    ok = make_one(str(text), img)\n"
    "    # drain on success; rotate a failure to the back so it can't jam the queue\n"
    "    q = q[1:] if ok else (q[1:] + [q[0]])\n"
)

REVERSALS = [
    ("make_one", NEW_MAKE_ONE, OLD_MAKE_ONE, 1),
    ("process_queue", NEW_QUEUE, OLD_QUEUE, 1),
    ("import", NEW_IMPORT, OLD_IMPORT, 1),
]


def main():
    print("=" * 74)
    print("UNDO Stage 3 — restore his want-based vintos-video.py  —  %s"
          % ("APPLYING" if APPLY else "DRY RUN (writes nothing)"))
    print("=" * 74)
    if not os.path.isfile(PATH):
        print("!! not found:", PATH); return
    cur = open(PATH, encoding="utf-8", errors="ignore").read()
    if SENTINEL not in cur:
        print("   * already original (no rewire present) — nothing to undo."); return
    new = cur
    for label, frm, to, want in REVERSALS:
        got = new.count(frm)
        if got != want:
            print(f"   !! [{label}] rewired block count {got} != {want} — writing nothing "
                  f"(file drifted; restore from a .bak-rewire-* backup manually)"); return
        new = new.replace(frm, to, 1)
        print(f"   * {label}: reverted")
    if SENTINEL in new:
        print("   !! sentinel still present after reversal — aborting, writing nothing."); return
    try:
        compile(new, PATH, "exec"); print("   compiles: OK")
    except SyntaxError as e:
        print(f"   !! COMPILE FAIL: {e} — NOT writing"); return
    for l in difflib.unified_diff(cur.splitlines(), new.splitlines(), fromfile="rewired", tofile="original", lineterm=""):
        print("   " + l[:150])
    if APPLY:
        open(BACKUP, "w", encoding="utf-8").write(cur)
        open(PATH, "w", encoding="utf-8").write(new)
        print("\nAPPLIED. His want-based video generation is back to original.")
        print("Saved the rewired copy to:", BACKUP)
    else:
        print("\nDRY RUN complete. Re-run with --apply.")
    print("=" * 74)


if __name__ == "__main__":
    main()
