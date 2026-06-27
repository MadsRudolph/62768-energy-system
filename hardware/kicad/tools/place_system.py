#!/usr/bin/env python3
"""
Rebuild the integrated-board placement from the floorplan (recovery + repack).
Run with KiCad 10 python:
  & "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" tools/place_system.py

Toroids placed at fixed spots; the 5 clusters shelf-packed AROUND them with a
clearance margin so courtyards never touch; edge connectors on the borders;
test points bottom-right; R_STAR on the GND/GND_MCU boundary; Edge.Cuts 200x130.
Prints region overflows + a final overlap count (must be 0).
First-pass auto-placement; hand-tune after.
"""
import re
import pcbnew
from pcbnew import VECTOR2I, FromMM, ToMM

PCB = r"C:\Users\Mads2\DTU\4. Semester\Electrical Energy Systems\team\hardware\kicad\system\system.kicad_pcb"
BW, BH = 200.0, 130.0
CLR = 0.8   # clearance margin added around every footprint bbox (mm)

board = pcbnew.LoadBoard(PCB)
fps = {fp.GetReference(): fp for fp in board.GetFootprints()}

def size_mm(fp):
    bb = fp.GetBoundingBox(False)
    return ToMM(bb.GetWidth()), ToMM(bb.GetHeight())

def put(fp, x, y, angle=0):
    fp.SetOrientationDegrees(angle)
    t = VECTOR2I(FromMM(x), FromMM(y)); fp.SetPosition(t)
    c = fp.GetBoundingBox(False).Centre()
    fp.SetPosition(VECTOR2I(t.x + (t.x - c.x), t.y + (t.y - c.y)))

def shelf(refs, x0, y0, xmax, ymax=None, label=""):
    """Left-to-right, wrap at xmax, rows downward. Each cell = bbox + 2*CLR."""
    cx, cy, rowh = x0, y0, 0.0
    for r in refs:
        fp = fps.get(r)
        if fp is None:
            continue
        fp.SetOrientationDegrees(0)
        w, h = size_mm(fp); w += 2*CLR; h += 2*CLR
        if cx + w > xmax and cx > x0:
            cx = x0; cy += rowh; rowh = 0.0
        put(fp, cx + w/2, cy + h/2, 0)
        cx += w; rowh = max(rowh, h)
    bottom = cy + rowh
    if ymax and bottom > ymax + 0.5:
        print(f"  WARN {label}: overflow bottom {bottom:.1f} > {ymax}")
    return bottom

# --- classify ---
EDGE = {
    "J_3PH101": (10, 24, 0), "J_MOT101": (10, 92, 0),
    "J_PV101": (90, 8, 0), "J_INA101": (112, 16, 90), "J_STO101": (132, 8, 0),
    "J_LOAD101": (100, 123, 0),
    "J_15V101": (190, 12, 0), "J_5V101": (190, 27, 0),
    "J_C2K101": (192, 66, 0), "J_ARD101": (192, 106, 0),
}
FIXED_BIG = {"L401": (100, 46, 0), "L501": (100, 99, 0)}  # toroids (left of centre col)
def fdig(ref):
    m = re.search(r"(\d+)$", ref); return m.group(1)[0] if m else "?"

clusters = {"2": [], "3": [], "4": [], "5": [], "6": []}
tps = []
for ref in fps:
    if ref in EDGE or ref in FIXED_BIG or ref == "R_STAR101":
        continue
    if ref.startswith("TP"):
        tps.append(ref); continue
    d = fdig(ref)
    if d in clusters:
        clusters[d].append(ref)
if "R_STAR101" in fps:
    clusters["6"].append("R_STAR101")   # pack with c2000 (GND_MCU side)
for d in clusters:
    clusters[d].sort(key=lambda r: -(lambda wh: wh[0]*wh[1])(size_mm(fps[r])))
tps.sort(key=lambda r: int(re.search(r"\d+", r).group()))

# --- fixed parts ---
for ref, (x, y, a) in {**EDGE, **FIXED_BIG}.items():
    if ref in fps:
        put(fps[ref], x, y, a)
# --- clusters ---
# LEFT column: motor_power (2xx) over motor_feedback (3xx)
shelf(clusters["2"], 18, 6, 80, ymax=102, label="motor_power")
shelf(clusters["3"], 18, 106, 80, ymax=128, label="motor_feedback")
# CENTRE column: toroids on the left (x 82..118), parts to their right (x 120..156)
shelf(clusters["4"], 120, 24, 158, ymax=78, label="mppt_buck")
shelf(clusters["5"], 120, 82, 158, ymax=128, label="boost")
# RIGHT column: c2000 dividers + R_STAR (top), test points (bottom)
shelf(clusters["6"], 160, 8, 186, ymax=95, label="c2000")
shelf(tps, 160, 99, 188, ymax=128, label="testpoints")

# --- Edge.Cuts ---
for d in list(board.GetDrawings()):
    if d.GetLayer() == pcbnew.Edge_Cuts:
        board.Remove(d)
rect = pcbnew.PCB_SHAPE(board)
rect.SetShape(pcbnew.SHAPE_T_RECT)
rect.SetStart(VECTOR2I(FromMM(0), FromMM(0)))
rect.SetEnd(VECTOR2I(FromMM(BW), FromMM(BH)))
rect.SetLayer(pcbnew.Edge_Cuts); rect.SetWidth(FromMM(0.15)); rect.SetFilled(False)
board.Add(rect)

# --- overlap check (courtyard-excluding bbox) ---
boxes = [(f.GetReference(), f.GetBoundingBox(False)) for f in board.GetFootprints()]
ov = []
for i in range(len(boxes)):
    for j in range(i+1, len(boxes)):
        if boxes[i][1].Intersects(boxes[j][1]):
            ov.append((boxes[i][0], boxes[j][0]))

pcbnew.SaveBoard(PCB, board)
print(f"placed {len(fps)} footprints, outline {BW:.0f}x{BH:.0f} mm")
print(f"OVERLAPS: {len(ov)}", "" if not ov else ov[:15])
