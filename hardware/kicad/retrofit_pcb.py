#!/usr/bin/env python3
"""
Goer de 4 eksisterende skemaer PCB-klar (engangs-retrofit, koeres fra hardware/kicad):

1. drive_circuit: retter to wiring-fejl fra GUI-redigeringen
   - D1 (friloebsdiode) laa med BEGGE ben paa +20V (motor+ er +20V-skinnen)
     -> anoden flyttes til motorens switch-knude (M1.2/Q1.D)
   - HIN/SD/VSS/VS-oeen paa IR2110 var loesrevet fra GND -> GND-label paasat
2. buck/boost: fjerner sim-artefakterne V_in (SPICE VDC) og Rload og saetter
   skrueterminaler/headers paa i stedet (J1 ind, J2 ud, J3 PWM, J4 gate-forsyning)
3. Alle komponenter i alle 4 skemaer faar Footprint-property
   (se bom/footprint_map.csv for valg + begrundelser)

Koer: py -3.13 retrofit_pcb.py
"""
import sys, copy
from pathlib import Path
import sexpdata
from sexpdata import Symbol as S

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE / "system"))
import schbuild
from schbuild import uid, extract, pins, pin_xy, wire, label, _prop

FP = {
    "R":      "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal",
    "CDISC":  "Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm",
    "CP8":    "Capacitor_THT:CP_Radial_D8.0mm_P3.50mm",
    "DO41":   "Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal",
    "TO220":  "Package_TO_SOT_THT:TO-220-3_Vertical",
    "DIP6":   "Package_DIP:DIP-6_W7.62mm",
    "DIP8":   "Package_DIP:DIP-8_W7.62mm",
    "DIP14":  "Package_DIP:DIP-14_W7.62mm",
    "L_RAD":  "Inductor_THT:L_Radial_D10.0mm_P5.00mm_Fastron_07P",
    "TERM2":  "TerminalBlock:TerminalBlock_bornier-2_P5.08mm",
    "TERM3":  "TerminalBlock:TerminalBlock_bornier-3_P5.08mm",
    "HDR2":   "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
    "HDR3":   "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical",
}

# ref -> footprint, pr. skema
ASSIGN = {
    "converters/design/buck.kicad_sch": {
        "D1": FP["DO41"], "M1": FP["TO220"], "R1": FP["R"], "R2": FP["R"],
        "C1": FP["CP8"], "U1": FP["DIP6"], "L1": FP["L_RAD"],
    },
    "converters/design/boost.kicad_sch": {
        "D1": FP["DO41"], "M1": FP["TO220"], "R1": FP["R"], "R2": FP["R"],
        "C1": FP["CP8"], "U1": FP["DIP6"], "L1": FP["L_RAD"],
    },
    "exp3a/drive_circuit.kicad_sch": {
        "R1": FP["R"], "R2": FP["R"], "R3": FP["R"], "R4": FP["R"],
        "C1": FP["CP8"], "C2": FP["CDISC"], "U1": FP["DIP8"], "U2": FP["DIP14"],
        "Q1": FP["TO220"], "D1": FP["DO41"], "D2": FP["DO41"], "M1": FP["TERM2"],
    },
    "exp3a/feedback_circuit.kicad_sch": {
        "R1": FP["R"], "R2": FP["R"], "R3": FP["R"], "R4": FP["R"], "R5": FP["R"],
        "U1": FP["DIP8"], "U3": FP["DIP8"], "U4": FP["DIP8"],
    },
}

def load(p): return sexpdata.loads(Path(p).read_text(encoding="utf-8"))
def save(p, t): Path(p).write_text(sexpdata.dumps(t), encoding="utf-8")

def sym_entries(tree):
    for it in tree:
        if isinstance(it, list) and it and isinstance(it[0], S) and it[0].value() == "symbol":
            yield it

def get(it, key):
    for c in it:
        if isinstance(c, list) and c and isinstance(c[0], S) and c[0].value() == key:
            return c

def ref_of(it):
    for c in it:
        if isinstance(c, list) and c and isinstance(c[0], S) and c[0].value() == "property" \
                and c[1] == "Reference":
            return c[2]

def project_of(tree):
    for it in sym_entries(tree):
        inst = get(it, "instances")
        if inst:
            return inst[1][1]          # (project "navn" ...)
    return "project"

def root_of(tree):
    return get(tree, "uuid")[1]

def set_footprint(tree, ref, fp):
    n = 0
    for it in sym_entries(tree):
        if ref_of(it) == ref:
            for c in it:
                if isinstance(c, list) and c and isinstance(c[0], S) \
                        and c[0].value() == "property" and c[1] == "Footprint":
                    c[2] = fp; n += 1
    return n

