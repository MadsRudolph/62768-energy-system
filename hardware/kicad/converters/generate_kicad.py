#!/usr/bin/env python3
"""
KiCad 9 schematic generator for the 62768 buck & boost converters.

Builds clean, connected schematics from scratch using sexpdata, following the
proven kicad-skip / sexpdata pattern (KiCad 9.0, version 20250114). Components
are placed on an explicit left-to-right grid; connectivity is by local net
labels placed exactly on each pin endpoint (no fragile wire routing).

The switch is a real N-MOSFET symbol (Q_NMOS -> IRF540N), the freewheel/output
diode a Schottky (D_Schottky -> 1N5819) -- matching the discrete build (Krav 9).

Run:   py -3.13 generate_kicad.py
Open:  buck.kicad_sch / boost.kicad_sch in KiCad 9.
"""
import copy
import uuid as _uuid
from pathlib import Path

import sexpdata
from sexpdata import Symbol as S

KICAD_LIB = Path(r"C:\Program Files\KiCad\9.0\share\kicad\symbols")
DEVICE_LIB = KICAD_LIB / "Device.kicad_sym"
OUT_DIR = Path(__file__).parent

# pin endpoint offsets (lib Y-up); schematic endpoint at 0deg = (x+px, y-py)
PIN_OFF = {
    "Device:R":           {"1": (0, 3.81),  "2": (0, -3.81)},
    "Device:L":           {"1": (0, 3.81),  "2": (0, -3.81)},
    "Device:C_Polarized": {"1": (0, 3.81),  "2": (0, -3.81)},
    "Device:D_Schottky":  {"1": (-3.81, 0), "2": (3.81, 0)},      # 1=K, 2=A
    "Device:Q_NMOS":      {"G": (-5.08, 0), "D": (2.54, 5.08), "S": (2.54, -5.08)},
}
LIB_NAME = {  # lib_id -> symbol name in Device.kicad_sym
    "Device:R": "R", "Device:L": "L", "Device:C_Polarized": "C_Polarized",
    "Device:D_Schottky": "D_Schottky", "Device:Q_NMOS": "Q_NMOS",
}
# direction (dx,dy) of a 2.54 mm wire stub drawn outward from each pin
STUB = {
    "Device:R":           {"1": (0, -2.54), "2": (0, 2.54)},
    "Device:L":           {"1": (0, -2.54), "2": (0, 2.54)},
    "Device:C_Polarized": {"1": (0, -2.54), "2": (0, 2.54)},
    "Device:D_Schottky":  {"1": (-2.54, 0), "2": (2.54, 0)},
    "Device:Q_NMOS":      {"G": (-2.54, 0), "D": (0, -2.54), "S": (0, 2.54)},
}


def uid():
    return str(_uuid.uuid4())


def pin_xy(lib_id, pin, x, y):
    px, py = PIN_OFF[lib_id][pin]
    return (round(x + px, 2), round(y - py, 2))


# ---- library symbol extraction (embed defs into the schematic) ----
def extract_lib_symbol(name):
    tree = sexpdata.loads(DEVICE_LIB.read_text(encoding="utf-8"))
    for it in tree:
        if isinstance(it, list) and len(it) > 1 and isinstance(it[0], S) \
                and it[0].value() == "symbol" and it[1] == name:
            sym = copy.deepcopy(it)
            sym[1] = f"Device:{name}"          # prefix top-level name only
            return sym
    raise ValueError(f"symbol {name} not found")


# ---- S-expression builders (KiCad 9 structure) ----
def _prop(name, value, x, y, hide=False):
    p = [S("property"), name, str(value),
         [S("at"), x, y, 0],
         [S("effects"), [S("font"), [S("size"), 1.27, 1.27]]]]
    if hide:
        p[4].append(S("hide"))
    return p


def make_symbol(lib_id, ref, value, x, y, pins, root_uuid, angle=0):
    sym = [S("symbol"),
           [S("lib_id"), lib_id],
           [S("at"), x, y, angle],
           [S("unit"), 1],
           [S("exclude_from_sim"), S("no")],
           [S("in_bom"), S("yes")],
           [S("on_board"), S("yes")],
           [S("dnp"), S("no")],
           [S("uuid"), uid()],
           _prop("Reference", ref, x + 5, y - 2.54),
           _prop("Value", value, x + 5, y + 2.54),
           _prop("Footprint", "", x, y, hide=True),
           _prop("Datasheet", "", x, y, hide=True),
           _prop("Description", "", x, y, hide=True)]
    for pn in pins:
        sym.append([S("pin"), str(pn), [S("uuid"), uid()]])
    sym.append([S("instances"),
                [S("project"), "energy_system",
                 [S("path"), f"/{root_uuid}",
                  [S("reference"), ref], [S("unit"), 1]]]])
    return sym


def make_label(name, x, y, angle=0):
    return [S("label"), name,
            [S("at"), x, y, angle],
            [S("effects"), [S("font"), [S("size"), 1.27, 1.27]],
             [S("justify"), S("left"), S("bottom")]],
            [S("uuid"), uid()]]


# external interface nets (single-endpoint) use global labels so they don't
# read as dangling; pure internal nets stay as plain local labels.
EXTERNAL_NETS = {"VIN_15V", "VIN_5V", "GATE"}


