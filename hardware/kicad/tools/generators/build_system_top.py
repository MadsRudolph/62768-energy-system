#!/usr/bin/env python3
"""
System top sheet — connected 5-board hierarchy for the integrated double-sided PCB.

Builds hardware/kicad/system/system.kicad_sch with:
  - 5 hierarchical sheets (one per board), pins = the hierarchical labels placed by hand
  - connectivity purely by GLOBAL LABELS (schbuild philosophy): each sheet pin gets a
    short wire stub + a global label = the contract net, so buses connect by name
  - J_ARD (Arduino Nano), J_C2K (C2000 LaunchPad), PV INA219 header
  - external screw terminals (3-phase, motor, PV, store, load, +15V gate, +5V)
  - diagnostic probe points (1-pin headers) on the key nets
  - PWR_FLAGs on externally-fed rails, and the single GND<->GND_MCU star tie (0R)

Contract: docs/superpowers/specs/2026-06-27-system-integrated-pcb-interface-contract.md
Run:  py -3.13 tools/generators/build_system_top.py    then ERC with KiCad 10 CLI.
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parents[1]))
import schbuild as sb
from sexpdata import Symbol as S, dumps

PROJECT = "system"
ROOT = sb.uid()
OUT = Path(__file__).parents[2] / "boards"   # placeholder, fixed below
OUT = Path(__file__).parents[2] / "system" / "system.kicad_sch"

# ---- the 5 boards: (sheetname, relative file, [(pin, type)]) ----
IN, OUT_, BI, PAS = "input", "output", "bidirectional", "passive"
SHEETS = [
    ("Motor Power", "../boards/motor_power/motor_power.kicad_sch", [
        ("PWM_MOTOR", IN), ("PWM_MOTOR_ALT", IN), ("MOTOR_A", OUT_), ("MOTOR_B", OUT_),
        ("3PH_U", BI), ("3PH_V", BI), ("3PH_W", BI), ("V1", OUT_), ("GND", PAS),
        ("+5V_PWR", IN)]),
    ("Motor Feedback", "../boards/motor_feedback/motor_feedback.kicad_sch", [
        ("V1", IN), ("GND", PAS), ("+5V_PWR", IN), ("MCU_V1", OUT_), ("GND_MCU", PAS),
        ("+5V_MCU", IN)]),
    ("MPPT buck", "../boards/mppt_buck/mppt_buck.kicad_sch", [
        ("PV_BUCK_IN", IN), ("STORE", OUT_), ("PWM_MPPT", IN), ("GND_MCU", PAS),
        ("+15V_GATE", IN), ("GND", PAS)]),
    ("Boost", "../boards/boost/boost_v2_mill/boost_v2_mill.kicad_sch", [
        ("STORE", IN), ("LOAD", OUT_), ("PWM_BOOST", IN), ("GND_MCU", PAS),
        ("+15V_GATE", IN), ("GND", PAS)]),
    ("C2000 Feedback", "../boards/c2000_feedback/c2000_feedback.kicad_sch", [
        ("V1", IN), ("LOAD", IN), ("STORE", IN), ("ADC_V1", OUT_), ("ADC_LOAD", OUT_),
        ("ADC_STORE", OUT_), ("+3V3", IN), ("GND", PAS)]),
]

elems = []

def sheet(name, fname, x, y, pins, page):
    """Emit a hierarchical sheet box + pins on the right edge; stub wire + global label each."""
    x, y = sb.snap(x), sb.snap(y)
    w = sb.snap(44.0)
    h = sb.snap(2.54 * (len(pins) + 1))
    sh = [S("sheet"), [S("at"), x, y], [S("size"), w, h],
          [S("stroke"), [S("width"), 0.1524], [S("type"), S("solid")]],
          [S("fill"), [S("color"), 0, 0, 0, 0.0]],
          [S("uuid"), sb.uid()],
          [S("property"), "Sheetname", name, [S("at"), x, y - 0.7, 0],
           [S("effects"), [S("font"), [S("size"), 1.27, 1.27]], [S("justify"), S("left"), S("bottom")]]],
          [S("property"), "Sheetfile", fname, [S("at"), x, y + h + 0.7, 0],
           [S("effects"), [S("font"), [S("size"), 1.27, 1.27]], [S("justify"), S("left"), S("top")]]]]
    for i, (pn, et) in enumerate(pins):
        py = sb.snap(y + 2.54 * (i + 1))
        px = x + w
        sh.append([S("pin"), pn, S(et), [S("at"), px, py, 0], [S("uuid"), sb.uid()],
                   [S("effects"), [S("font"), [S("size"), 1.27, 1.27]], [S("justify"), S("right")]]])
        lx = px + 5.08
        elems.append(sb.wire(px, py, lx, py))
        elems.append(sb.label(pn, lx, py, True))
    sh.append([S("instances"), [S("project"), PROJECT,
               [S("path"), f"/{ROOT}", [S("page"), str(page)]]]])
    return sh

# place the 5 sheets in a column
y = sb.snap(30.0)
for idx, (name, fname, pins) in enumerate(SHEETS):
    elems.append(sheet(name, fname, 30.0, y, pins, idx + 2))
    y = sb.snap(y + 2.54 * (len(pins) + 1) + 12.7)

# ---- top-level symbols (connectors / terminals / probes / flags / star tie) ----
# connectivity is by net label on each pin -> all nets are "global"
HDR = "Connector_Generic:Conn_01x{:02d}"
SCREW = "Connector:Screw_Terminal_01x{:02d}"
TP = "Connector:TestPoint"
RES = "Device:R"
FLG = "power:PWR_FLAG"

comps = [
    # MCU connectors
    {"lib": HDR.format(6), "ref": "J_ARD", "val": "Arduino Nano", "x": 120, "y": 30,
     "nets": {"1": "MCU_V1", "2": "PV_SDA", "3": "PV_SCL", "4": "PWM_MPPT",
              "5": "+5V_PWR", "6": "GND"}},
    {"lib": HDR.format(7), "ref": "J_C2K", "val": "C2000 LaunchPad", "x": 120, "y": 75,
     "nets": {"1": "ADC_V1", "2": "ADC_LOAD", "3": "ADC_STORE", "4": "PWM_MOTOR",
              "5": "PWM_BOOST", "6": "+3V3", "7": "GND"}},
    # PV INA219 breakout header (Vin+ / Vin- / VCC / GND / SDA / SCL)
    {"lib": HDR.format(6), "ref": "J_INA", "val": "PV INA219", "x": 120, "y": 125,
     "nets": {"1": "PV_PLUS", "2": "PV_BUCK_IN", "3": "+5V_PWR", "4": "GND",
              "5": "PV_SDA", "6": "PV_SCL"}},
    # external screw terminals
    {"lib": SCREW.format(3), "ref": "J_3PH", "val": "3-phase in", "x": 175, "y": 30,
     "nets": {"1": "3PH_U", "2": "3PH_V", "3": "3PH_W"}},
    {"lib": SCREW.format(2), "ref": "J_MOT", "val": "DC motor", "x": 175, "y": 55,
     "nets": {"1": "MOTOR_A", "2": "MOTOR_B"}},
    {"lib": SCREW.format(2), "ref": "J_PV", "val": "PV panel", "x": 175, "y": 80,
     "nets": {"1": "PV_PLUS", "2": "GND"}},   # panel return = system GND
    {"lib": SCREW.format(2), "ref": "J_STO", "val": "1F store", "x": 175, "y": 105,
     "nets": {"1": "STORE", "2": "GND"}},
    {"lib": SCREW.format(2), "ref": "J_LOAD", "val": "pulsing load", "x": 175, "y": 130,
     "nets": {"1": "LOAD", "2": "GND"}},
    {"lib": SCREW.format(2), "ref": "J_15V", "val": "+15V gate supply", "x": 175, "y": 155,
     "nets": {"1": "+15V_GATE", "2": "GND"}},
    {"lib": SCREW.format(2), "ref": "J_5V", "val": "+5V supply", "x": 175, "y": 180,
     "nets": {"1": "+5V_PWR", "2": "GND"}},
    # GND <-> GND_MCU single star tie
    {"lib": RES, "ref": "R_STAR", "val": "0R", "x": 220, "y": 200,
     "nets": {"1": "GND", "2": "GND_MCU"}},
]

# diagnostic probe points (1-pin test points)
PROBES = ["V1", "STORE", "LOAD", "+5V_PWR", "+3V3", "+15V_GATE", "GND", "GND_MCU",
          "PWM_MOTOR", "PWM_BOOST", "PWM_MPPT", "ADC_V1", "ADC_LOAD", "ADC_STORE",
          "MCU_V1", "PV_SDA", "PV_SCL"]
px, py = 230.0, 30.0
for i, net in enumerate(PROBES):
    comps.append({"lib": TP, "ref": f"TP{i+1}", "val": net, "x": px, "y": py + i * 9.0,
                  "nets": {"1": net}})

# NB: PWR_FLAGs intentionally NOT added at the top level — every sub-sheet already
# carries its own PWR_FLAG on its power/ground nets, and a second flag on the same net
# trips ERC pin_to_pin (two power outputs). Any top-only rail that ERC reports as
# undriven gets a single flag added back below.

# ---- emit component symbols + their pin stubs/labels (reuse schbuild) ----
libs = []
for c in comps:
    c["x"], c["y"] = sb.snap(c["x"]), sb.snap(c["y"])
    ang, unit = c.get("ang", 0), c.get("unit", 1)
    if c["lib"] not in libs:
        libs.append(c["lib"])
    elems.append(sb.symbol(c["lib"], c["ref"], c["val"], c.get("fp", ""),
                           c["x"], c["y"], ang, unit, list(c["nets"].keys()), ROOT, PROJECT))
    for p, net in c["nets"].items():
        # Anchor the global label directly on the pin connection point. No stub wire:
        # schbuild's center-offset stub heuristic mis-fires on multi-pin vertical
        # connectors (outer pins' vertical offset dominates -> vertical stub lands on
        # the neighbouring pin -> shorts adjacent pins). A label on the pin endpoint
        # connects to exactly that one pin; the global NAME does the cross-net wiring.
        ex, ey = sb.pin_xy(c["lib"], p, c["x"], c["y"], ang, unit)
        elems.append(sb.label(net, ex, ey, True))

# ---- assemble tree ----
libsyms = [S("lib_symbols")] + [sb.extract(l) for l in libs]
sheet_inst = [S("sheet_instances"), [S("path"), "/", [S("page"), "1"]]]
tree = [S("kicad_sch"), [S("version"), 20250114], [S("generator"), "eeschema"],
        [S("generator_version"), "9.0"], [S("uuid"), ROOT], [S("paper"), "A2"], libsyms,
        *elems, sheet_inst, [S("embedded_fonts"), S("no")]]
OUT.write_text(dumps(tree), encoding="utf-8")
print("wrote", OUT)
print(f"{len(SHEETS)} sheets, {len(comps)} top-level symbols, {len(PROBES)} probe points")
