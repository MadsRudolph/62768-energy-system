#!/usr/bin/env python3
"""
Improved integrated-board placement: connectivity-aware force-directed layout per
region (related parts cluster -- decoupling caps by their IC, gate parts by the
MOSFET, divider Rs by the op-amp), pulled toward each region's fixed connectors and
toroids. Strips old routing first. Active separation -> 0 overlaps, 0.5 mm grid snap
for neatness, shelf-pack fallback per region if a region can't resolve.

Same signal-flow regions as place_system.py (proven to fit): motor_power left,
motor_feedback bottom-left, mppt centre-top, boost centre-bottom, c2000 right,
TP row, R_STAR on the GND/GND_MCU side, edge connectors on borders.

Run with KiCad 10 python, KiCad CLOSED.
  python place_system2.py
"""
import re, math, random
import pcbnew
from pcbnew import VECTOR2I, FromMM, ToMM

PCB = r"C:\Users\Mads2\DTU\4. Semester\Electrical Energy Systems\team\hardware\kicad\system\system.kicad_pcb"
BW, BH = 200.0, 130.0
CLR = 0.8                     # courtyard margin between footprints (mm)
random.seed(7)                # deterministic (Math.random-free spirit)

board = pcbnew.LoadBoard(PCB)
fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
# NB: routing/zones must already be stripped TEXTUALLY (tools/strip_all_routing.py)
# before this runs -- in-process board.Remove() on tracks/zones corrupts KiCad's
# SWIG iterators (AttributeError 'thisown').

def size_mm(fp):
    bb = fp.GetBoundingBox(False)
    return ToMM(bb.GetWidth()), ToMM(bb.GetHeight())

def put(fp, x, y, angle=None):
    if angle is not None:
        fp.SetOrientationDegrees(angle)
    t = VECTOR2I(FromMM(x), FromMM(y)); fp.SetPosition(t)
    c = fp.GetBoundingBox(False).Centre()
    fp.SetPosition(VECTOR2I(t.x + (t.x - c.x), t.y + (t.y - c.y)))

# ---- fixed parts ----
EDGE = {
    "J_3PH101": (10, 24, 0), "J_MOT101": (10, 92, 0),
    "J_PV101": (90, 8, 0), "J_INA101": (112, 16, 90), "J_STO101": (132, 8, 0),
    "J_LOAD101": (100, 123, 0),
    "J_15V101": (190, 12, 0), "J_5V101": (190, 27, 0),
    "J_C2K101": (192, 66, 0), "J_ARD101": (192, 106, 0),
}
FIXED_BIG = {"L401": (100, 46, 0), "L501": (100, 99, 0)}
for ref, (x, y, a) in {**EDGE, **FIXED_BIG}.items():
    if ref in fps:
        put(fps[ref], x, y, a)
FIXED = set(EDGE) | set(FIXED_BIG)
fixed_pos = {r: (p[0], p[1]) for r, p in {**EDGE, **FIXED_BIG}.items() if r in fps}

# ---- regions (x0,y0,x1,y1) ----
REGION = {
    "2": (21, 6, 80, 102),     # motor_power (x0 clears left connectors, x1 clears toroids)
    "3": (21, 106, 80, 128),   # motor_feedback
    "4": (118, 22, 158, 78),   # mppt_buck
    "5": (118, 82, 158, 128),  # boost
    "6": (160, 8, 188, 96),    # c2000_feedback (+ R_STAR)
}
def fdig(ref):
    m = re.search(r"(\d+)$", ref); return m.group(1)[0] if m else "?"

clusters = {k: [] for k in REGION}
tps = []
for ref in fps:
    if ref in FIXED:
        continue
    if ref.startswith("TP"):
        tps.append(ref); continue
    if ref == "R_STAR101":
        clusters["6"].append(ref); continue
    d = fdig(ref)
    if d in clusters:
        clusters[d].append(ref)
tps.sort(key=lambda r: int(re.search(r"\d+", r).group()))

# ---- connectivity: comp<->comp weights from shared signal nets ----
PWR = {"GND", "GND_MCU", "+5V_PWR", "+15V_GATE", "+15V2", "+3V3", "+5V"}
net_comps = {}
for ref, fp in fps.items():
    for p in fp.Pads():
        n = p.GetNetname()
        if not n or n in PWR or n.startswith("unconnected-"):
            continue
        net_comps.setdefault(n, set()).add(ref)
weight = {}   # (a,b)->w
for n, comps in net_comps.items():
    if len(comps) < 2 or len(comps) > 6:   # skip single-comp nets and big rails
        continue
    cl = sorted(comps)
    w = 1.0 / (len(cl) - 1)
    for i in range(len(cl)):
        for j in range(i + 1, len(cl)):
            k = (cl[i], cl[j])
            weight[k] = weight.get(k, 0) + w
def wt(a, b):
    return weight.get((a, b) if a < b else (b, a), 0.0)

def overlaps(refs):
    boxes = [(r, fps[r].GetBoundingBox(False)) for r in refs]
    o = []
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            if boxes[i][1].Intersects(boxes[j][1]):
                o.append((boxes[i][0], boxes[j][0]))
    return o

def shelf(refs, x0, y0, x1, y1):
    cx, cy, rowh = x0, y0, 0.0
    for r in sorted(refs, key=lambda r: -(lambda s: s[0]*s[1])(size_mm(fps[r]))):
        fp = fps[r]; fp.SetOrientationDegrees(0)
        w, h = size_mm(fp); w += 2*CLR; h += 2*CLR
        if cx + w > x1 and cx > x0:
            cx = x0; cy += rowh; rowh = 0.0
        put(fp, cx + w/2, cy + h/2)
        cx += w; rowh = max(rowh, h)

