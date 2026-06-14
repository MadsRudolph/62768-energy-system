#!/usr/bin/env python3
"""Flyt F.Cu-refdes-tekster der kolliderer med F.Cu-kobber (efter topside-
migreringen). Samme kandidat-soegning som pcb_route.add_refdes_copper, men mod
F.Cu-forhindringer. Ren session (ingen Remove) -> stabil. Refiller zoner til
sidst og gemmer.
Brug: "<KiCad>\\bin\\python.exe" fix_text_collisions.py <board>.kicad_pcb
"""
import sys
import pcbnew
from pcbnew import FromMM, VECTOR2I

board = pcbnew.LoadBoard(sys.argv[1])
bbox_brd = board.GetBoardEdgesBoundingBox()
margin = FromMM(1.2)
CLR = FromMM(0.85)

obstacles = []
for t in board.GetTracks():
    if t.GetClass() == "PCB_TRACK" and t.GetLayer() != pcbnew.F_Cu:
        continue
    s, e = t.GetStart(), t.GetEnd()
    length = max(1, int(((e.x - s.x) ** 2 + (e.y - s.y) ** 2) ** 0.5))
    n = max(1, length // FromMM(1.5))
    r = t.GetWidth() // 2 + CLR
    for i in range(n + 1):
        px = s.x + (e.x - s.x) * i // n
        py = s.y + (e.y - s.y) * i // n
        obstacles.append(pcbnew.BOX2I(VECTOR2I(px - r, py - r), VECTOR2I(2 * r, 2 * r)))
for fp in board.GetFootprints():
    for pad in fp.Pads():
        bb = pad.GetBoundingBox()
        bb.Inflate(CLR)
        obstacles.append(bb)

texts = [d for d in board.GetDrawings()
         if d.GetClass() == "PCB_TEXT" and d.GetLayer() == pcbnew.F_Cu]

def free(bb, ignore):
    if bb.GetLeft() < bbox_brd.GetLeft() + margin: return False
    if bb.GetRight() > bbox_brd.GetRight() - margin: return False
    if bb.GetTop() < bbox_brd.GetTop() + margin: return False
    if bb.GetBottom() > bbox_brd.GetBottom() - margin: return False
    if any(bb.Intersects(o) for o in obstacles): return False
    for other in texts:
        if other is ignore: continue
        ob = other.GetBoundingBox(); ob.Inflate(CLR)
        if bb.Intersects(ob): return False
    return True

moved = 0
for txt in texts:
    tb = txt.GetBoundingBox(); tb.Inflate(FromMM(0.2))
    if free(tb, txt):
        continue                                   # staar allerede frit
    cx, cy = txt.GetPosition().x, txt.GetPosition().y
    found = False
    for ring in range(1, 9):                       # spiral ud i 1.5 mm-trin
        d = FromMM(1.5) * ring
        for dx, dy in [(0,-d),(0,d),(-d,0),(d,0),(-d,-d),(d,-d),(-d,d),(d,d)]:
            txt.SetPosition(VECTOR2I(cx + dx, cy + dy))
            tb = txt.GetBoundingBox(); tb.Inflate(FromMM(0.2))
            if free(tb, txt):
                found = True
                break
        if found: break
    if found:
        moved += 1
        print(f"  flyttede '{txt.GetText()}'")
    else:
        board.Remove(txt)  # sidste udvej: hellere intet navn end en kortslutning
        texts.remove(txt)
        print(f"  '{txt.GetText()}': ingen fri plads - FJERNET")
        moved += 1

if moved:
    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())
    pcbnew.SaveBoard(sys.argv[1], board)
print(f"fix_text_collisions: {moved} aendringer i {sys.argv[1]}")
