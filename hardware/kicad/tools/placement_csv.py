#!/usr/bin/env python3
"""Round-trip the board placement through a human-editable CSV (the kicad-parts-placer
idea, no dependency). Edit x/y/rotation in a spreadsheet -- equal x => column-aligned,
arithmetic series => even spacing -- then apply it back.

  python placement_csv.py export <board.kicad_pcb> <out.csv>
  python placement_csv.py apply  <board.kicad_pcb> <in.csv>     (KiCad CLOSED)
Columns: ref,value,footprint,x_mm,y_mm,rotation,side
"""
import sys, csv
import pcbnew
from pcbnew import VECTOR2I, FromMM, ToMM

mode, pcb, csvf = sys.argv[1], sys.argv[2], sys.argv[3]
board = pcbnew.LoadBoard(pcb)
fps = {f.GetReference(): f for f in board.GetFootprints()}

if mode == "export":
    rows = []
    for ref, f in fps.items():
        p = f.GetPosition()
        rows.append([ref, f.GetValue(), f.GetFPIDAsString(),
                     round(ToMM(p.x), 3), round(ToMM(p.y), 3),
                     f.GetOrientationDegrees(),
                     "back" if f.IsFlipped() else "front"])
    rows.sort(key=lambda r: r[0])
    with open(csvf, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh); w.writerow(["ref","value","footprint","x_mm","y_mm","rotation","side"])
        w.writerows(rows)
    print(f"exported {len(rows)} parts -> {csvf}")

elif mode == "apply":
    n = 0
    with open(csvf, encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            f = fps.get(row["ref"])
            if not f:
                print("  ?? no footprint", row["ref"]); continue
            f.SetOrientationDegrees(float(row["rotation"]))
            f.SetPosition(VECTOR2I(FromMM(float(row["x_mm"])), FromMM(float(row["y_mm"]))))
            n += 1
    pcbnew.SaveBoard(pcb, board)
    print(f"applied {n} positions -> {pcb}")