def make_glabel(name, x, y, angle=0):
    return [S("global_label"), name,
            [S("shape"), S("input")],
            [S("at"), x, y, angle],
            [S("effects"), [S("font"), [S("size"), 1.27, 1.27]], [S("justify"), S("left")]],
            [S("uuid"), uid()],
            [S("property"), "Intersheetrefs", "${INTERSHEET_REFS}",
             [S("at"), 0, 0, 0],
             [S("effects"), [S("font"), [S("size"), 1.27, 1.27]], [S("hide"), S("yes")]]]]


def make_wire(x1, y1, x2, y2):
    return [S("wire"),
            [S("pts"), [S("xy"), x1, y1], [S("xy"), x2, y2]],
            [S("stroke"), [S("width"), 0], [S("type"), S("default")]],
            [S("uuid"), uid()]]


def make_text(text, x, y, size=2.0):
    return [S("text"), text,
            [S("at"), x, y, 0],
            [S("effects"), [S("font"), [S("size"), size, size],
                            [S("thickness"), 0.4], S("bold")],
             [S("justify"), S("left")]],
            [S("uuid"), uid()]]


def build(title, comps, out_path):
    """comps: list of dicts {lib, ref, val, x, y, nets:{pin:netname}}"""
    root_uuid = uid()
    elements = []
    libs_used = []
    for c in comps:
        if c["lib"] not in libs_used:
            libs_used.append(c["lib"])
        pins = list(PIN_OFF[c["lib"]].keys())
        elements.append(make_symbol(c["lib"], c["ref"], c["val"],
                                    c["x"], c["y"], pins, root_uuid))
        for pin, net in c["nets"].items():
            ex, ey = pin_xy(c["lib"], pin, c["x"], c["y"])
            dx, dy = STUB[c["lib"]][pin]
            sx, sy = round(ex + dx, 2), round(ey + dy, 2)
            elements.append(make_wire(ex, ey, sx, sy))     # stub off the pin
            if net in EXTERNAL_NETS:
                elements.append(make_glabel(net, sx, sy))  # external I/O port
            else:
                elements.append(make_label(net, sx, sy))   # internal net label
    elements.append(make_text(title, comps[0]["x"] - 5, comps[0]["y"] - 18))

    lib_symbols = [S("lib_symbols")]
    for lib_id in libs_used:
        lib_symbols.append(extract_lib_symbol(LIB_NAME[lib_id]))

    tree = [S("kicad_sch"),
            [S("version"), 20250114],
            [S("generator"), "eeschema"],
            [S("generator_version"), "9.0"],
            [S("uuid"), root_uuid],
            [S("paper"), "A4"],
            lib_symbols,
            *elements,
            [S("sheet_instances"), [S("path"), "/", [S("page"), "1"]]],
            [S("embedded_fonts"), S("no")]]

    out_path.write_text(sexpdata.dumps(tree), encoding="utf-8")
    print("wrote", out_path)


# ======================= BUCK 15V -> 5V =======================
# All origins on a 2.54 mm grid so every pin lands on KiCad's 1.27 mm grid.
buck = [
    {"lib": "Device:Q_NMOS", "ref": "M1", "val": "IRF540N", "x": 88.9, "y": 88.9,
     "nets": {"D": "VIN_15V", "S": "SW", "G": "GATE"}},
    {"lib": "Device:D_Schottky", "ref": "D1", "val": "1N5819", "x": 101.6, "y": 104.14,
     "nets": {"1": "SW", "2": "GND"}},                       # K=SW, A=GND (freewheel)
    {"lib": "Device:L", "ref": "L1", "val": "470u", "x": 114.3, "y": 88.9,
     "nets": {"1": "SW", "2": "VOUT_5V"}},
    {"lib": "Device:C_Polarized", "ref": "C1", "val": "47u", "x": 139.7, "y": 88.9,
     "nets": {"1": "VOUT_5V", "2": "GND"}},
    {"lib": "Device:R", "ref": "Rload", "val": "10", "x": 165.1, "y": 88.9,
     "nets": {"1": "VOUT_5V", "2": "GND"}},
]

# ======================= BOOST 5V -> 15V =======================
boost = [
    {"lib": "Device:L", "ref": "L1", "val": "470u", "x": 88.9, "y": 88.9,
     "nets": {"1": "VIN_5V", "2": "SW"}},
    {"lib": "Device:Q_NMOS", "ref": "M1", "val": "IRF540N", "x": 114.3, "y": 88.9,
     "nets": {"D": "SW", "S": "GND", "G": "GATE"}},          # low-side switch
    {"lib": "Device:D_Schottky", "ref": "D1", "val": "1N5819", "x": 139.7, "y": 88.9,
     "nets": {"1": "VOUT_15V", "2": "SW"}},                  # K=OUT, A=SW (output)
    {"lib": "Device:C_Polarized", "ref": "C1", "val": "47u", "x": 165.1, "y": 88.9,
     "nets": {"1": "VOUT_15V", "2": "GND"}},
    {"lib": "Device:R", "ref": "Rload", "val": "100", "x": 190.5, "y": 88.9,
     "nets": {"1": "VOUT_15V", "2": "GND"}},
]

if __name__ == "__main__":
    build("Buck converter  15V -> 5V   (62768, Krav 8/9)", buck,
          OUT_DIR / "buck.kicad_sch")
    build("Boost converter  5V -> 15V   (62768, Krav 8/9)", boost,
          OUT_DIR / "boost.kicad_sch")
