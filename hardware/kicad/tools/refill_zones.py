#!/usr/bin/env python3
"""Refill alle zoner paa et board og gem. Koeres i en REN pcbnew-session
(ingen Remove-kald -> ingen SWIG-korruption/krasj i KiCad 9.0.6).
Brug: "C:\\Program Files\\KiCad\\9.0\\bin\\python.exe" tools/refill_zones.py board.kicad_pcb
"""
import sys
import pcbnew

board = pcbnew.LoadBoard(sys.argv[1])
filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
pcbnew.SaveBoard(sys.argv[1], board)
print("refill:", sys.argv[1])
