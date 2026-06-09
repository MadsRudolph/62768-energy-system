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
    # GND-pour paa B.Cu OVENPAA den routede GND: forbinder eventuelle rest-oer
    # og giver lav impedans. Solid pad-forbindelse (ingen starved thermals).
    gnd = None
    for net in board.GetNetsByName():
        name = str(net)
        if name.lstrip("/") == "GND":
            gnd = board.GetNetsByName()[name]
    if gnd:
        bbox = board.GetBoardEdgesBoundingBox()
        zone = pcbnew.ZONE(board)
        zone.SetLayer(pcbnew.B_Cu)
        zone.SetNetCode(gnd.GetNetCode())
        chain = pcbnew.SHAPE_LINE_CHAIN()
        for px, py in [(bbox.GetLeft(), bbox.GetTop()), (bbox.GetRight(), bbox.GetTop()),
                       (bbox.GetRight(), bbox.GetBottom()), (bbox.GetLeft(), bbox.GetBottom())]:
            chain.Append(px, py)
        chain.SetClosed(True)
        zone.Outline().AddOutline(chain)
        zone.SetLocalClearance(pcbnew.FromMM(0.5))
        zone.SetMinThickness(pcbnew.FromMM(0.5))
        zone.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
        board.Add(zone)
        filler = pcbnew.ZONE_FILLER(board)
        filler.Fill(board.Zones())
    pcbnew.SaveBoard(boardf, board)
    print("ses:", ok, "+ GND-pour" if gnd else "")
