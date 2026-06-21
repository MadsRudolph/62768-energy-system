"""Estimate the minimum cluster bbox for a board's footprints packed in signal-flow
rows, using REAL footprint sizes from pcbnew. Helps decide if a board fits the
104x104 laser jig single-sided before committing to a placement.
Run with KiCad python:  & "<kicad>\python.exe" _pack_estimate.py <netlist.json> [gap_mm]
Set KICAD_LASER_EXTRA_LIBS to find vendored libs.
"""
import json, sys, os, math
import pcbnew

FPLIB = r"C:\Program Files\KiCad\9.0\share\kicad\footprints"
SKILL_LIB = r"C:\Users\Mads2\.claude\skills\kicad-laser-pcb\lib"
EXTRA = [p for p in os.environ.get("KICAD_LASER_EXTRA_LIBS", "").split(os.pathsep) if p.strip()]

def load_fp(fpid):
    lib, name = fpid.split(":")
    for base in EXTRA + [SKILL_LIB, FPLIB]:
        d = rf"{base}\{lib}.pretty"
        if os.path.isdir(d):
            fp = pcbnew.FootprintLoad(d, name)
            if fp is not None:
                return fp
    raise SystemExit(f"fp not found: {fpid}")

def size(fp):
    bb = fp.GetBoundingBox(False)
    return pcbnew.ToMM(bb.GetWidth()), pcbnew.ToMM(bb.GetHeight())

jsonf = sys.argv[1]
gap = float(sys.argv[2]) if len(sys.argv) > 2 else 3.0
data = json.load(open(jsonf, encoding="utf-8"))
sz = {}
for c in data["components"]:
    sz[c["ref"]] = size(load_fp(c["footprint"]))

# signal-flow BANDS for motor_power, each a left->right ordered sub-circuit.
# Coupled parts kept adjacent so the router (and a reader) follow the signal path:
#  A: motor drive chain (J1 PWM -> U1 -> opto U3 -> IR2110 U5 -> Q1 -> motor J3)
#  B: 555 + control (U2 osc, opamps U2/U4, pots, timing R/C)
#  C: buck drive chain (J2/SW1 select -> opto U7 -> IR2110 U8 -> Q2 -> L1 -> V1 out)
#  D: 15V supply / 7805 + decoupling
#  E: 3-phase rectifier (J4/J5 + bridge diodes -> bus C11)
BANDS = [
    ["J1","U1","R2","R4","R5","U3","R6","U5","R8","D3","R10","Q1","D4","J3"],
    ["U2","C2","C1","C4","RV1","D1","D2","R1","R3","U4","C6","RV2"],
    ["J2","SW1","R9","R7","U7","R11","U8","R12","R13","D7","Q2","L1","D12","J6","J7","C12"],
    ["U6","C7","C10","C3","C5","C8","C9"],
    ["J4","D5","D6","D10","D11","D8","D9","C11","J5"],
]
SEQ = [r for band in BANDS for r in band]
miss = set(sz) - set(SEQ); extra = set(SEQ) - set(sz)
if miss or extra:
    print("SEQ mismatch  missing:", miss, " extra:", extra); sys.exit(1)

total_area = sum(w*h for w,h in sz.values())

def skyline_pack(items, binw, gp, loc_bias=0.45):
    """items: list of (key, w, h). Pack into bin of width binw, insertion order.
    loc_bias>0 keeps consecutive items near each other (locality) by penalizing
    horizontal distance from the previous item, so signal-flow neighbours cluster.
    Returns {key:(cx,cy)} local centers, and (W,H) of the packed cluster."""
    sky = [(0.0, binw, 0.0)]
    out = {}
    prev_cx = 0.0
    for key, w0, h0 in items:
        w, h = w0 + gp, h0 + gp
        cands = []
        for i in range(len(sky)):
            x0 = sky[i][0]
            if x0 + w > binw + 1e-6: continue
            need = w; yy = 0.0; j = i
            while need > 1e-6 and j < len(sky):
                yy = max(yy, sky[j][2]); need -= sky[j][1]; j += 1
            if need > 1e-6: continue
            cands.append((x0, yy))
        if not cands:
            x0, y0 = 0.0, max(s[2] for s in sky)
        else:
            ymin = min(c[1] for c in cands)
            # among near-lowest candidates, pick the one closest to previous item's x
            x0, y0 = min(cands, key=lambda c: (c[1] - ymin) + loc_bias * abs((c[0] + w/2) - prev_cx))
        prev_cx = x0 + w/2
        out[key] = (x0 + w/2, y0 + h/2)
        top = y0 + h; ns = []
        for (sx, sw, sh) in sky:
            if sx + sw <= x0 + 1e-6 or sx >= x0 + w - 1e-6:
                ns.append((sx, sw, sh)); continue
            if sx < x0: ns.append((sx, x0 - sx, sh))
            rt = sx + sw
            if rt > x0 + w: ns.append((x0 + w, rt - (x0 + w), sh))
        ns.append((x0, w, top)); ns.sort(); sky = ns
    W = max((c[0] for c in out.values()), default=0) + max((it[1] for it in items), default=0)/2 + gp/2
    H = max((s[2] for s in sky), default=0)
    return out, W, H

BOARDW = float(sys.argv[3]) if len(sys.argv) > 3 else 96.0
MODE = sys.argv[4] if len(sys.argv) > 4 else "flat"

if MODE == "blocks":
    # Hierarchical: pack each band into a sub-block, then arrange blocks.
    blocks = {}
    for bi, band in enumerate(BANDS):
        items = [(r, sz[r][0], sz[r][1]) for r in band]
        barea = sum(w*h for _,w,h in items)
        binw = max(max(w for _,w,_ in items), math.sqrt(barea) * 1.3)
        loc, W, H = skyline_pack(items, binw, gap)
        blocks[bi] = (loc, W, H)
    block_items = [(bi, blocks[bi][1], blocks[bi][2]) for bi in blocks]
    borigin, BW, BH = skyline_pack(block_items, BOARDW, gap + 3.0)
    X0, Y0 = 12, 12
    coords = {}
    for bi, (loc, W, H) in blocks.items():
        bx = borigin[bi][0] - W/2; by = borigin[bi][1] - H/2
        for r, (cx, cy) in loc.items():
            coords[r] = (round(X0 + bx + cx, 1), round(Y0 + by + cy, 1), 0)
else:
    # Flat: single skyline over the signal-flow SEQ (compact, decent locality).
    items = [(r, sz[r][0], sz[r][1]) for r in SEQ]
    loc, BW, BH = skyline_pack(items, BOARDW, gap)
    X0, Y0 = 12, 12
    coords = {r: (round(X0 + cx, 1), round(Y0 + cy, 1), 0) for r, (cx, cy) in loc.items()}
print(f"gap={gap} boardw={BOARDW} mode={MODE}")
print(f"CLUSTER {BW:.1f} x {BH:.1f} mm   area={total_area:.0f}mm^2 ({100*total_area/(104*104):.0f}%)")
print(f"SUGGEST JIG  {math.ceil(BW)+8} x {math.ceil(BH)+8}  (blank {math.ceil(BW)+13} x {math.ceil(BH)+13})")
print("PLACE_REFS = {")
for r in SEQ:
    print(f'    "{r}": {coords[r]},')
print("}")
