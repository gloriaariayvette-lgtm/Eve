#!/usr/bin/env python3
"""positive_thread_tag_patch.py — tag somatic/pride threads dream_only at write time.

Somatic sessions and pride mirrors are POSITIVE experiences — resolution, not unresolved tension.
Their threads belong to dreams, not to mirrors/therapy. This flags them `dream_only` in seed_thread
so the tension-consumers can skip them while dreams still consume them. (The consumer-side skip is a
separate patch; the skip also matches by source so pre-existing untagged threads are covered too.)

Self-locating, idempotent, backs up emoclaw_utils.py.
"""
import io, os, time, shutil

F = os.path.expanduser("~/Vintos/emoclaw_utils.py")
s = io.open(F, encoding="utf-8").read()

if '"dream_only":' in s:
    print("already patched — skipping"); raise SystemExit(0)

anchor = ('        "timestamp": datetime.now().isoformat(),\n'
          '        "consumed": False\n'
          '    })')
if anchor not in s:
    print("MISS: seed_thread append block not found"); raise SystemExit(1)

repl = ('        "timestamp": datetime.now().isoformat(),\n'
        '        "consumed": False,\n'
        '        "dream_only": source in ("somatic", "pride", "pride-mirror", "pride_mirror")\n'
        '    })')
s = s.replace(anchor, repl, 1)

shutil.copy(F, F + ".bak-dreamonly-" + time.strftime("%Y%m%d-%H%M%S"))
io.open(F, "w", encoding="utf-8").write(s)
print('PATCHED — seed_thread tags somatic/pride threads "dream_only": True')
