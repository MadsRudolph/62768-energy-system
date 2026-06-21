"""Format-agnostic: for one component <ref>, change its Footprint from the plain
TO-220 LaserPads to the _GDS variant. Anchors on the Reference property, then the next
Footprint property (guarding that no other Reference sits in between, so it's this
component's). Works on single-line (old KiCad 9) and multi-line files.
Usage: py -3.13 _set_mosfet_gds.py <file.kicad_sch> <REF>
"""
import sys

path, ref = sys.argv[1], sys.argv[2]
PLAIN = '(property "Footprint" "energy_system:TO-220-3_Vertical_LaserPads"'
GDSv = '(property "Footprint" "energy_system:TO-220-3_Vertical_LaserPads_GDS"'
s = open(path, "r", encoding="utf8", newline="").read()

anchor = f'(property "Reference" "{ref}"'
i = s.find(anchor)
if i == -1:
    print(f"{path}: ref {ref} not found"); sys.exit(0)
j = s.find(PLAIN, i)
if j == -1:
    print(f"{path}: {ref} not on plain TO-220 footprint (already fixed?)"); sys.exit(0)
between = s[i + len(anchor):j]
if '(property "Reference"' in between:
    print(f"{path}: refused - next plain footprint after {ref} belongs to another symbol")
    sys.exit(1)
s = s[:j] + GDSv + s[j + len(PLAIN):]
open(path, "w", encoding="utf8", newline="").write(s)
print(f"{path}: {ref} -> GDS")
