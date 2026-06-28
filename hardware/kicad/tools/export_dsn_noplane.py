#!/usr/bin/env python3
"""Export a Specctra DSN with the GND pours removed (in memory only) so Freerouting
routes every net -- including GND -- as tracks. The saved .kicad_pcb keeps its zones;
we re-pour/refill after the SES import. Run with KiCad 10 python.
  python export_dsn_noplane.py <board.kicad_pcb> <out.dsn>"""
import sys, pcbnew
board = pcbnew.LoadBoard(sys.argv[1])
n = 0
for z in list(board.Zones()):
    board.Remove(z); n += 1
ok = pcbnew.ExportSpecctraDSN(board, sys.argv[2])
print(f"removed {n} zones (in memory), DSN export: {ok}")
