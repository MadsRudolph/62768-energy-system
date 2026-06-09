#!/usr/bin/env python3
"""
Build the buck converter (15 V -> 5 V) schematic in the same wired style as the
hand-drawn boost: V_in source on the left, components on a top rail, GND rail at
the bottom. High-side N-MOSFET switch. KiCad 9 / sexpdata.

Topology:  VIN -> M1(drain-source) -> SW -> L1 -> OUT -> C1 || Rload
           D1 freewheel: SW(cathode) -> GND(anode)
Gate net 'GATE' + node 'SW' are labelled so add_optocoupler.py can attach an
SW-referenced (floating) gate drive afterwards.
"""
import copy
import uuid as _uuid
from pathlib import Path
import sexpdata
from sexpdata import Symbol as S

SYM = {
    "Simulation_SPICE:VDC": (r"C:\Program Files\KiCad\9.0\share\kicad\symbols\Simulation_SPICE.kicad_sym", "VDC"),
    "Device:L": (r"C:\Program Files\KiCad\9.0\share\kicad\symbols\Device.kicad_sym", "L"),
    "Device:Q_NMOS": (r"C:\Program Files\KiCad\9.0\share\kicad\symbols\Device.kicad_sym", "Q_NMOS"),
    "Device:D_Schottky": (r"C:\Program Files\KiCad\9.0\share\kicad\symbols\Device.kicad_sym", "D_Schottky"),
    "Device:C_Polarized": (r"C:\Program Files\KiCad\9.0\share\kicad\symbols\Device.kicad_sym", "C_Polarized"),
    "Device:R": (r"C:\Program Files\KiCad\9.0\share\kicad\symbols\Device.kicad_sym", "R"),
}
PIN = {
    "Simulation_SPICE:VDC": {"1": (0, 5.08), "2": (0, -5.08)},
    "Device:L": {"1": (0, 3.81), "2": (0, -3.81)},
    "Device:Q_NMOS": {"G": (-5.08, 0), "D": (2.54, 5.08), "S": (2.54, -5.08)},
    "Device:D_Schottky": {"1": (-3.81, 0), "2": (3.81, 0)},      # 1=K, 2=A
    "Device:C_Polarized": {"1": (0, 3.81), "2": (0, -3.81)},
    "Device:R": {"1": (0, 3.81), "2": (0, -3.81)},
}
OUT = Path(__file__).parent / "buck.kicad_sch"


def uid():
    return str(_uuid.uuid4())


def rot(a, b, ang):
    # KiCad stored angle -> math rotation by -angle (verified against ERC pin coords)
    if ang == 0:   return (a, b)
    if ang == 90:  return (b, -a)
    if ang == 180: return (-a, -b)
    if ang == 270: return (-b, a)


def pin_xy(lib, pin, x, y, ang):
    px, py = PIN[lib][pin]
    ox, oy = rot(px, -py, ang)
    return (round(x + ox, 2), round(y + oy, 2))


def extract(lib_id):
    path, name = SYM[lib_id]
    t = sexpdata.loads(Path(path).read_text(encoding="utf-8"))
    for it in t:
        if isinstance(it, list) and len(it) > 1 and isinstance(it[0], S) \
                and it[0].value() == "symbol" and it[1] == name:
            s = copy.deepcopy(it)
            s[1] = lib_id
            return s
    raise ValueError(lib_id)


def _prop(name, value, x, y, hide=False):
    p = [S("property"), name, str(value), [S("at"), x, y, 0],
         [S("effects"), [S("font"), [S("size"), 1.27, 1.27]]]]
    if hide:
        p[4].append(S("hide"))
    return p


def make_symbol(lib_id, ref, value, x, y, ang, pins, root):
    sym = [S("symbol"), [S("lib_id"), lib_id], [S("at"), x, y, ang], [S("unit"), 1],
           [S("exclude_from_sim"), S("no")], [S("in_bom"), S("yes")],
           [S("on_board"), S("yes")], [S("dnp"), S("no")], [S("uuid"), uid()],
           _prop("Reference", ref, x + 2.54, y - 6.35),
           _prop("Value", value, x + 2.54, y + 3.81),
           _prop("Footprint", "", x, y, hide=True),
           _prop("Datasheet", "", x, y, hide=True),
           _prop("Description", "", x, y, hide=True)]
    for pn in pins:
        sym.append([S("pin"), str(pn), [S("uuid"), uid()]])
    sym.append([S("instances"), [S("project"), "energy_system",
                [S("path"), f"/{root}", [S("reference"), ref], [S("unit"), 1]]]])
    return sym


def wire(x1, y1, x2, y2):
    return [S("wire"), [S("pts"), [S("xy"), x1, y1], [S("xy"), x2, y2]],
            [S("stroke"), [S("width"), 0], [S("type"), S("default")]], [S("uuid"), uid()]]


def label(name, x, y):
    return [S("label"), name, [S("at"), x, y, 0],
            [S("effects"), [S("font"), [S("size"), 1.27, 1.27]],
             [S("justify"), S("left"), S("bottom")]], [S("uuid"), uid()]]


