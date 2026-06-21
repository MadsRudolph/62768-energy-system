"""Patch an existing .kicad_pro to the fiber-laser netclass (track 1.0mm, clearance
0.8mm) so GUI hand-routing and reloaded-board DSN export don't fall back to 0.2mm.
Mirrors the net_settings/board.rules that pcb_build.py writes for a fresh board.
Preserves everything else in the .kicad_pro.
Usage: py -3.13 _set_laser_netclass.py <file.kicad_pro>
"""
import json, sys

path = sys.argv[1]
d = json.load(open(path, encoding="utf-8"))

board = d.setdefault("board", {})
ds = board.setdefault("design_settings", {})
rules = ds.setdefault("rules", {})
rules["min_clearance"] = 0.0
rules["min_track_width"] = 0.8
rules["min_copper_edge_clearance"] = 0.5

ns = d.setdefault("net_settings", {})
classes = ns.setdefault("classes", [])
default = None
for c in classes:
    if c.get("name") == "Default":
        default = c
        break
if default is None:
    default = {"name": "Default"}
    classes.append(default)
default.update({
    "clearance": 0.8,
    "track_width": 1.0,
    "via_diameter": 1.6,
    "via_drill": 0.8,
})

json.dump(d, open(path, "w", encoding="utf-8"), indent=2)
print(f"{path}: Default netclass -> track 1.0 / clearance 0.8, board rules set")
