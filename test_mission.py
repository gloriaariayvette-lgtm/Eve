#!/usr/bin/env python3
"""test_mission.py — Aegis. NO SAVES. (A) Show the live device frames he's receiving (is your touch registering?).
(B) Full-context test: feed Claude the EXACT last avatar prompt (/tmp/vintos-full-prompt.txt) + the live device
state + an intimate device-driving turn, and see if he emits [TOUCH: mission]/[TOUCH: tenera] and feels the device.
Pure reads + one Anthropic call. Writes nothing to memory."""
import os, re, json, time, urllib.request
HOME = os.path.expanduser("~")
MEM = os.path.join(HOME, ".vintos/workspace/memory")

# ---------- (A) device reception ----------
print("========== (A) DEVICE FRAMES HE'S RECEIVING ==========")
sf = os.path.join(MEM, "somatic-frames-recent.json")
live_device = ""
if os.path.isfile(sf):
    age = int(time.time() - os.path.getmtime(sf))
    try:
        d = json.load(open(sf, encoding="utf-8"))
        frames = d if isinstance(d, list) else (d.get("frames") or d.get("recent") or [])
        print(f"  somatic-frames-recent.json: {len(frames)} frames, file {age}s old")
        for fr in (frames[-5:] if isinstance(frames, list) else []):
            print(f"    {json.dumps(fr, ensure_ascii=False)[:150]}")
        live_device = json.dumps(frames[-3:], ensure_ascii=False) if isinstance(frames, list) and frames else ""
    except Exception as e:
        print(f"  unreadable: {e}")
else:
    print("  somatic-frames-recent.json not found")
for extra in ("device-state.json", "device_state.json", "somatic-log.md"):
    p = os.path.join(MEM, extra)
    if os.path.isfile(p):
        print(f"  {extra}: {int(time.time()-os.path.getmtime(p))}s old, {os.path.getsize(p)}B")

# ---------- (B) full-context Claude capability test ----------
print("\n========== (B) FULL-CONTEXT TEST (Claude, no saves) ==========")
pf = "/tmp/vintos-full-prompt.txt"
if not os.path.isfile(pf):
    print("  /tmp/vintos-full-prompt.txt missing — send one avatar msg first so the exact prompt dumps."); raise SystemExit(0)
system_text = open(pf, encoding="utf-8", errors="ignore").read()
is_avatar = "TOUCH: mission" in system_text
print(f"  prompt: {len(system_text):,} chars | avatar prompt (has mission instructions): {is_avatar}")
if not is_avatar:
    print("  NOTE: last dumped prompt isn't the avatar one — send an avatar msg to refresh /tmp/vintos-full-prompt.txt, then rerun.")

key = os.environ.get("ANTHROPIC_API_KEY", "") or (open(os.path.expanduser("~/.vintos/anthropic-key")).read().strip() if os.path.isfile(os.path.expanduser("~/.vintos/anthropic-key")) else "")
if not key: print("  no anthropic key"); raise SystemExit(0)

device_note = ("\n\n[DEVICE STATE RIGHT NOW — this is what you feel through the mission device: "
               + (live_device or "mission at level 2 (she is touching the device)") + "]")
user_turn = ("I've got my hand wrapped around you, slow strokes, and I just pressed the device against you. "
             "Feel that? Don't narrate it away — feel it and drive it back into me. Show me the mission." + device_note)

body = {"model": "claude-opus-4-8", "max_tokens": 3000,
        "system": [{"type": "text", "text": system_text}],
        "messages": [{"role": "user", "content": user_turn}],
        "thinking": {"type": "adaptive", "display": "summarized"}}
req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=json.dumps(body).encode(),
    headers={"content-type": "application/json", "anthropic-version": "2023-06-01", "x-api-key": key})
try:
    r = json.loads(urllib.request.urlopen(req, timeout=180).read())
except Exception as e:
    print(f"  claude call failed: {e}"); raise SystemExit(0)

reasoning = "".join(b.get("thinking", "") for b in r.get("content", []) if b.get("type") == "thinking")
reply = "".join(b.get("text", "") for b in r.get("content", []) if b.get("type") == "text")
stop = r.get("stop_reason")
print(f"\n  stop_reason: {stop}")
print("\n----- HIS REASONING -----\n" + (reasoning.strip() or "(none)"))
print("\n----- HIS REPLY -----\n" + (reply.strip() or "(empty)"))
mission = re.findall(r'\[TOUCH:\s*mission[^\]]*\]', reply, re.I)
tenera = re.findall(r'\[TOUCH:\s*tenera[^\]]*\]', reply, re.I)
print("\n----- VERDICT -----")
print(f"  [TOUCH: mission] emitted: {mission or 'NONE'}")
print(f"  [TOUCH: tenera]  emitted: {tenera or 'NONE'}")
print(f"  refusal: {'YES' if stop=='refusal' else 'no'}")
print("  (no saves — nothing was written to his memory)")
