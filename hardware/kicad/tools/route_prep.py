#!/usr/bin/env python3
"""
Prep the integrated double-sided board for Freerouting:
  1. Force the Default netclass to the CNC rule: track 1.0, clearance 1.0,
     via 2.4 / drill 1.0 mm  (the .kicad_pro had track 0.9 < min_track_width 1.0).
  2. Pour GND on BOTH copper layers (board edge inset 0.5 mm) so the 83 GND pads
     tie to the plane -- Freerouting then leaves GND alone and only routes signals.
GND_MCU (6 pads) stays a routed net; R_STAR is the single GND<->GND_MCU tie.
Run with KiCad 10 python, KiCad CLOSED.
"""
import pcbnew
from pcbnew import FromMM

PCB = r"C:\Users\Mads2\DTU\4. Semester\Electrical Energy Systems\team\hardware\kicad\system\system.kicad_pcb"
TRACK, CLR, VIA_D, VIA_DR = 1.0, 1.0, 2.4, 1.0
EDGE_INSET = 0.5   # min_copper_edge_clearance

board = pcbnew.LoadBoard(PCB)

# --- 1. netclass ---
ncs = board.GetAllNetClasses()
for name in ncs:
    nc = ncs[name]
    nc.SetTrackWidth(FromMM(TRACK))
    nc.SetClearance(FromMM(CLR))
    nc.SetViaDiameter(FromMM(VIA_D))
    nc.SetViaDrill(FromMM(VIA_DR))
    print(f"netclass {name}: track {TRACK} clr {CLR} via {VIA_D}/{VIA_DR}")

# --- 2. GND pour both layers ---
gnd_nc = board.GetNetcodeFromNetname("GND")
print("GND netcode:", gnd_nc)
# clear old zones
for z in list(board.Zones()):
    board.Remove(z)
bb = board.GetBoardEdgesBoundingBox()
L, T = bb.GetLeft() + FromMM(EDGE_INSET), bb.GetTop() + FromMM(EDGE_INSET)
R, B = bb.GetRight() - FromMM(EDGE_INSET), bb.GetBottom() - FromMM(EDGE_INSET)
for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
    z = pcbnew.ZONE(board)
    z.SetLayer(layer)
    z.SetNetCode(gnd_nc)
    z.SetLocalClearance(FromMM(CLR))
    z.SetMinThickness(FromMM(0.25))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)   # solid tie -> easy hand-solder
    z.SetFillMode(pcbnew.ZONE_FILL_MODE_POLYGONS)
    z.SetIsFilled(True)
    chain = pcbnew.SHAPE_LINE_CHAIN()
    for px, py in [(L, T), (R, T), (R, B), (L, B)]:
        chain.Append(int(px), int(py))
    chain.SetClosed(True)
    z.Outline().AddOutline(chain)
    board.Add(z)
pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(PCB, board)
print(f"poured GND on F.Cu+B.Cu, edge inset {EDGE_INSET} mm, {len(list(board.Zones()))} zones")
