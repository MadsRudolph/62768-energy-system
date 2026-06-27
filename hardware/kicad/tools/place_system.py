#!/usr/bin/env python3
"""
Rebuild the integrated-board placement from the floorplan (recovery after the
unsaved-placement loss). Run with KiCad 10 python:
  & "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" tools/place_system.py

Edge connectors -> borders; the 5 board clusters shelf-packed into their regions
(big parts first); test points in a row; R_STAR on the GND/GND_MCU boundary;
Edge.Cuts outline 196 x 122 mm (<=203.2 wide for the SRM-20).
A first-pass auto-placement — non-overlapping and regioned; fine-tune by hand after.
"""
import re, sys
import pcbnew
from pcbnew import VECTOR2I, FromMM, ToMM

PCB = r"C:\Users\Mads2\DTU\4. Semester\Electrical Energy Systems\team\hardware\kicad\system\system.kicad_pcb"
BW, BH = 200.0, 130.0   # <=203.2 wide (mill X), <=133 tall (stock)

board = pcbnew.LoadBoard(PCB)
fps = {fp.GetReference(): fp for fp in board.GetFootprints()}

def put(fp, x, y, angle=0):
    fp.SetOrientationDegrees(angle)
    t = VECTOR2I(FromMM(x), FromMM(y)); fp.SetPosition(t)
    c = fp.GetBoundingBox(False).Centre()
    fp.SetPosition(VECTOR2I(t.x + (t.x - c.x), t.y + (t.y - c.y)))

def size_mm(fp):
    bb = fp.GetBoundingBox(False)
    return ToMM(bb.GetWidth()), ToMM(bb.GetHeight())

def shelf(refs, x0, y0, xmax, gap=2.5, angle=0):
    """Left-to-right, wrap at xmax, rows downward. Returns bottom y used."""
    cx, cy, rowh = x0, y0, 0.0
    for r in refs:
        fp = fps.get(r)
        if fp is None:
            continue
        fp.SetOrientationDegrees(angle)
        w, h = size_mm(fp)
        if cx + w > xmax and cx > x0:
            cx = x0; cy += rowh + gap; rowh = 0.0
        put(fp, cx + w/2, cy + h/2, angle)
        cx += w + gap; rowh = max(rowh, h)
    return cy + rowh

# --- classify refs ---
EDGE = {  # ref: (x, y, angle)
    "J_3PH101": (12, 22, 0), "J_MOT101": (12, 86, 0),
    "J_PV101": (98, 8, 0), "J_INA101": (98, 18, 0), "J_STO101": (128, 8, 0),
    "J_LOAD101": (120, 124, 0),
    "J_15V101": (190, 12, 0), "J_5V101": (190, 28, 0),
    "J_C2K101": (192, 62, 0), "J_ARD101": (192, 102, 0),
}
def first_digit(ref):
    m = re.search(r"(\d+)$", ref)
    return m.group(1)[0] if m else "?"

clusters = {"2": [], "3": [], "4": [], "5": [], "6": []}
tps = []
for ref in fps:
    if ref in EDGE or ref == "R_STAR101":
        continue
    if ref.startswith("TP"):
        tps.append(ref); continue
    d = first_digit(ref)
    if d in clusters:
        clusters[d].append(ref)

# big parts first within each cluster (better packing + anchors land top-left)
for d in clusters:
    clusters[d].sort(key=lambda r: -(lambda wh: wh[0]*wh[1])(size_mm(fps[r])))
tps.sort(key=lambda r: int(re.search(r"\d+", r).group()))

# --- place edge connectors ---
for ref, (x, y, a) in EDGE.items():
    if ref in fps:
        put(fps[ref], x, y, a)

# --- place clusters in regions ---
# LEFT: motor_power (2xx) + motor_feedback (3xx)
b = shelf(clusters["2"], 22, 8, 92, gap=2.5)
shelf(clusters["3"], 22, max(b + 4, 104), 90, gap=2.5)
# CENTRE-TOP: mppt_buck (4xx)
shelf(clusters["4"], 98, 24, 154, gap=2.2)
# CENTRE-BOTTOM: boost (5xx)
shelf(clusters["5"], 98, 66, 154, gap=2.2)
# RIGHT: c2000_feedback (6xx)
shelf(clusters["6"], 158, 12, 194, gap=2.0)
# R_STAR on the GND/GND_MCU boundary (between centre power + right MCU)
if "R_STAR101" in fps:
    put(fps["R_STAR101"], 156, 108, 0)
# test points: row along the bottom (move locally near nets when routing)
shelf(tps, 30, 122, 192, gap=3.0)

# --- Edge.Cuts outline (replace any existing) ---
for d in list(board.GetDrawings()):
    if d.GetLayer() == pcbnew.Edge_Cuts:
        board.Remove(d)
rect = pcbnew.PCB_SHAPE(board)
rect.SetShape(pcbnew.SHAPE_T_RECT)
rect.SetStart(VECTOR2I(FromMM(0), FromMM(0)))
rect.SetEnd(VECTOR2I(FromMM(BW), FromMM(BH)))
rect.SetLayer(pcbnew.Edge_Cuts)
rect.SetWidth(FromMM(0.15))
rect.SetFilled(False)
board.Add(rect)

pcbnew.SaveBoard(PCB, board)
print(f"placed {len(fps)} footprints; outline {BW:.0f}x{BH:.0f} mm")
print("clusters:", {d: len(v) for d, v in clusters.items()}, "| TP:", len(tps))
