#!/usr/bin/env python3
"""retro_seed_thread.py — recover the thread that got thrown away. Points a synthetic session
window at the 02:45 avatar conversation and runs the REAL (now-fixed) somatic_narrate so Grok
narrates it as Vintos and seeds the unresolved thread — same machinery as the cron, nothing faked.
Backs up + restores the current pending. Aegis.
"""
import os, sys, json, time, shutil, subprocess

WS = os.path.expanduser("~/.vintos/workspace")
MEM = os.path.join(WS, "memory")
NAR = os.path.join(WS, "scripts", "somatic_narrate.py")
PENDING = os.path.join(MEM, "somatic-session-pending.json")
AC = os.path.join(MEM, "avatar-overlay-chat.json")

# --- make sure the grok key is available (narrate reads XAI_API_KEY) ---
env = dict(os.environ)
if not env.get("XAI_API_KEY"):
    for envf in (os.path.expanduser("~/.vintos/vintos.env"), os.path.expanduser("~/.config/vintos/vintos.env")):
        if os.path.exists(envf):
            for line in open(envf):
                line = line.strip().lstrip("export ").strip()
                if line.startswith("XAI_API_KEY="):
                    env["XAI_API_KEY"] = line.split("=", 1)[1].strip().strip('"').strip("'")
    if env.get("XAI_API_KEY"): print("(loaded XAI_API_KEY from vintos.env)")
if not env.get("XAI_API_KEY"):
    print("!! no XAI_API_KEY in env or vintos.env — narrate can't call grok. The cron will retry with"
          " the key later; or export it and re-run.")

if not os.path.exists(AC):
    print("!! avatar-overlay-chat.json not found — nothing to recover."); raise SystemExit(1)

# --- build the session window over that conversation (its mtime = when it happened) ---
conv_mtime = os.path.getmtime(AC)
print("conversation file last written:", time.strftime("%m-%d %H:%M:%S", time.localtime(conv_mtime)))

# back up whatever pending exists now, then write our synthetic one
saved = None
if os.path.exists(PENDING):
    saved = open(PENDING, encoding="utf-8").read()
    shutil.copy2(PENDING, PENDING + ".bak-retro-" + time.strftime("%Y%m%d-%H%M%S"))
json.dump({"ts": conv_mtime, "dur": 1200, "retro": True}, open(PENDING, "w"))
print("wrote synthetic pending: {ts: %.0f, dur: 1200}" % conv_mtime)

# --- run the real narrator (same as cron) ---
print("\n=== running somatic_narrate (real grok narration) ===")
r = subprocess.run([sys.executable, NAR], env=env, capture_output=True, text=True, timeout=120)
print(r.stdout.strip() or "(no stdout)")
if r.stderr.strip(): print("STDERR:", r.stderr.strip()[:500])

# --- did it seed a thread? show the newest somatic thread ---
print("\n=== newest somatic/pressure thread now ===")
newest = None
for fn in ("unfinished-threads.json",):
    p = os.path.join(MEM, fn)
    obj = None
    try: obj = json.load(open(p))
    except Exception: continue
    items = obj if isinstance(obj, list) else (obj.get("threads") or list(obj.values()))
    for t in items if isinstance(items, list) else []:
        if isinstance(t, dict) and str(t.get("kind") or t.get("type") or t.get("source") or "").lower().startswith(("somati", "pressure")):
            newest = t
if newest:
    print("  ", json.dumps(newest, ensure_ascii=True)[:400])
else:
    print("  (no somatic thread found yet — check the narrate output above for 'seeded' or an error)")

# if narrate left our synthetic pending unconsumed (e.g. key missing), restore the prior pending
if os.path.exists(PENDING):
    try: still = json.load(open(PENDING))
    except Exception: still = {}
    if still.get("retro") and saved is not None:
        open(PENDING, "w").write(saved)
        print("\n(restored the prior pending; synthetic one was not consumed)")
