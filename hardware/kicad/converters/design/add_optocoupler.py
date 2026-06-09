#!/usr/bin/env python3
"""
Inject an isolated optocoupler gate-drive block into an existing converter
schematic (preserves the hand-drawn layout). KiCad 9 / sexpdata.

Gate drive (non-inverting, galvanically isolated):
    PWM (MCU) -> R1 330 -> 4N25 LED -> GND_MCU        (logic side)
    4N25 transistor: collector -> +12V, emitter -> GATE
    R2 10k: GATE -> GND  (gate pulldown to the switch reference)

Usage: py -3.13 add_optocoupler.py <schematic.kicad_sch> <gate_ref_net>
       gate_ref_net = GND for a low-side switch (boost),
                      SW  for a high-side switch (buck, floating drive).
"""
import sys
import copy
import uuid as _uuid
from pathlib import Path
import sexpdata
from sexpdata import Symbol as S

ISO_LIB = Path(r"C:\Program Files\KiCad\9.0\share\kicad\symbols\Isolator.kicad_sym")

PIN_OFF = {
    "Device:R":       {"1": (0, 3.81), "2": (0, -3.81)},
    "Isolator:4N25":  {"1": (-7.62, 2.54), "2": (-7.62, -2.54), "3": (-5.08, 0),
                       "4": (7.62, -2.54), "5": (7.62, 0), "6": (7.62, 2.54)},
}


def uid():
    return str(_uuid.uuid4())


def pin_xy(lib, pin, x, y):
    px, py = PIN_OFF[lib][pin]
    return (round(x + px, 2), round(y - py, 2))


def extract_lib_symbol(name):
    t = sexpdata.loads(ISO_LIB.read_text(encoding="utf-8"))
    for it in t:
        if isinstance(it, list) and len(it) > 1 and isinstance(it[0], S) \
                and it[0].value() == "symbol" and it[1] == name:
            s = copy.deepcopy(it)
            s[1] = f"Isolator:{name}"
            return s
    raise ValueError(name)


def _prop(name, value, x, y, hide=False):
    p = [S("property"), name, str(value), [S("at"), x, y, 0],
         [S("effects"), [S("font"), [S("size"), 1.27, 1.27]]]]
    if hide:
        p[4].append(S("hide"))
    return p


def make_symbol(lib_id, ref, value, x, y, pins, root_uuid):
    sym = [S("symbol"), [S("lib_id"), lib_id], [S("at"), x, y, 0], [S("unit"), 1],
           [S("exclude_from_sim"), S("no")], [S("in_bom"), S("yes")],
           [S("on_board"), S("yes")], [S("dnp"), S("no")], [S("uuid"), uid()],
           _prop("Reference", ref, x + 2.54, y - 7.62),
           _prop("Value", value, x + 2.54, y + 7.62),
           _prop("Footprint", "", x, y, hide=True),
           _prop("Datasheet", "", x, y, hide=True),
           _prop("Description", "", x, y, hide=True)]
    for pn in pins:
        sym.append([S("pin"), str(pn), [S("uuid"), uid()]])
    sym.append([S("instances"), [S("project"), "energy_system",
                [S("path"), f"/{root_uuid}", [S("reference"), ref], [S("unit"), 1]]]])
    return sym


def make_wire(x1, y1, x2, y2):
    return [S("wire"), [S("pts"), [S("xy"), x1, y1], [S("xy"), x2, y2]],
            [S("stroke"), [S("width"), 0], [S("type"), S("default")]], [S("uuid"), uid()]]


def make_label(name, x, y):
    return [S("label"), name, [S("at"), x, y, 0],
            [S("effects"), [S("font"), [S("size"), 1.27, 1.27]],
             [S("justify"), S("left"), S("bottom")]], [S("uuid"), uid()]]


