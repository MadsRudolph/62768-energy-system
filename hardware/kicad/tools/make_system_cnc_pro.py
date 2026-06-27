"""Build hardware/kicad/system/system.kicad_pro with the CNC double-sided netclass.

Derives from the known-good boost_v2_mill project file and rewrites ONLY:
  - the Default netclass (CNC double-sided rules, hand-stitched vias)
  - the DRC rule floors (min track / clearance)
  - identity fields (filename, top-level sheet, plot path)

CNC double-sided rules (SRM-20, 0.8 mm isolation end mill):
  clearance   1.0 mm  (gap >= bit width 0.8 mm, +0.2 mm margin)
  track       1.0 mm
  via pad     2.4 mm / drill 1.0 mm  (hand-stitched rivet/wire, solder both sides)
"""
import json
import os

KICAD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(KICAD, "boards", "boost", "boost_v2_mill", "boost_v2_mill.kicad_pro")
DST = os.path.join(KICAD, "system", "system.kicad_pro")

with open(SRC, "r", encoding="utf-8") as f:
    pro = json.load(f)

# --- Default netclass: CNC double-sided ---
cls = pro["net_settings"]["classes"][0]
cls["clearance"] = 1.0          # copper-to-copper gap >= 0.8 mm bit
cls["track_width"] = 1.0        # min track
cls["via_diameter"] = 2.4       # hand-stitch pad: 0.7 mm annular ring each side
cls["via_drill"] = 1.0          # fits a via rivet / soldered wire

# --- DRC rule floors ---
rules = pro["board"]["design_settings"]["rules"]
rules["min_track_width"] = 1.0
rules["min_clearance"] = 0.9    # hard floor below the 1.0 netclass
rules["min_through_hole_diameter"] = 0.3
rules["min_via_diameter"] = 1.0
rules["min_hole_to_hole"] = 0.5

# --- identity ---
pro["meta"]["filename"] = "system.kicad_pro"
pro["schematic"]["top_level_sheets"] = [
    {"filename": "system.kicad_sch", "name": "system",
     "uuid": "00000000-0000-0000-0000-000000000000"}
]
pro["pcbnew"]["last_paths"]["plot"] = "../../production/system/gerbers/"
pro["pcbnew"]["last_paths"]["specctra_dsn"] = ""

with open(DST, "w", encoding="utf-8") as f:
    json.dump(pro, f, indent=2)
    f.write("\n")

print("wrote", DST)
print("netclass:", {k: cls[k] for k in ("clearance", "track_width", "via_diameter", "via_drill")})
print("floors:", {k: rules[k] for k in ("min_track_width", "min_clearance", "min_via_diameter")})
