#!/usr/bin/env python3
"""
Clean grid-aligned placement: components in neat rows, JUSTIFIED to fill each
functional region (even spacing -> real routing channels between parts), same-type
parts grouped, all snapped to a 1 mm grid. Functional blocks spread across the whole
board; each converter keeps its own toroid.

Board has no routing here (strip_all_routing.py already ran). Run KiCad 10 python.
  python place_system3.py
"""
import re
import pcbnew
from pcbnew import VECTOR2I, FromMM, ToMM

PCB = r"C:\Users\Mads2\DTU\4. Semester\Electrical Energy Systems\team\hardware\kicad\system\system.kicad_pcb"
BW, BH = 200.0, 130.0
SNAP = 1.0

board = pcbnew.LoadBoard(PCB)
fps = {fp.GetReference(): fp for fp in board.GetFootprints()}

def size_mm(fp):
    bb = fp.GetBoundingBox(False)
    return ToMM(bb.GetWidth()), ToMM(bb.GetHeight())

def put(fp, x, y, angle=None):
    if angle is not None:
        fp.SetOrientationDegrees(angle)
    t = VECTOR2I(FromMM(x), FromMM(y)); fp.SetPosition(t)
    c = fp.GetBoundingBox(False).Centre()
    fp.SetPosition(VECTOR2I(t.x + (t.x - c.x), t.y + (t.y - c.y)))

def snap(v):
    return round(v / SNAP) * SNAP

# ---- fixed edge connectors (on the borders) ----
EDGE = {
    "J_3PH101": (10, 24, 0), "J_MOT101": (10, 92, 0),
    "J_PV101": (96, 8, 0), "J_INA101": (118, 9, 0), "J_STO101": (140, 8, 0),
    "J_LOAD101": (138, 124, 0),
    "J_15V101": (193, 12, 0), "J_5V101": (193, 28, 0),
    "J_C2K101": (194, 58, 0), "J_ARD101": (194, 104, 0),
}
for ref, (x, y, a) in EDGE.items():
    if ref in fps:
        put(fps[ref], x, y, a)

# ---- functional regions (x0,y0,x1,y1). mppt & boost SIDE BY SIDE in the centre,
# each full height, so neither overflows (stacked, the centre column was too short).
REGION = {
    "2": (18, 8, 78, 126),     # motor_power  (left, full height)
    "4": (82, 24, 118, 116),   # mppt_buck    (+ L401 toroid) -- centre-left, full height
    "5": (122, 24, 158, 116),  # boost        (+ L501 toroid) -- centre-right, full height
    "6": (162, 8, 186, 52),    # c2000_feedback (+ R_STAR)
    "3": (162, 56, 186, 96),   # motor_feedback
    "TP": (162, 100, 186, 126),# probe-point block (right column, bottom)
}
def fdig(ref):
    m = re.search(r"(\d+)$", ref); return m.group(1)[0] if m else "?"

groups = {k: [] for k in REGION}
for ref in fps:
    if ref in EDGE:
        continue
    if ref.startswith("TP"):
        groups["TP"].append(ref); continue
    if ref == "R_STAR101":
        groups["6"].append(ref); continue
    d = fdig(ref)
    if d in groups:
        groups[d].append(ref)

def justified(refs, box, gap):
    """Pack into rows (greedy width), then justify rows over height and items over
    width so the region fills evenly. Returns total height used (for fit check)."""
    x0, y0, x1, y1 = box
    W, H = x1 - x0, y1 - y0
    # lay tall parts on their side (landscape) -> short, uniform rows
    for r in refs:
        fps[r].SetOrientationDegrees(0)
        w, h = size_mm(fps[r])
        if h > w * 1.2:
            fps[r].SetOrientationDegrees(90)
    # group same types together, tall first -> neat rows of similar height
    refs = sorted(refs, key=lambda r: (-round(size_mm(fps[r])[1], 1),
                                       fps[r].GetFPIDAsString(), r))
    rows, cur, curw = [], [], 0.0
    for r in refs:
        w = size_mm(fps[r])[0] + gap
        if cur and curw + w > W:
            rows.append(cur); cur, curw = [], 0.0
        cur.append(r); curw += w
    if cur:
        rows.append(cur)
    rowh = [max(size_mm(fps[r])[1] for r in row) for row in rows]
    total_h = sum(rowh)
    return rows, rowh, total_h, refs

def place_region(refs, box):
    if not refs:
        return
    x0, y0, x1, y1 = box
    W, H = x1 - x0, y1 - y0
    gap = 4.0
    while gap > 0.8:                       # shrink gap until the rows fit the height
        rows, rowh, total_h, _ = justified(refs, box, gap)
        if total_h + gap * (len(rows) + 1) <= H or len(rows) <= 1:
            break
        gap -= 0.5
    vgap = max(gap, (H - sum(rowh)) / (len(rows) + 1))
    y = y0 + vgap
    for ri, row in enumerate(rows):
        rh = rowh[ri]
        tot_w = sum(size_mm(fps[r])[0] for r in row)
        hgap = max(gap, (W - tot_w) / (len(row) + 1))
        x = x0 + hgap
        for r in row:
            w = size_mm(fps[r])[0]
            put(fps[r], snap(x + w / 2), snap(y + rh / 2))
            x += w + hgap
        y += rh + vgap

for k, box in REGION.items():
    place_region(groups[k], box)

# ---- Edge.Cuts ----
for d in list(board.GetDrawings()):
    if d.GetLayer() == pcbnew.Edge_Cuts:
        board.Remove(d)
rect = pcbnew.PCB_SHAPE(board)
rect.SetShape(pcbnew.SHAPE_T_RECT)
rect.SetStart(VECTOR2I(FromMM(0), FromMM(0)))
rect.SetEnd(VECTOR2I(FromMM(BW), FromMM(BH)))
rect.SetLayer(pcbnew.Edge_Cuts); rect.SetWidth(FromMM(0.15)); rect.SetFilled(False)
board.Add(rect)

# ---- overlap check ----
boxes = [(f.GetReference(), f.GetBoundingBox(False)) for f in board.GetFootprints()]
ov = []
for i in range(len(boxes)):
    for j in range(i + 1, len(boxes)):
        if boxes[i][1].Intersects(boxes[j][1]):
            ov.append((boxes[i][0], boxes[j][0]))
pcbnew.SaveBoard(PCB, board)
print(f"placed {len(fps)} footprints, outline {BW:.0f}x{BH:.0f} mm")
for k in REGION:
    print(f"  region {k}: {len(groups[k])} parts")
print(f"OVERLAPS: {len(ov)}", "" if not ov else ov[:20])