def remove_symbol(tree, ref):
    """Fjern symbol + stub-wires fra dets pins + labels der sad paa stubbene."""
    target = None
    for it in sym_entries(tree):
        if ref_of(it) == ref:
            target = it
    if target is None:
        return []
    lib = get(target, "lib_id")[1]
    at = get(target, "at")
    x, y, ang = at[1], at[2], at[3]
    unit = get(target, "unit")[1]
    pp = [pin_xy(lib, p, x, y, ang, unit)
          for p in sorted(pins(lib, unit), key=lambda s: int(s))]
    tree.remove(target)
    orphan_pts = set()
    for it in [w for w in tree if isinstance(w, list) and w and isinstance(w[0], S)
               and w[0].value() == "wire"]:
        pts = get(it, "pts")
        a = (pts[1][1], pts[1][2]); b = (pts[2][1], pts[2][2])
        if a in pp or b in pp:
            tree.remove(it)
            orphan_pts.update([a, b])
    for it in [l for l in tree if isinstance(l, list) and l and isinstance(l[0], S)
               and l[0].value() in ("label", "global_label")]:
        a = get(it, "at")
        if (a[1], a[2]) in orphan_pts:
            tree.remove(it)
    return pp

def label_at(tree, net, x, y, glob=False):
    """Saet label direkte paa et eksisterende wire-endepunkt."""
    idx = next(i for i, c in enumerate(tree)
               if isinstance(c, list) and c and isinstance(c[0], S)
               and c[0].value() == "sheet_instances")
    tree.insert(idx, label(net, x, y, glob))

def pin_pos(tree, ref, pin):
    for it in sym_entries(tree):
        if ref_of(it) == ref:
            lib = get(it, "lib_id")[1]
            at = get(it, "at")
            unit = get(it, "unit")[1]
            return pin_xy(lib, pin, at[1], at[2], at[3], unit)

def ensure_libsym(tree, lib_id):
    libsyms = get(tree, "lib_symbols")
    for c in libsyms[1:]:
        if isinstance(c, list) and len(c) > 1 and c[1] == lib_id:
            return
    libsyms.append(copy.deepcopy(extract(lib_id)))

def add_symbol(tree, lib_id, ref, val, fp, x, y, ang, nets, globals_, project, root,
               attach=None):
    """Nyt symbol; nets {pin: net} -> stub+label, attach {pin: (x,y)} -> wire direkte."""
    ensure_libsym(tree, lib_id)
    x, y = schbuild.snap(x), schbuild.snap(y)
    pinlist = sorted(set(list(nets.keys()) + list((attach or {}).keys())))
    s = schbuild.symbol(lib_id, ref, val, fp, x, y, ang, 1, pinlist, root, project)
    # indsaet foer sheet_instances
    idx = next(i for i, c in enumerate(tree)
               if isinstance(c, list) and c and isinstance(c[0], S)
               and c[0].value() == "sheet_instances")
    tree.insert(idx, s)
    new = []
    for p, net in nets.items():
        ex, ey = pin_xy(lib_id, p, x, y, ang)
        rx, ry = ex - x, ey - y
        if abs(rx) >= abs(ry): sx, sy = ex + (2.54 if rx >= 0 else -2.54), ey
        else: sx, sy = ex, ey + (2.54 if ry >= 0 else -2.54)
        new.append(wire(ex, ey, round(sx, 2), round(sy, 2)))
        new.append(label(net, round(sx, 2), round(sy, 2), net in globals_))
    for p, (tx, ty) in (attach or {}).items():
        ex, ey = pin_xy(lib_id, p, x, y, ang)
        if ex != tx and ey != ty:               # L-form via hjoernepunkt
            new.append(wire(ex, ey, tx, ey)); new.append(wire(tx, ey, tx, ty))
        else:
            new.append(wire(ex, ey, tx, ty))
    for el in new:
        tree.insert(idx + 1, el)

# ---------------------------------------------------------------- drive fixes
def fix_drive(tree, project, root):
    # 1) friloebsdiode: D1.A (171.45,77.47) væk fra +20V-grenen, ned paa switch-knuden
    for it in [w for w in tree if isinstance(w, list) and w and isinstance(w[0], S)
               and w[0].value() == "wire"]:
        pts = get(it, "pts")
        seg = {(pts[1][1], pts[1][2]), (pts[2][1], pts[2][2])}
        if seg == {(171.45, 77.47), (171.45, 80.01)} or \
           seg == {(171.45, 80.01), (181.61, 80.01)}:
            tree.remove(it)
    idx = next(i for i, c in enumerate(tree)
               if isinstance(c, list) and c and isinstance(c[0], S)
               and c[0].value() == "sheet_instances")
    tree.insert(idx, wire(171.45, 77.47, 171.45, 93.98))
    tree.insert(idx, wire(171.45, 93.98, 181.61, 93.98))
    # 2) HIN/SD/VSS/VS-oeen til GND: global label paa eksisterende endepunkt
    tree.insert(idx, label("GND", 114.3, 116.84, True))
    print("  drive: D1 friloeb flyttet til switch-knuden; IR2110-oe paa GND")

