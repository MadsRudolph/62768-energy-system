#!/usr/bin/env python3
"""Genererer system/system.kicad_sch - det STORE hovedskema hvor alle 7
board-skemaer ligger som hierarkiske sheets, arrangeret efter energiflowet
(docs/system-architecture.md). Grafiske pile + tekst viser kabel-
forbindelserne mellem boards (skrueterminal til skrueterminal).

OBS: projektet er til navigation/overblik/print - hvert board har stadig sit
eget projekt som source of truth for sin PCB. Globale labels (GND, PWM, GATE)
deles paa tvaers af sheets i KiCads oejne; PWM/GATE er reelt separate signaler
pr. board, saa lav ALDRIG netliste/PCB fra dette projekt.

Brug: py -3.13 tools/build_system_sch.py
"""
import json
import uuid
from pathlib import Path

OUT = Path(__file__).parent.parent / "system"
OUT.mkdir(exist_ok=True)

def u():
    return str(uuid.uuid4())

# (navn, fil, x, y, bredde, hoejde) - A3 420x297, flow venstre->hoejre
SHEETS = [
    ("Motor-drive",   "drive_circuit",    30,  40, 50, 25),
    ("Rectifier",     "rectifier",       140,  40, 50, 25),
    ("Buck",          "buck",            250,  40, 50, 25),
    ("MPPT + PV",     "mppt",             30, 120, 50, 25),
    ("Boost",         "boost",           250, 120, 50, 25),
    ("Feedback",      "feedback_circuit", 30, 200, 50, 25),
    ("Current sense", "current_sense",   140, 200, 50, 25),
]

def sheet(name, board, x, y, w, h):
    return f'''  (sheet (at {x} {y}) (size {w} {h})
    (stroke (width 0.1524) (type solid))
    (fill (color 0 0 0 0.0000))
    (uuid "{u()}")
    (property "Sheetname" "{name}" (at {x} {y - 0.8} 0)
      (effects (font (size 2 2) (bold yes)) (justify left bottom)))
    (property "Sheetfile" "../boards/{board}/{board}.kicad_sch" (at {x} {y + h + 0.8} 0)
      (effects (font (size 1.27 1.27)) (justify left top)))
  )'''

def line(pts, width=0.4):
    p = " ".join(f"(xy {x} {y})" for x, y in pts)
    return (f'  (polyline (pts {p}) '
            f'(stroke (width {width}) (type solid)) (uuid "{u()}"))')

def arrow(pts):
    """Polylinje + pilespids paa sidste segment."""
    (x1, y1), (x2, y2) = pts[-2], pts[-1]
    import math
    a = math.atan2(y2 - y1, x2 - x1)
    s = 2.5
    h1 = (x2 - s * math.cos(a - 0.45), y2 - s * math.sin(a - 0.45))
    h2 = (x2 - s * math.cos(a + 0.45), y2 - s * math.sin(a + 0.45))
    return "\n".join([line(pts),
                      line([h1, (x2, y2)]),
                      line([h2, (x2, y2)])])

def text(s, x, y, size=1.8, bold=False):
    b = " (bold yes)" if bold else ""
    return (f'  (text "{s}" (exclude_from_sim no) (at {x} {y} 0) '
            f'(effects (font (size {size} {size}){b}) (justify left bottom)) (uuid "{u()}"))')

def box(x, y, w, h):
    return (f'  (rectangle (start {x} {y}) (end {x + w} {y + h}) '
            f'(stroke (width 0.6) (type solid)) (fill (type none)) (uuid "{u()}"))')

parts = []
parts.append(f'''(kicad_sch (version 20250114) (generator "eeschema") (generator_version "9.0")
  (uuid "{u()}")
  (paper "A3")
  (title_block
    (title "62768 Electrical Energy Systems - samlet system")
    (date "2026-06-11")
    (comment 1 "Hierarkisk overblik: hvert sheet = et fysisk board (eget KiCad-projekt + PCB)")
    (comment 2 "Pile = kabler mellem skrueterminaler. Lav IKKE netliste/PCB fra dette projekt.")
  )''')

for s in SHEETS:
    parts.append(sheet(*s))

# --- eksterne blokke (ting vi ikke bygger selv) ---
parts.append(box(140, 113, 50, 18))
parts.append(text("DC-motor + AC-generator", 142, 120, 1.6))
parts.append(text("+ 3x transformer (eksterne)", 142, 124, 1.6))
parts.append(box(355, 31, 45, 18))
parts.append(text("1F LAGER", 362, 39, 2.2, bold=True))
parts.append(text("V3 = 5 V", 362, 44, 1.8))
parts.append(box(355, 111, 45, 18))
parts.append(text("PULSERENDE LAST", 357, 119, 1.8, bold=True))
parts.append(text("V2 = 10 V", 362, 124, 1.8))
parts.append(box(250, 196, 60, 24))
parts.append(text("ARDUINO UNO", 262, 204, 2.2, bold=True))
parts.append(text("PID: V1 via motor-PWM", 254, 209, 1.6))
parts.append(text("+ overvaagning (PC)", 254, 213, 1.6))

# --- energiflow (kabler mellem skrueterminaler) ---
# drive -> motor/gen/trafo-blokken (motorkabel)
parts.append(arrow([(80, 52), (110, 52), (110, 122), (140, 122)]))
parts.append(text("motorkabel (M1)", 84, 50.5))
# gen/trafo -> rectifier (3-fase ind i J1)
parts.append(arrow([(165, 113), (165, 65)]))
parts.append(text("3-fase", 167, 90))
# rectifier -> buck (V1)
parts.append(arrow([(190, 52), (250, 52)]))
parts.append(text("V1 = 15 V", 205, 50.5))
# buck -> lager (5 V)
parts.append(arrow([(300, 52), (327, 52), (327, 40), (355, 40)]))
parts.append(text("5 V", 332, 38.5))
# mppt -> lager (V3, PV bruges foerst)
parts.append(arrow([(80, 132), (95, 132), (95, 95), (370, 95), (370, 49)]))
parts.append(text("V3 (PV-energi bruges foerst)", 130, 93.5))
# lager -> boost (5 V ind)
parts.append(arrow([(390, 49), (390, 80), (230, 80), (230, 132), (250, 132)]))
parts.append(text("5 V fra lager", 240, 78.5))
# boost -> pulserende last (V2)
parts.append(arrow([(300, 132), (327, 132), (327, 120), (355, 120)]))
parts.append(text("V2 = 10 V", 305, 130.5))
# feedback + current sense -> Arduino ADC
parts.append(arrow([(190, 208), (250, 208)]))
parts.append(arrow([(55, 225), (55, 232), (235, 232), (235, 216), (250, 216)]))
parts.append(text("ADC", 215, 206.5))
# Arduino -> motor-drive (PWM, PID-sloejfen der regulerer V1)
parts.append(arrow([(280, 196), (280, 170), (15, 170), (15, 52), (30, 52)]))
parts.append(text("PWM (PID regulerer V1 via motorfart)", 60, 168.5))
# sense-indgange (graa note)
parts.append(text("Feedback/current sense maaler V1, V2, V3 + gren-stroemme", 250, 226, 1.5))

content = "\n".join(parts) + f'\n  (sheet_instances (path "/" (page "1")))\n)\n'
(OUT / "system.kicad_sch").write_text(content, encoding="utf-8")

pro = OUT / "system.kicad_pro"
if not pro.exists():
    pro.write_text(json.dumps({
        "meta": {"filename": "system.kicad_pro", "version": 3},
        "project": {"files": []},
    }, indent=2), encoding="utf-8")
print("wrote", OUT / "system.kicad_sch")