def glabel(name, x, y):
    return [S("global_label"), name, [S("shape"), S("input")], [S("at"), x, y, 0],
            [S("effects"), [S("font"), [S("size"), 1.27, 1.27]], [S("justify"), S("left")]],
            [S("uuid"), uid()],
            [S("property"), "Intersheetrefs", "${INTERSHEET_REFS}", [S("at"), 0, 0, 0],
             [S("effects"), [S("font"), [S("size"), 1.27, 1.27]], [S("hide"), S("yes")]]]]


def text(t, x, y):
    return [S("text"), t, [S("at"), x, y, 0],
            [S("effects"), [S("font"), [S("size"), 2, 2], [S("thickness"), 0.4], S("bold")],
             [S("justify"), S("left")]], [S("uuid"), uid()]]


root = uid()

# ---- component placements (rotation-aware) ----
#   M1 high-side: 0deg (drain up=VIN, source down=SW, gate left)
#   D1 freewheel: 270deg (cathode up=SW, anode down=GND)
#   L1: 90deg horizontal (SW -> OUT)
comps = [
    ("Simulation_SPICE:VDC", "V_in", "15", 81.28, 116.84, 0, ["1", "2"]),
    ("Device:Q_NMOS", "M1", "IRF530N", 101.6, 109.22, 0, ["G", "D", "S"]),
    ("Device:D_Schottky", "D1", "1N5819", 104.14, 118.11, 270, ["1", "2"]),
    ("Device:L", "L1", "470u", 116.84, 114.3, 90, ["1", "2"]),
    ("Device:C_Polarized", "C1", "47u", 132.08, 118.11, 0, ["1", "2"]),
    ("Device:R", "Rload", "10", 149.86, 118.11, 0, ["1", "2"]),
]
elems = [make_symbol(l, r, v, x, y, a, p, root) for (l, r, v, x, y, a, p) in comps]

TOP, SWY, GND = 104.14, 114.3, 124.46
Vp = pin_xy("Simulation_SPICE:VDC", "1", 81.28, 116.84, 0)    # V_in +
Vn = pin_xy("Simulation_SPICE:VDC", "2", 81.28, 116.84, 0)    # V_in -
Md = pin_xy("Device:Q_NMOS", "D", 101.6, 109.22, 0)          # drain  -> VIN (104.14,104.14)
Ms = pin_xy("Device:Q_NMOS", "S", 101.6, 109.22, 0)          # source -> SW  (104.14,114.3)
Mg = pin_xy("Device:Q_NMOS", "G", 101.6, 109.22, 0)          # gate          (96.52,109.22)
Da = pin_xy("Device:D_Schottky", "2", 104.14, 118.11, 270)   # anode -> GND  (104.14,121.92)
Ll = pin_xy("Device:L", "1", 116.84, 114.3, 90)              # left  -> SW   (113.03,114.3)
Lr = pin_xy("Device:L", "2", 116.84, 114.3, 90)              # right -> OUT  (120.65,114.3)
Ct = pin_xy("Device:C_Polarized", "1", 132.08, 118.11, 0)    # top -> OUT    (132.08,114.3)
Cb = pin_xy("Device:C_Polarized", "2", 132.08, 118.11, 0)    # bottom -> GND
Rt = pin_xy("Device:R", "1", 149.86, 118.11, 0)
Rb = pin_xy("Device:R", "2", 149.86, 118.11, 0)

# ---- wires ----
elems += [
    wire(*Vp, Vp[0], TOP), wire(Vp[0], TOP, Md[0], TOP),       # V_in+ up, VIN rail -> M1.D
    wire(*Ms, Ll[0], SWY),                                      # SW: M1.S -> L1.left (D1.K coincides)
    wire(*Da, Da[0], GND),                                      # D1.A -> GND
    wire(*Lr, Lr[0], TOP), wire(Lr[0], TOP, Ct[0], TOP), wire(Ct[0], TOP, Rt[0], TOP),  # OUT rail
    wire(Ct[0], TOP, *Ct), wire(Rt[0], TOP, *Rt),              # OUT down to C1, Rload
    wire(*Cb, Cb[0], GND), wire(*Rb, Rb[0], GND),              # bottoms -> GND
    wire(*Vn, Vn[0], GND),                                      # V_in- -> GND
    wire(Vn[0], GND, Da[0], GND), wire(Da[0], GND, Ct[0], GND), wire(Ct[0], GND, Rt[0], GND),
    wire(*Mg, Mg[0], SWY),                                      # gate stub down
]
# ---- labels ----
elems += [
    glabel("GATE", Mg[0], SWY),
    label("SW", 109.22, SWY),
    label("VIN_15V", 88.9, TOP),
    label("VOUT_5V", 140.97, TOP),
    label("GND", 93.98, GND),
    text("Buck converter  15V -> 5V   (62768, Krav 8/9)", 76.2, 86.36),
]

lib_symbols = [S("lib_symbols")] + [extract(l) for l in PIN if l in {c[0] for c in comps}]
tree = [S("kicad_sch"),
        [S("version"), 20250114], [S("generator"), "eeschema"],
        [S("generator_version"), "9.0"], [S("uuid"), root], [S("paper"), "A4"],
        lib_symbols, *elems,
        [S("sheet_instances"), [S("path"), "/", [S("page"), "1"]]],
        [S("embedded_fonts"), S("no")]]
OUT.write_text(sexpdata.dumps(tree), encoding="utf-8")
print("wrote", OUT)
