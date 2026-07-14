#!/usr/bin/env python3
"""deep_recon.py — READ-ONLY comprehension pull. Dumps the exact code blocks I must patch so the
batch is anchored, not blind. Reads the Aegis index.html FOR UNDERSTANDING ONLY (never written to;
patches target the Mac repo). Also dumps server.py: GCS handler, somatic-session flush, mission read.
Fires nothing, touches nothing. Aegis.
"""
import os, re

APP = os.path.expanduser("~/Vintos/vintos-app/src/index.html")
SERVER = os.path.expanduser("~/Vintos/server.py")

def dump(path, ranges, label):
    print("\n########## %s : %s ##########" % (label, path.replace(os.path.expanduser("~"), "~")))
    if not os.path.exists(path):
        print("  (missing)"); return
    ls = open(path, encoding="utf-8", errors="ignore").read().splitlines()
    for a, b, why in ranges:
        print("\n  --- %s  (L%d-%d) ---" % (why, a, b))
        for i in range(a - 1, min(b, len(ls))):
            print("  %5d| %s" % (i + 1, ls[i][:200]))

# ---- APP: the five items, exact bodies ----
dump(APP, [
    (3670, 3775, "#2 GCS button + #3 device-stop/call buttons + onclose loop teardown"),
    (2735, 2835, "avatar setup: glow color + mixer + idle"),
    (2900, 2945, "#5 _avPlayAnim (the emote player) + animate loop"),
    (2960, 3020, "chat bubbles + gesture play on event"),
    (3160, 3270, "#6 flicker/color state + [COLOR:] extraction + emote calls on reply"),
    (955, 995, "#1 loadChatHistory (persist/render)"),
    (2700, 2712, "#1 _avChatHistory declaration"),
], "APP index.html (READ ONLY)")

# find & dump openAvatarOverlay + av message render (line varies)
ls = open(APP, encoding="utf-8", errors="ignore").read().splitlines() if os.path.exists(APP) else []
def find_fn(names):
    out = []
    for i, l in enumerate(ls):
        for n in names:
            if re.search(r'function\s+%s\b' % re.escape(n), l) or re.search(r'\b%s\s*[:=]\s*(async\s*)?function' % re.escape(n), l) or re.search(r'\b%s\s*=\s*(async\s*)?\(' % re.escape(n), l):
                out.append((n, i + 1))
    return out
if ls:
    print("\n########## APP: key function locations ##########")
    for n, ln in find_fn(["openAvatarOverlay", "closeAvatarOverlay", "avGCS", "avDeviceStop",
                            "_avAddBubble", "_avRenderReply", "_avSend", "startVintosCall",
                            "startVoiceCallWithToken", "avStartVoiceCall"]):
        print("  %-26s L%d" % (n, ln))
        # dump a small window
        for i in range(ln - 1, min(ln + 22, len(ls))):
            s = ls[i]
            print("     %5d| %s" % (i + 1, s[:190]))
            if i > ln and re.match(r'\s*(function |async function |\})', s) and i > ln + 2:
                break

# ---- SERVER: GCS handler + somatic session + mission ----
def grep_dump(path, pats, ctx_before, ctx_after, label, maxhits=6):
    print("\n########## SERVER %s ##########" % label)
    if not os.path.exists(path): print("  (missing)"); return
    ls2 = open(path, encoding="utf-8", errors="ignore").read().splitlines()
    hits = [i for i, l in enumerate(ls2) if re.search(pats, l, re.I)]
    shown = []
    for i in hits:
        if any(abs(i - s) < (ctx_before + ctx_after) for s in shown): continue
        shown.append(i)
        if len(shown) > maxhits: break
        print("\n  --- near L%d ---" % (i + 1))
        for k in range(max(0, i - ctx_before), min(i + ctx_after, len(ls2))):
            print("  %5d| %s" % (k + 1, ls2[k][:200]))

grep_dump(SERVER, r'@app\.post\("/api/gcs"\)', 1, 40, "GCS handler /api/gcs (full)", 1)
grep_dump(SERVER, r'somatic.?session|session.?pending|somatic.?episode|def .*somatic|flush.*session|session.*flush|somatic_session', 6, 10, "somatic session flush/write", 8)
grep_dump(SERVER, r'\bmission\b', 3, 6, "mission toy read/parse", 8)