def force_layout(refs, box, iters=600):
    """Force-directed inside box; returns True if 0 overlaps after separation."""
    x0, y0, x1, y1 = box
    cxr, cyr = (x0+x1)/2, (y0+y1)/2
    pos = {}
    sz = {}
    for r in refs:
        fps[r].SetOrientationDegrees(0)
        w, h = size_mm(fps[r]); sz[r] = (w, h)
    # init on a coarse grid inside the box
    gx = x0 + 4
    gy = y0 + 4
    for r in refs:
        pos[r] = [gx + random.uniform(-1, 1), gy + random.uniform(-1, 1)]
        gx += 8
        if gx > x1 - 4:
            gx = x0 + 4; gy += 8
            if gy > y1 - 4:
                gy = y0 + 4
    # attractor positions = fixed nodes (connectors/toroids) sharing a net
    for it in range(iters):
        k_att = 0.06
        k_rep = 1.0
        disp = {r: [0.0, 0.0] for r in refs}
        # attraction comp-comp
        for a in refs:
            for b in refs:
                if a >= b:
                    continue
                w = wt(a, b)
                if w <= 0:
                    continue
                dx = pos[b][0]-pos[a][0]; dy = pos[b][1]-pos[a][1]
                d = math.hypot(dx, dy) or 0.01
                rest = (max(sz[a])+max(sz[b]))/2 + CLR
                f = k_att * w * (d - rest)
                ux, uy = dx/d, dy/d
                disp[a][0] += f*ux; disp[a][1] += f*uy
                disp[b][0] -= f*ux; disp[b][1] -= f*uy
            # attraction to fixed attractors
            for fr, fp_ in fixed_pos.items():
                w = wt(a, fr)
                if w <= 0:
                    continue
                dx = fp_[0]-pos[a][0]; dy = fp_[1]-pos[a][1]
                d = math.hypot(dx, dy) or 0.01
                f = k_att * w * 0.5
                disp[a][0] += f*dx/d; disp[a][1] += f*dy/d
            # mild gravity to region centre (compactness)
            disp[a][0] += 0.01*(cxr-pos[a][0]); disp[a][1] += 0.01*(cyr-pos[a][1])
        # repulsion on bbox overlap
        for a in refs:
            for b in refs:
                if a >= b:
                    continue
                dx = pos[b][0]-pos[a][0]; dy = pos[b][1]-pos[a][1]
                ox = (sz[a][0]+sz[b][0])/2 + CLR - abs(dx)
                oy = (sz[a][1]+sz[b][1])/2 + CLR - abs(dy)
                if ox > 0 and oy > 0:                 # overlapping
                    if ox < oy:
                        s = math.copysign(k_rep*ox, dx or 1)
                        disp[a][0] -= s/2; disp[b][0] += s/2
                    else:
                        s = math.copysign(k_rep*oy, dy or 1)
                        disp[a][1] -= s/2; disp[b][1] += s/2
        for r in refs:
            pos[r][0] = min(x1-sz[r][0]/2, max(x0+sz[r][0]/2, pos[r][0]+disp[r][0]))
            pos[r][1] = min(y1-sz[r][1]/2, max(y0+sz[r][1]/2, pos[r][1]+disp[r][1]))
    # hard separation pass
    for _ in range(400):
        moved = False
        for a in refs:
            for b in refs:
                if a >= b:
                    continue
                dx = pos[b][0]-pos[a][0]; dy = pos[b][1]-pos[a][1]
                ox = (sz[a][0]+sz[b][0])/2 + CLR - abs(dx)
                oy = (sz[a][1]+sz[b][1])/2 + CLR - abs(dy)
                if ox > 0 and oy > 0:
                    if ox <= oy:
                        s = math.copysign(ox/2+0.05, dx or 1)
                        pos[a][0]-=s; pos[b][0]+=s
                    else:
                        s = math.copysign(oy/2+0.05, dy or 1)
                        pos[a][1]-=s; pos[b][1]+=s
                    moved = True
        for r in refs:
            pos[r][0] = min(x1-sz[r][0]/2, max(x0+sz[r][0]/2, pos[r][0]))
            pos[r][1] = min(y1-sz[r][1]/2, max(y0+sz[r][1]/2, pos[r][1]))
        if not moved:
            break
    # snap to 0.5 mm grid + apply
    for r in refs:
        x = round(pos[r][0]/0.5)*0.5
        y = round(pos[r][1]/0.5)*0.5
        x = min(x1-sz[r][0]/2, max(x0+sz[r][0]/2, x))
        y = min(y1-sz[r][1]/2, max(y0+sz[r][1]/2, y))
        put(fps[r], x, y)
    return len(overlaps(refs)) == 0

# ---- place each region ----
for k, box in REGION.items():
    refs = clusters[k]
    ok = force_layout(refs, box)
    if not ok:
        print(f"  region {k}: force layout left overlaps -> shelf fallback")
        shelf(refs, box[0], box[1], box[2], box[3])
    else:
        print(f"  region {k}: force layout OK ({len(refs)} parts)")
# TP row (bottom strip) -- keep neat, shelf it
shelf(tps, 160, 100, 190, 128)

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

# ---- overlap check (whole board) ----
allmov = [r for k in clusters for r in clusters[k]] + tps + list(FIXED)
ov = overlaps([r for r in allmov if r in fps])
pcbnew.SaveBoard(PCB, board)
print(f"placed {len(fps)} footprints, outline {BW:.0f}x{BH:.0f} mm")
print(f"OVERLAPS: {len(ov)}", "" if not ov else ov[:15])
