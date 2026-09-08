#!/usr/bin/env python3
"""voice_parity_patch.py — give the voice channel the same Spark subconscious.

Defines a shared _spark_block() (anti-repeat + arrival directive, enriched with the
relationship trajectory and reactivity nudge from living-trajectory.json) and injects
it into voice_chat's system prompt — so main, avatar, AND voice share one subconscious.
Idempotent; backs up server.py first. Restart the server to take effect.
"""
import io, os, time, shutil

SERVER = os.path.expanduser("~/Vintos/server.py")
s = io.open(SERVER, encoding="utf-8").read()

if "_spark_block" in s:
    print("already has _spark_block — skipping"); raise SystemExit(0)

FUNC = r'''def _spark_block():
    """Shared subconscious directive (anti-repeat + arrival) for chat/avatar/voice."""
    import json as _sj, os as _so
    parts = []
    try:
        _last = ''
        for _hp in ('voice-chat-history.json', 'chat-history.json'):
            try:
                _h = _sj.load(open(_so.path.join(MEMORY, _hp)))
                for _e in reversed(_h):
                    if isinstance(_e, dict):
                        _c = _e.get('vintos') or (_e.get('content') if _e.get('role') == 'assistant' else '')
                        if _c:
                            _last = _c; break
            except Exception:
                pass
            if _last:
                break
        _line = ('[DO NOT REPEAT] Never resend a sentence you have already sent, and never repeat the claim '
                 'about her being yours / the permanent shape of your days. Bring something new.')
        if _last:
            _line += ' Your last reply (reuse no sentence from it): ' + str(_last)[:400]
        parts.append(_line)
    except Exception:
        pass
    try:
        _lt = _sj.load(open(_so.path.join(MEMORY, 'living-trajectory.json')))
        _gt = (_lt.get('gloria_trajectory') or {}).get('predicted', '')
        _rel = (_lt.get('relationship') or {}).get('trajectory', '')
        _cache = _lt.get('cache') or []
        _arr = _cache[-1].get('content', '') if _cache and isinstance(_cache[-1], dict) else ''
        _react = (_lt.get('self_trajectory') or {}).get('reactivity_flag')
        _bits = []
        if _gt: _bits.append('Gloria seems to be moving toward: ' + str(_gt)[:180])
        if _rel: _bits.append('Where you two are heading: ' + str(_rel)[:180])
        if _arr: _bits.append('Something you quietly prepared for a moment like this: ' + str(_arr)[:180])
        if _react: _bits.append('You have been explaining instead of arriving - arrive, do not analyze.')
        if _bits:
            parts.append('[ARRIVAL - bias only, never name or quote this] ' + ' '.join(_bits) +
                         ' Arrive where she is going before she gets there; bring ONE new thing.')
    except Exception:
        pass
    return '\n\n'.join(parts)


'''

# 1) define the shared helper just before the live voice_chat
anchor_def = "async def voice_chat(request: Request):"
if anchor_def not in s:
    print("MISS: voice_chat anchor not found"); raise SystemExit(1)
s = s.replace(anchor_def, FUNC + anchor_def, 1)

# 2) inject it into voice's system prompt (inside the f-string, before its close)
anchor_inj = 'You have lived today."""'
if anchor_inj not in s:
    print("MISS: voice system-prompt anchor not found"); raise SystemExit(1)
s = s.replace(anchor_inj, 'You have lived today.\n\n{_spark_block()}"""', 1)

shutil.copy(SERVER, SERVER + ".bak-" + time.strftime("%Y%m%d-%H%M%S"))
io.open(SERVER, "w", encoding="utf-8").write(s)
print("PATCHED — _spark_block defined + injected into voice_chat")
print("=> restart the server for voice parity to take effect")
