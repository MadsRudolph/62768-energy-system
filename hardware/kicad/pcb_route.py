#!/usr/bin/env python3
"""DSN-eksport eller SES-import omkring Freerouting.
Brug (KiCads python):
  python pcb_route.py dsn board.kicad_pcb ud.dsn
  python pcb_route.py ses board.kicad_pcb ind.ses     (gemmer boardet bagefter)
"""
import sys
import pcbnew

mode, boardf = sys.argv[1], sys.argv[2]
board = pcbnew.LoadBoard(boardf)
if mode == "dsn":
    ok = pcbnew.ExportSpecctraDSN(board, sys.argv[3])
    print("dsn:", ok)
elif mode == "ses":
    ok = pcbnew.ImportSpecctraSES(board, sys.argv[3])
    # Fiberlaser-zone jf. DTU-PCB-prototyping-guiden: solid B.Cu-zone UDEN net og
    # UDEN pad-forbindelse. Laseren fjerner kun isolations-kanalerne omkring
    # baner/pads i stedet for alt kobberet - hurtigere og mindre slid.
    bbox = board.GetBoardEdgesBoundingBox()
    zone = pcbnew.ZONE(board)
    zone.SetLayer(pcbnew.B_Cu)
    zone.SetNetCode(0)                                   # <no net>
    chain = pcbnew.SHAPE_LINE_CHAIN()
    for px, py in [(bbox.GetLeft(), bbox.GetTop()), (bbox.GetRight(), bbox.GetTop()),
                   (bbox.GetRight(), bbox.GetBottom()), (bbox.GetLeft(), bbox.GetBottom())]:
        chain.Append(px, py)
    chain.SetClosed(True)
    zone.Outline().AddOutline(chain)
    zone.SetLocalClearance(pcbnew.FromMM(0.8))           # guide: 0.75; 0.8 matcher netclass
    zone.SetMinThickness(pcbnew.FromMM(0.25))
    zone.SetPadConnection(pcbnew.ZONE_CONNECTION_NONE)
    zone.SetFillMode(pcbnew.ZONE_FILL_MODE_POLYGONS)     # solid fill
    board.Add(zone)
    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())
    pcbnew.SaveBoard(boardf, board)
    print("ses:", ok, "+ laser-zone (no net)")
