#!/usr/bin/env python3
"""
Finish the double-sided system route after Freerouting:
  1. Import the SES (signal tracks + vias).
  2. Refill the GND pours on both layers.
  3. Drop sparse GND stitching vias on a grid where the GND plane is clear of
     pads / non-GND tracks (THT GND leads already stitch the planes at every
     through-hole, so this only fills the big open copper).
  4. Save.
Run with KiCad 10 python, KiCad CLOSED.
  python route_finish.py <board.kicad_pcb> <in.ses> [grid_mm]
"""
import sys, math
import pcbnew
from pcbnew import FromMM, ToMM, VECTOR2I

PCB = sys.argv[1]
SES = sys.argv[2]
GRID = float(sys.argv[3]) if len(sys.argv) > 3 else 25.0
VIA_D, VIA_DR, CLR = 2.4, 1.0, 1.0
KEEP = VIA_D/2 + CLR          # via-centre keepout to other-net copper (mm)

board = pcbnew.LoadBoard(PCB)
gnd = board.GetNetcodeFromNetname("GND")

# --- 1. import SES ---
ok = pcbnew.ImportSpecctraSES(board, SES)
print("SES import:", ok)
trk = [t for t in board.GetTracks() if t.GetClass() == "PCB_TRACK"]
via = [t for t in board.GetTracks() if t.GetClass() == "PCB_VIA"]
print(f"after import: {len(trk)} tracks, {len(via)} vias")

# --- 2. refill GND pours ---
pcbnew.ZONE_FILLER(board).Fill(board.Zones())

# --- 3. sparse GND stitching grid ---
def seg_dist(px, py, x1, y1, x2, y2):
    dx, dy = x2-x1, y2-y1
    L2 = dx*dx + dy*dy
    if L2 == 0:
        return math.hypot(px-x1, py-y1)
    t = max(0, min(1, ((px-x1)*dx + (py-y1)*dy)/L2))
    return math.hypot(px-(x1+t*dx), py-(y1+t*dy))

pads = [(p, p.GetNetCode()) for fp in board.GetFootprints() for p in fp.Pads()]
ntrk = [t for t in board.GetTracks()
        if t.GetClass() == "PCB_TRACK" and t.GetNetCode() != gnd]
bb = board.GetBoardEdgesBoundingBox()
x0, y0 = ToMM(bb.GetLeft()), ToMM(bb.GetTop())
x1, y1 = ToMM(bb.GetRight()), ToMM(bb.GetBottom())
margin = VIA_D/2 + 1.0

def clear(xmm, ymm):
    if not (x0+margin < xmm < x1-margin and y0+margin < ymm < y1-margin):
        return False
    pt = VECTOR2I(FromMM(xmm), FromMM(ymm))
    for p, nc in pads:                       # avoid every pad (even GND)
        bbp = p.GetBoundingBox(); bbp.Inflate(FromMM(KEEP))
        if bbp.Contains(pt):
            return False
    for t in ntrk:                           # avoid non-GND tracks
        s, e = t.GetStart(), t.GetEnd()
        d = seg_dist(FromMM(xmm), FromMM(ymm), s.x, s.y, e.x, e.y)
        if ToMM(d) < KEEP + ToMM(t.GetWidth())/2:
            return False
    return True

added = 0
gx = x0 + GRID/2
while gx < x1:
    gy = y0 + GRID/2
    while gy < y1:
        if clear(gx, gy):
            v = pcbnew.PCB_VIA(board)
            v.SetPosition(VECTOR2I(FromMM(gx), FromMM(gy)))
            v.SetWidth(FromMM(VIA_D))
            v.SetDrill(FromMM(VIA_DR))
            v.SetNetCode(gnd)
            v.SetViaType(pcbnew.VIATYPE_THROUGH)
            board.Add(v)
            added += 1
        gy += GRID
    gx += GRID
print(f"GND stitching vias added: {added} (grid {GRID} mm)")

# refill once more so pours connect to the new stitching vias
pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(PCB, board)

# unconnected report
board.BuildConnectivity()
print("done. saved", PCB)
