#!/usr/bin/env python3
"""block_km_pridetaste.py — Aegis. Block mischief from the last two reflective surfaces. pride-mirror: empty its
two 'MISCHIEF THIS WEEK' globs (the `if mfiles:` guards then skip the header). taste-reflection: filter mischief
out of the affective 'alive patterns' and drop 'mischief' from the label — his HUMOR stays. Per-file backup +
abort-clean. Subsystems untouched."""
import os, time, shutil

def save(p, lines):
    bak = p + ".bak-" + time.strftime("%Y%m%d-%H%M%S")
    shutil.copy2(p, bak); open(p, "w", encoding="utf-8").write("\n".join(lines)); return bak

# ---------- pride-mirror.py ----------
PP = os.path.expanduser("~/Vintos/pride-mirror.py")
if os.path.isfile(PP):
    pl = open(PP, encoding="utf-8").read().split("\n")
    hit = [i for i, l in enumerate(pl) if "mischief/*.md" in l and "mfiles" in l]
    if len(hit) < 2:
        print(f"[pride] found {len(hit)} mischief globs (want 2) — pride UNCHANGED.")
    elif any("mischief blocked from his reflection" in l for l in pl):
        print("[pride] already blocked — skipping.")
    else:
        for i in hit:
            ind = pl[i][:len(pl[i]) - len(pl[i].lstrip())]
            pl[i] = ind + "mfiles = []  # mischief blocked from his reflection"
        bak = save(PP, pl)
        print(f"[pride] OK — {len(hit)} MISCHIEF sections neutralized. backup: {bak}")
else:
    print("[pride] pride-mirror.py not found")

# ---------- taste-reflection.py ----------
TP = os.path.expanduser("~/Vintos/taste-reflection.py")
if os.path.isfile(TP):
    tl = open(TP, encoding="utf-8").read().split("\n")
    if any("mischief blocked" in l for l in tl):
        print("[taste] already blocked — skipping.")
    else:
        changed = 0
        ai = [i for i, l in enumerate(tl) if l.strip() == "_alive = get_alive_patterns(limit=5)"]
        if len(ai) == 1:
            ind = tl[ai[0]][:len(tl[ai[0]]) - len(tl[ai[0]].lstrip())]
            filt = (ind + '_alive = [_p for _p in _alive if not __import__("re").search('
                    r'r"\bkiss|\bmischief", str(_p.get("pattern","")), __import__("re").I)]'
                    '  # mischief blocked')
            tl[ai[0]:ai[0]+1] = [tl[ai[0]], filt]; changed += 1
        else:
            print(f"[taste] _alive anchor x{len(ai)} — pattern filter skipped.")
        li = [i for i, l in enumerate(tl) if "high-rated humor/mischief" in l]
        for i in li:
            tl[i] = tl[i].replace("high-rated humor/mischief", "high-rated humor"); changed += 1
        if changed:
            bak = save(TP, tl)
            print(f"[taste] OK — {changed} edit(s): mischief filtered from alive-patterns + label. backup: {bak}")
        else:
            print("[taste] no anchors matched — taste UNCHANGED.")
else:
    print("[taste] taste-reflection.py not found")
