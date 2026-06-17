#!/usr/bin/env python3
"""
Kirurgisk patch af buck_v2.kicad_sch: erstat den gamle gate-drive (4N25-opto med
9V-batteri flydende paa SW) med en rigtig IR2110 HIGH-SIDE driver.

BEVARER hele front-enden (LM7805 -> NE555 -> RV1/D1/D2 timing, SW1 555/ekstern-valg,
opto-LED siden) og effekttrinet (Q1/D3/L1/C4). Optoen bliver staaende: den
level-shifter den 5V PWM op til IR2110'ens ~9.5V logik-taerskel.

Aendringer:
  - Slet J1 (9V-batteri) + dens wires/labels (+9V_SW, SW i top-venstre).
  - Omdoeb opto-kollektorens net +9V_SW -> +15V (jordrefereret driver-forsyning).
  - Klip gate-wiren U3.4(emitter)/R4.1 -> Q1.G; flyt R4 vaek saa emitter og gate skilles.
  - Opto-emitter (U3.4) -> HIN. Q1-gate -> GATE.
  - Tilfoej IR2110 (U4) high-side: HIN, LIN/SD->GND, VS->SW, VB via bootstrap
    (D4 fra VCC/+15V -> VB, C7 VB->VS), HO -> R5(10) || D5(1N4148) -> gate.
  - R4(1k) gate->SW pulldown (flyttet). R6(1k) HIN-pulldown. C8/C9 +15V afkobling.
  - J5 driver-forsyning +15V/GND + PWR_FLAG.

Verificeres bagefter via ERC + netliste. Koer: py -3.13 patch_buck_v2_ir2110.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1]))   # schbuild ligger i tools/
import schbuild
from schbuild import S
import sexpdata

SCH = Path(__file__).parents[2] / "boards/buck/buck_v2/buck_v2.kicad_sch"
t = sexpdata.loads(SCH.read_text(encoding="utf-8"))

def tag(x): return isinstance(x, list) and x and isinstance(x[0], S) and x[0].value()
def getv(node, name):
    for c in node:
        if tag(c) == name: return c
def at_of(node):
    a = getv(node, "at")
    return (round(float(a[1]), 2), round(float(a[2]), 2)) if a else None
def sym_ref(c):
    for p in c:
        if tag(p) == "property" and p[1] == "Reference": return p[2]

root = getv(t, "uuid")[1]
project = "energy_system"
for c in t:
    if tag(c) == "symbol":
        inst = getv(c, "instances")
        if inst:
            for p in inst:
                if tag(p) == "project": project = p[1]; break
        if project: break

EPS = 0.05
def near(p, q): return p is not None and abs(p[0]-q[0]) < EPS and abs(p[1]-q[1]) < EPS
def wpts(w):
    pts = getv(w, "pts"); xy = [c for c in pts if tag(c) == "xy"]
    return ((round(float(xy[0][1]),2), round(float(xy[0][2]),2)),
            (round(float(xy[1][1]),2), round(float(xy[1][2]),2)))

# ---- deletions ----
DEL_WIRES = [((31.75,27.94),(31.75,33.02)), ((46.99,25.4),(46.99,27.94)),
             ((46.99,27.94),(34.29,27.94)),
             ((156.21,86.36),(168.91,86.36)),            # gammel gate-wire U3.4/R4.1 -> Q1.G
             ((156.21,93.98),(156.21,96.52))]            # R4.2 -> SW label
DEL_JUNC = [(156.21,86.36)]
DEL_LABELS = [("SW",(31.75,33.02)), ("+9V_SW",(46.99,25.4)), ("SW",(156.21,96.52))]
DEL_REFS = {"J1", "R4"}                                  # R4 genplaceres

def wire_match(w):
    a, b = wpts(w)
    for da, db in DEL_WIRES:
        if (near(a,da) and near(b,db)) or (near(a,db) and near(b,da)): return True
    return False
def label_match(l):
    p = at_of(l)
    return any(l[1] == n and near(p, pos) for n, pos in DEL_LABELS)

kept = []
removed = {"wire":0,"junction":0,"label":0,"symbol":0}
for c in t:
    tg = tag(c)
    if tg == "wire" and wire_match(c): removed["wire"]+=1; continue
    if tg == "junction" and any(near(at_of(c), j) for j in DEL_JUNC): removed["junction"]+=1; continue
    if tg == "label" and label_match(c): removed["label"]+=1; continue
    if tg == "symbol" and sym_ref(c) in DEL_REFS: removed["symbol"]+=1; continue
    kept.append(c)

# ---- relabel opto collector net +9V_SW -> +15V ----
renamed = 0
for c in kept:
    if tag(c) == "label" and c[1] == "+9V_SW" and near(at_of(c), (156.21,74.93)):
        c[1] = "+15V"; renamed += 1

# ---- update stale text notes ----
for c in kept:
    if tag(c) == "text":
        if "batteriet FLYDER" in c[1]:
            c[1] = "Gate-drive: opto (5V PWM) -> IR2110 HIN ; HO -> R5(10) -> gate (high-side)."
        elif "R5 holder" in c[1]:
            c[1] = "VS=SW, bootstrap D4(+15V->VB)/C7(VB->VS). R4=gate->SW pulldown. +15V via J5; LF50/555 fra Rectifier (V1)."

# ---- new lib_symbol: IR2110 ----
libsyms = getv(kept, "lib_symbols")
libsyms.append(schbuild.extract("Driver_FET:IR2110"))

# ---- new elements (schbuild-style: symbol + stub-wire + net-label per pin) ----
new_elems = []
def place(lib, ref, val, fp, x, y, ang, nets, unit=1):
    x, y = schbuild.snap(x), schbuild.snap(y)
    new_elems.append(schbuild.symbol(lib, ref, val, fp, x, y, ang, unit, list(nets.keys()), root, project))
    for p, net in nets.items():
        ex, ey = schbuild.pin_xy(lib, p, x, y, ang, unit)
        rx, ry = ex - x, ey - y
        if abs(rx) >= abs(ry): sx, sy = ex + (2.54 if rx >= 0 else -2.54), ey
        else: sx, sy = ex, ey + (2.54 if ry >= 0 else -2.54)
        new_elems.append(schbuild.wire(ex, ey, round(sx,2), round(sy,2)))
        new_elems.append(schbuild.label(net, round(sx,2), round(sy,2), False))
def nc(lib, p, x, y, ang=0, unit=1):
    ex, ey = schbuild.pin_xy(lib, p, schbuild.snap(x), schbuild.snap(y), ang, unit)
    new_elems.append(schbuild.noconnect(ex, ey))
def stub(pt, net, dx):
    ex, ey = pt
    new_elems.append(schbuild.wire(ex, ey, round(ex+dx,2), ey))
    new_elems.append(schbuild.label(net, round(ex+dx,2), ey, False))

FP_R     = "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal"
FP_DIP14 = "Package_DIP:DIP-14_W7.62mm_LongPads"
FP_CP    = "Capacitor_THT:CP_Radial_D8.0mm_P3.50mm"
FP_CDISC = "Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm"
FP_DO35  = "Diode_THT:D_DO-35_SOD27_P7.62mm_Horizontal"
FP_TERM  = "TerminalBlock:TerminalBlock_bornier-2_P5.08mm"
IR = "Driver_FET:IR2110"

# IR2110 high-side: VDD/VCC=+15V, VSS/COM/LIN/SD=GND, HIN=HIN, VS=SW, VB=VB, HO=HO
place(IR, "U4", "IR2110", FP_DIP14, 150, 130, 0,
      {"9":"+15V","3":"+15V","13":"GND","2":"GND","10":"HIN","12":"GND","11":"GND",
       "5":"SW","6":"VB","7":"HO"})
for p in ("1","4","8","14"):                              # LO + NC ubrugt
    nc(IR, p, 150, 130)
place("Device:D", "D4", "1N4148", FP_DO35, 185, 118, 0, {"2":"+15V","1":"VB"})  # boot: A=+15V,K=VB
place("Device:C", "C7", "1u",     FP_CDISC,200, 124, 0, {"1":"VB","2":"SW"})    # boot-cap VB->VS
place("Device:R", "R5", "10",     FP_R,    185, 145, 0, {"1":"HO","2":"GATE"})  # serie gate-R
place("Device:D", "D5", "1N4148", FP_DO35, 200, 145, 0, {"1":"HO","2":"GATE"})  # anti-parallel (K=HO,A=GATE)
place("Device:R", "R6", "1k",     FP_R,    124, 128, 0, {"1":"HIN","2":"GND"})  # HIN pulldown
place("Device:C", "C8", "22u",    FP_CP,    75, 120, 0, {"1":"+15V","2":"GND"}) # bulk afkobling
place("Device:C", "C9", "100n",   FP_CDISC, 90, 120, 0, {"1":"+15V","2":"GND"}) # HF afkobling
place("Connector:Conn_01x02_Socket", "J5", "drive +15V", FP_TERM, 60, 120, 0, {"1":"+15V","2":"GND"})
place("power:PWR_FLAG", "#FLG03", "PWR_FLAG", "", 105, 120, 0, {"1":"+15V"})
place("Device:R", "R4", "1k",     FP_R,    120, 145, 0, {"1":"GATE","2":"SW"})  # gate->SW pulldown (flyttet)

# existing-pin stubs: opto emitter -> HIN, Q1 gate -> GATE
stub((156.21, 86.36), "HIN", +2.54)
stub((168.91, 86.36), "GATE", -2.54)

# splice new elements before sheet_instances
idx = len(kept)
for i, c in enumerate(kept):
    if tag(c) == "sheet_instances": idx = i; break
kept[idx:idx] = new_elems

SCH.write_text(sexpdata.dumps(kept), encoding="utf-8")
print(f"patched {SCH.name}: removed {removed}, renamed +9V_SW->+15V x{renamed}, "
      f"added {len([e for e in new_elems if tag(e)=='symbol'])} symbols")
