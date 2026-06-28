#!/usr/bin/env python3
"""
Narrow THT pads on dense (<=2.54 mm-pitch) parts so a 0.8 mm end mill can isolate
adjacent pins. For each pad on a dense footprint, the dimension facing its nearest
neighbour is clamped to TARGET mm -> inter-pin gap opens from ~0.84/0.94 mm to
~1.14 mm (clears the 1.0 mm clearance rule and leaves the 0.8 mm bit 0.34 mm margin).
The perpendicular (solder-length) dimension and the drill are left untouched.

Operates directly on the .kicad_pcb (pad geometry edit), not the library. A future
"Update PCB from Schematic" with "replace footprints" ticked would undo it -- re-run.

  python narrow_pads.py <board.kicad_pcb> [--apply]   (omit --apply for dry run)
Run with KiCad 10 python, KiCad CLOSED.
"""
import sys, math, itertools
import pcbnew
from pcbnew import ToMM, FromMM, VECTOR2I

PCB = sys.argv[1]
APPLY = "--apply" in sys.argv
TARGET = 1.40          # clamped pad dimension (mm)
DENSE = 3.0            # footprint is "dense" if any pad pair is within this (mm)
GAPWANT = 1.10         # only shrink if current edge gap would be below this

board = pcbnew.LoadBoard(PCB)
changed = 0
fp_touched = []
for fp in board.GetFootprints():
    pads = list(fp.Pads())
    if len(pads) < 2:
        continue
    # dense?
    mind = min(math.hypot(ToMM(a.GetPosition().x-b.GetPosition().x),
                          ToMM(a.GetPosition().y-b.GetPosition().y))
               for a, b in itertools.combinations(pads, 2))
    if mind > DENSE:
        continue
    n_fp = 0
    for p in pads:
        px, py = p.GetPosition().x, p.GetPosition().y
        # nearest neighbour pad
        best = None
        for q in pads:
            if q is p:
                continue
            d = math.hypot(q.GetPosition().x-px, q.GetPosition().y-py)
            if best is None or d < best[0]:
                best = (d, q)
        d, q = best
        if ToMM(d) > DENSE:
            continue
        dx = abs(q.GetPosition().x - px)
        dy = abs(q.GetPosition().y - py)
        sz = p.GetSize()
        sx, sy = ToMM(sz.x), ToMM(sz.y)
        axis = "x" if dx >= dy else "y"          # axis toward the neighbour
        pitch = ToMM(dx if axis == "x" else dy)
        cur = sx if axis == "x" else sy
        if cur <= TARGET:                          # already narrow enough
            continue
        if (pitch - cur) >= GAPWANT:               # gap already fine
            continue
        # circle -> oval when we make it non-square
        if p.GetShape() == pcbnew.PAD_SHAPE_CIRCLE:
            p.SetShape(pcbnew.PAD_SHAPE_OVAL)
        if axis == "x":
            p.SetSize(VECTOR2I(FromMM(TARGET), sz.y))
        else:
            p.SetSize(VECTOR2I(sz.x, FromMM(TARGET)))
        changed += 1
        n_fp += 1
    if n_fp:
        fp_touched.append(f"{fp.GetReference()}({fp.GetFPIDAsString().split(':')[-1]}):{n_fp}")

print(f"pads narrowed: {changed} across {len(fp_touched)} footprints")
for s in fp_touched:
    print("  ", s)
if APPLY:
    pcbnew.SaveBoard(PCB, board)
    print("SAVED", PCB)
else:
    print("(dry run -- pass --apply to save)")
