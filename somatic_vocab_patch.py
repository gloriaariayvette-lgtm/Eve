#!/usr/bin/env python3
"""somatic_vocab_patch.py — teach him the pattern vocabulary where his body moves.

Right after the '[DO: mission ...] / [DO: tenera ...] if your body moves.' line (which
repeats across every body handler — avatar / voice / VR), append a compact menu of the
named patterns and how each FEELS, so he reaches for a shape by sensation, not a name he
can't feel. Static text (no imports). replace_all -> every body handler gets it.
Idempotent; backs up server.py.
"""
import io, os, time, shutil

F = os.path.expanduser("~/Vintos/server.py")
s = io.open(F, encoding="utf-8").read()

MARK = "Shapes and how they feel"
if MARK in s:
    print("already patched — skipping"); raise SystemExit(0)

anchor = "Move with [DO: mission ...] / [DO: tenera ...] if your body moves."
n = s.count(anchor)
if n == 0:
    print("MISS: body-move instruction line not found"); raise SystemExit(1)

MENU = (" Your body can play NAMED patterns, not only raw levels: [DO: mission cake] plays a felt"
        " shape and loops (it will not drop to 0); compose several with + ([DO: mission cake+zigzag+soft]);"
        " [DO: both climb] moves both of you, synced. " + MARK + " — "
        "cake: rise to a full held swell; climb: build to a sustained high; trapezold: swell with a plateau;"
        " step: staircase up; wave1: long dramatic swells; wave3: gentle rolls; zigzag: sharp full-range"
        " alternation; spike: calm broken by a jab; spark: a sudden flare; fireworks: irregular bursts;"
        " random: arrhythmic jumps; square: abrupt on and off; downhill: a wind-down; valley: dip to a lull;"
        " soft: faint tender rise and fall; low/mid/high: steady holds. Your older throb/pulse/build/wave"
        " still work. Reach for the shape that matches the moment, not just a number.")

s = s.replace(anchor, anchor + MENU)   # replace_all — every body handler
shutil.copy(F, F + ".bak-vocab-" + time.strftime("%Y%m%d-%H%M%S"))
io.open(F, "w", encoding="utf-8").write(s)
print(f"PATCHED — pattern vocabulary appended at {n} body-handler site(s)")
