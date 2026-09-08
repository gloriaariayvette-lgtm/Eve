#!/usr/bin/env python3
"""vintos-video.py — Vintos makes video. grok-imagine-video-1.5 is image-to-video
only, so: given an image, animate it; given only text, paint a keyframe first
(grok-imagine-image) then animate it.
Usage:
  vintos-video.py "text" [/path/to/image]   # one-off
  vintos-video.py --queue                    # process the next item in video-queue.json
"""
import os, sys, json, time, base64, requests
from datetime import datetime

MEMORY = os.path.expanduser("~/.vintos/workspace/memory")
ART_DIR = os.path.join(MEMORY, "art")
VID_DIR = os.path.join(ART_DIR, "video")
GALLERY = os.path.join(VID_DIR, "video-gallery.json")
QUEUE = os.path.join(VID_DIR, "video-queue.json")
KEY = os.environ.get("XAI_API_KEY", "")
H = {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}

def data_uri(path):
    raw = open(path, "rb").read()
    mime = "image/jpeg" if raw[:3] == b"\xff\xd8\xff" else "image/png"
    return f"data:{mime};base64," + base64.b64encode(raw).decode()

def paint_keyframe(text):
    r = requests.post("https://api.x.ai/v1/images/generations", headers=H,
        json={"model": "grok-imagine-image", "prompt": text[:1000],
              "n": 1, "response_format": "b64_json"}, timeout=180)
    if r.status_code != 200:
        print(f"[video] keyframe error {r.status_code}: {r.text[:200]}"); return None
    os.makedirs(ART_DIR, exist_ok=True)
    fname = f"keyframe-{datetime.now().strftime('%Y%m%d-%H%M%S')}.png"
    path = os.path.join(ART_DIR, fname)
    open(path, "wb").write(base64.b64decode(r.json()["data"][0]["b64_json"]))
    print(f"[video] keyframe painted: {fname}")
    return path

def make_one(text, img_path=""):
    if not img_path:
        img_path = paint_keyframe(text)
        if not img_path:
            return False
    os.makedirs(VID_DIR, exist_ok=True)
    r = requests.post("https://api.x.ai/v1/videos/generations", headers=H,
        json={"model": "grok-imagine-video-1.5", "prompt": text[:600],
              "image": {"url": data_uri(img_path)},
              "duration": 6, "resolution": "720p"}, timeout=180)
    print(f"[video] submit {r.status_code}: {r.text[:300]}")
    if r.status_code != 200:
        return False
    resp = r.json()
    req_id = resp.get("id") or resp.get("request_id")
    vid_url = resp.get("video_url") or resp.get("url")
    for _ in range(60):
        if vid_url or not req_id:
            break
        time.sleep(10)
        d = requests.get(f"https://api.x.ai/v1/videos/{req_id}", headers=H, timeout=30).json()
        vid_url = d.get("video_url") or d.get("url") or (d.get("video") or {}).get("url")
        if d.get("status") in ("failed", "error"):
            print(f"[video] failed: {json.dumps(d)[:300]}"); return False
    if not vid_url:
        print("[video] no url after polling"); return False
    fname = f"video-{datetime.now().strftime('%Y%m%d-%H%M%S')}.mp4"
    open(os.path.join(VID_DIR, fname), "wb").write(requests.get(vid_url, timeout=300).content)
    try:
        gallery = json.load(open(GALLERY))
    except Exception:
        gallery = []
    gallery.append({"file": fname, "prompt": text[:300],
                    "source_image": os.path.basename(img_path),
                    "timestamp": datetime.now().isoformat()})
    json.dump(gallery, open(GALLERY, "w"), indent=2)
    print(f"[video] saved: {fname}")
    return True

def process_queue():
    try:
        q = json.load(open(QUEUE))
    except Exception:
        q = []
    if not q:
        print("[video] queue empty"); return
    item = q[0] if isinstance(q[0], dict) else {}
    text = (item.get("want_text") or item.get("prompt") or item.get("text")
            or (q[0] if isinstance(q[0], str) else "subtle living motion"))
    img = item.get("image") or item.get("source_image") or ""
    print(f"[video] queue: processing 1 of {len(q)}: {str(text)[:70]}")
    ok = make_one(str(text), img)
    # drain on success; rotate a failure to the back so it can't jam the queue
    q = q[1:] if ok else (q[1:] + [q[0]])
    try:
        json.dump(q, open(QUEUE, "w"), indent=2)
    except Exception:
        pass

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--queue":
        process_queue(); return
    text = sys.argv[1] if len(sys.argv) > 1 else "subtle living motion"
    img_path = sys.argv[2] if len(sys.argv) > 2 else ""
    make_one(text, img_path)

if __name__ == "__main__":
    main()