def make_glabel(name, x, y):
    return [S("global_label"), name, [S("shape"), S("input")], [S("at"), x, y, 0],
            [S("effects"), [S("font"), [S("size"), 1.27, 1.27]], [S("justify"), S("left")]],
            [S("uuid"), uid()],
            [S("property"), "Intersheetrefs", "${INTERSHEET_REFS}", [S("at"), 0, 0, 0],
             [S("effects"), [S("font"), [S("size"), 1.27, 1.27]], [S("hide"), S("yes")]]]]


def make_noconnect(x, y):
    return [S("no_connect"), [S("at"), x, y], [S("uuid"), uid()]]


def kids(n, k):
    return [c for c in n if isinstance(c, list) and c and isinstance(c[0], S) and c[0].value() == k]


def inject(path, gate_ref, supply="+12V"):
    tree = sexpdata.loads(Path(path).read_text(encoding="utf-8"))
    root_uuid = kids(tree, "uuid")[0][1]
    libsyms = kids(tree, "lib_symbols")[0]
    have = {c[1] for c in kids(libsyms, "symbol")}
    if "Isolator:4N25" not in have:
        libsyms.append(extract_lib_symbol("4N25"))

    # placements (on 1.27 mm grid)
    U, R1, R2 = (109.22, 144.78), (93.98, 137.16), (116.84, 153.67)
    elems = []
    elems.append(make_symbol("Isolator:4N25", "U1", "4N25", U[0], U[1],
                             ["1", "2", "3", "4", "5", "6"], root_uuid))
    elems.append(make_symbol("Device:R", "R1", "330", R1[0], R1[1], ["1", "2"], root_uuid))
    elems.append(make_symbol("Device:R", "R2", "10k", R2[0], R2[1], ["1", "2"], root_uuid))

    def stub(lib, ref_xy, pin, dx, dy, net, glob=False):
        ex, ey = pin_xy(lib, pin, *ref_xy)
        sx, sy = round(ex + dx, 2), round(ey + dy, 2)
        elems.append(make_wire(ex, ey, sx, sy))
        elems.append((make_glabel if glob else make_label)(net, sx, sy))

    # optocoupler
    stub("Isolator:4N25", U, "1", -2.54, 0, "OPTO_LED")
    stub("Isolator:4N25", U, "2", -2.54, 0, "GND_MCU", glob=True)
    stub("Isolator:4N25", U, "5", 2.54, 0, supply, glob=True)
    stub("Isolator:4N25", U, "4", 2.54, 0, "GATE", glob=True)
    ex, ey = pin_xy("Isolator:4N25", "6", *U)            # base -> no-connect
    elems.append(make_noconnect(ex, ey))
    # R1: PWM -> OPTO_LED
    stub("Device:R", R1, "1", 0, -2.54, "PWM", glob=True)
    stub("Device:R", R1, "2", 0, 2.54, "OPTO_LED")
    # R2: GATE -> gate_ref (GND for low-side, SW for high-side)
    stub("Device:R", R2, "1", 0, -2.54, "GATE", glob=True)
    stub("Device:R", R2, "2", 0, 2.54, gate_ref)

    # name the converter reference rail (label dropped on an existing wire point)
    if len(sys.argv) > 3 and sys.argv[3] not in ("", "-", "none"):
        gx, gy = (float(v) for v in sys.argv[3].split(","))
        elems.append(make_label(gate_ref, gx, gy))

    # insert before sheet_instances
    idx = next(i for i, c in enumerate(tree)
               if isinstance(c, list) and c and isinstance(c[0], S) and c[0].value() == "sheet_instances")
    tree[idx:idx] = elems
    Path(path).write_text(sexpdata.dumps(tree), encoding="utf-8")
    print(f"injected optocoupler into {path}  (gate pulldown -> {gate_ref})")


if __name__ == "__main__":
    gr = sys.argv[2] if len(sys.argv) > 2 else "GND"
    sup = sys.argv[4] if len(sys.argv) > 4 else "+12V"
    inject(sys.argv[1], gr, sup)
