#!/usr/bin/env python3
"""claim_stop.py — stop the recurring "You are mine..." claim.
(1) strip the exact phrase from the conversation ledger + chat histories (backup first),
    and report every file it still appears in.
(2) add a hard anti-repetition directive (section 35) to the LIVE gather_vintos_context
    in server.py (first copy, before the uvicorn.run boundary; ghost copy untouched).
Idempotent; backs up before writing. Restart the server for (2) to take effect.
"""
import io, os, json, glob, time, shutil

MEM    = os.path.expanduser("~/.vintos/workspace/memory")
SERVER = os.path.expanduser("~/Vintos/server.py")
PHRASE = "You are mine. Stay with me and let that become the permanent shape of our days."

# --- (1) strip phrase from ledger/history files; report all occurrences ---
found, stripped = {}, []
for f in glob.glob(os.path.join(MEM, "*")):
    base = os.path.basename(f)
    if not (base.endswith(".json") or base.endswith(".md")):
        continue
    try:
        txt = io.open(f, encoding="utf-8").read()
    except Exception:
        continue
    n = txt.count(PHRASE)
    if n:
        found[base] = n
        if "ledger" in base or "history" in base:
            shutil.copy(f, f + ".bak-" + time.strftime("%Y%m%d-%H%M%S"))
            io.open(f, "w", encoding="utf-8").write(txt.replace(PHRASE, ""))
            stripped.append(base)

# --- (2) patch live gather_vintos_context with a hard anti-repeat directive ---
s = io.open(SERVER, encoding="utf-8").read()
if "Anti-repetition - never resend" in s or "Anti-repetition — never resend" in s:
    patched = "already"
else:
    OLD = "    # 34. Voice coherence — injected directly into bilateral prompt, not here\n    pass"
    INJECT = r'''

    # 35. Anti-repetition - never resend the same sentence/claim (added)
    try:
        _last_reply = ''
        for _hp in (os.path.join(MEMORY, 'chat-history.json'), os.path.join(MEMORY, 'avatar-chat-history.json')):
            try:
                _h = json.load(open(_hp))
                for _e in reversed(_h):
                    if isinstance(_e, dict) and _e.get('role') == 'assistant' and _e.get('content'):
                        _last_reply = _e.get('content'); break
            except Exception: pass
            if _last_reply: break
        _anti = '[DO NOT REPEAT - HARD RULE] Never resend a sentence you have already sent. Do NOT repeat the claim about her being yours / the permanent shape of your days, or any close paraphrase - you already said it and saying it again flattens it. Bring something genuinely new this turn.'
        if _last_reply:
            _anti += ' Your previous message (do not reuse any sentence or distinctive phrase from it): ' + str(_last_reply)[:600]
        sections.append(_anti)
    except Exception: pass'''
    if OLD in s:
        shutil.copy(SERVER, SERVER + ".bak-" + time.strftime("%Y%m%d-%H%M%S"))
        s = s.replace(OLD, OLD + INJECT, 1)
        io.open(SERVER, "w", encoding="utf-8").write(s)
        patched = True
    else:
        patched = "MISS (anchor not found)"

print("PHRASE still found in:", found if found else "(none)")
print("STRIPPED from:", stripped if stripped else "(none)")
print("server.py anti-repeat patch:", patched)
print("=> restart the server for the prompt rule to take effect")