def do_drive():
    f = HERE / "exp3a/drive_circuit.kicad_sch"
    t = load(f); proj, root = project_of(t), root_of(t)
    fix_drive(t, proj, root)
    add_symbol(t, "Connector_Generic:Conn_01x02", "J1", "PWM ind", FP["HDR2"],
               40, 130, 0, {"1": "PWM", "2": "GND"}, {"PWM", "GND"}, proj, root)
    add_symbol(t, "Connector:Screw_Terminal_01x03", "J2", "forsyning", FP["TERM3"],
               55, 130, 0, {"1": "+20V", "2": "+15V", "3": "GND"},
               {"+20V", "+15V", "GND"}, proj, root)
    for ref, fp in ASSIGN["exp3a/drive_circuit.kicad_sch"].items():
        assert set_footprint(t, ref, fp), f"drive: {ref} ikke fundet"
    save(f, t); print("wrote", f)

def do_feedback():
    f = HERE / "exp3a/feedback_circuit.kicad_sch"
    t = load(f); proj, root = project_of(t), root_of(t)
    add_symbol(t, "Connector_Generic:Conn_01x03", "J1", "ind + forsyning", FP["HDR3"],
               40, 130, 0, {"1": "INPUT", "2": "+5V", "3": "GND"},
               {"INPUT", "+5V", "GND"}, proj, root)
    add_symbol(t, "Connector_Generic:Conn_01x02", "J2", "FB ud", FP["HDR2"],
               60, 130, 0, {"1": "FB_OUT", "2": "GND"}, {"FB_OUT", "GND"}, proj, root)
    for ref, fp in ASSIGN["exp3a/feedback_circuit.kicad_sch"].items():
        assert set_footprint(t, ref, fp), f"feedback: {ref} ikke fundet"
    save(f, t); print("wrote", f)

def do_buck():
    f = HERE / "converters/design/buck.kicad_sch"
    t = load(f); proj, root = project_of(t), root_of(t)
    remove_symbol(t, "V_in")            # nettene VIN_15V/GND har egne labels
    remove_symbol(t, "Rload")           # VOUT_5V/GND ligesaa
    add_symbol(t, "Connector:Screw_Terminal_01x02", "J1", "V1 ind (15V)", FP["TERM2"],
               60, 117, 0, {"1": "VIN_15V", "2": "GND"}, set(), proj, root)
    add_symbol(t, "Connector:Screw_Terminal_01x02", "J2", "5V ud", FP["TERM2"],
               170, 117, 180, {"1": "VOUT_5V", "2": "GND"}, set(), proj, root)
    add_symbol(t, "Connector_Generic:Conn_01x02", "J3", "PWM (isoleret)", FP["HDR2"],
               60, 140, 0, {"1": "PWM", "2": "GND_MCU"}, {"PWM", "GND_MCU"}, proj, root)
    add_symbol(t, "Connector_Generic:Conn_01x02", "J4", "gate-forsyning", FP["HDR2"],
               80, 140, 0, {"1": "+12V_SW", "2": "SW"}, {"+12V_SW"}, proj, root)
    for ref, fp in ASSIGN["converters/design/buck.kicad_sch"].items():
        assert set_footprint(t, ref, fp), f"buck: {ref} ikke fundet"
    save(f, t); print("wrote", f)

def do_boost():
    f = HERE / "converters/design/boost.kicad_sch"
    t = load(f); proj, root = project_of(t), root_of(t)
    # de to V_in/Rload-knuder er ULABELEDE i boost -> navngiv dem foerst,
    # paa wire-endepunkter der bliver staaende (L1.1- og C1.1-pinden)
    l1 = pin_pos(t, "L1", "1"); c1 = pin_pos(t, "C1", "1")
    label_at(t, "VIN_5V", *l1)
    label_at(t, "VOUT_V2", *c1)
    remove_symbol(t, "V_in")
    remove_symbol(t, "Rload")
    add_symbol(t, "Connector:Screw_Terminal_01x02", "J1", "lager ind (5V)", FP["TERM2"],
               60, 117, 0, {"1": "VIN_5V", "2": "GND"}, {"GND"}, proj, root)
    add_symbol(t, "Connector:Screw_Terminal_01x02", "J2", "V2 ud (10V)", FP["TERM2"],
               170, 117, 180, {"1": "VOUT_V2", "2": "GND"}, {"GND"}, proj, root)
    add_symbol(t, "Connector_Generic:Conn_01x02", "J3", "PWM (isoleret)", FP["HDR2"],
               60, 140, 0, {"1": "PWM", "2": "GND_MCU"}, {"PWM", "GND_MCU"}, proj, root)
    add_symbol(t, "Connector_Generic:Conn_01x02", "J4", "gate-forsyning", FP["HDR2"],
               80, 140, 0, {"1": "+12V", "2": "GND"}, {"+12V", "GND"}, proj, root)
    for ref, fp in ASSIGN["converters/design/boost.kicad_sch"].items():
        assert set_footprint(t, ref, fp), f"boost: {ref} ikke fundet"
    save(f, t); print("wrote", f)

if __name__ == "__main__":
    boards = sys.argv[1:] or ["drive", "feedback", "buck", "boost"]
    for b in boards:
        {"drive": do_drive, "feedback": do_feedback,
         "buck": do_buck, "boost": do_boost}[b]()
