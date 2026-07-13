#!/usr/bin/env python3
"""trajectory_dense_patch.py — load_emotional_trajectory prefers the dense trajectory once it exists.

emotion_densifier writes emotion-trajectory-dense.json. This patches load_emotional_trajectory (in
BOTH causality engines — the importable underscore one and the hyphen cron one) to read that dense
file when it has real depth (>=12 points), falling back to the original emotional-state.json
trajectory otherwise. So cause / drift / (future) LAM all sharpen automatically as the densifier
accumulates, with zero change to the daemon. Self-locating, idempotent, backs up each file.
"""
import io, os, time, shutil

TARGETS = [os.path.expanduser("~/.vintos/workspace/scripts/causality_engine.py"),
           os.path.expanduser("~/Vintos/causality-engine.py")]

ANCHOR = ('def load_emotional_trajectory():\n'
          '    """Load emotion trajectory from .json to find spikes."""\n'
          '    path = os.path.join(MEMORY, "emotional-state.json")\n'
          '    try:\n'
          '        with open(path) as f:\n'
          '            data = json.load(f)\n'
          '        return data.get("trajectory", [])\n'
          '    except:\n'
          '        return []')

REPL = ('def load_emotional_trajectory():\n'
        '    """Load emotion trajectory — prefer the dense snapshot series once it has depth."""\n'
        '    _dense = os.path.join(MEMORY, "emotion-trajectory-dense.json")\n'
        '    try:\n'
        '        _d = json.load(open(_dense))\n'
        '        if isinstance(_d, list) and len(_d) >= 12:\n'
        '            return _d\n'
        '    except Exception:\n'
        '        pass\n'
        '    path = os.path.join(MEMORY, "emotional-state.json")\n'
        '    try:\n'
        '        with open(path) as f:\n'
        '            data = json.load(f)\n'
        '        return data.get("trajectory", [])\n'
        '    except:\n'
        '        return []')

def main():
    done = 0
    for F in TARGETS:
        try:
            s = io.open(F, encoding="utf-8").read()
        except Exception as e:
            print(f"skip {F}: {e}"); continue
        if "emotion-trajectory-dense.json" in s:
            print(f"already patched — {F}"); continue
        if ANCHOR not in s:
            print(f"MISS: load_emotional_trajectory body not found in {F}"); continue
        s = s.replace(ANCHOR, REPL, 1)
        shutil.copy(F, F + ".bak-densetraj-" + time.strftime("%Y%m%d-%H%M%S"))
        io.open(F, "w", encoding="utf-8").write(s)
        print(f"PATCHED {F}"); done += 1
    print(f"done — {done} engine(s) now prefer the dense trajectory")

if __name__ == "__main__":
    main()
