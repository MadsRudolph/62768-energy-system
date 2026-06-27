#!/usr/bin/env python3
"""
Assign footprints to the top-level symbols in system/system.kicad_sch.

Targeted patch (the top sheet is GUI-owned now): loads the schematic, sets the
Footprint property value on the 28 top-level symbols by reference, writes it back.
Does NOT touch the sub-sheet boards or any other element.

Run with KiCad CLOSED (file lock), then reopen in KiCad.
"""
from pathlib import Path
import re, sys
sys.path.insert(0, str(Path(__file__).parent))
import sexpdata
from sexpdata import Symbol as S

SCH = Path(__file__).parents[1] / "system" / "system.kicad_sch"

TERM2 = "TerminalBlock:TerminalBlock_bornier-2_P5.08mm"
TERM3 = "TerminalBlock:TerminalBlock_bornier-3_P5.08mm"
HDR6  = "Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical"
HDR7  = "Connector_PinHeader_2.54mm:PinHeader_1x07_P2.54mm_Vertical"
HDR1  = "Connector_PinHeader_2.54mm:PinHeader_1x01_P2.54mm_Vertical"
RAX   = "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal"

# match by reference PREFIX (annotation renumbered to <prefix><sheet*100+n>)
PREFIX_FP = {
    "J_3PH": TERM3,
    "J_5V": TERM2, "J_15V": TERM2, "J_LOAD": TERM2, "J_STO": TERM2, "J_PV": TERM2, "J_MOT": TERM2,
    "J_ARD": HDR6, "J_INA": HDR6, "J_C2K": HDR7,
    "R_STAR": RAX,
    "TP": HDR1,
}

def prop(sym, name):
    for c in sym:
        if isinstance(c, list) and c and isinstance(c[0], S) and c[0].value() == "property" \
                and len(c) > 2 and c[1] == name:
            return c
    return None

def fp_for(ref):
    # longest matching prefix wins (so J_5V doesn't match a hypothetical J_5)
    for p in sorted(PREFIX_FP, key=len, reverse=True):
        if ref.startswith(p):
            return PREFIX_FP[p]
    return None

tree = sexpdata.loads(SCH.read_text(encoding="utf-8"))
changed = []
for el in tree:
    if not (isinstance(el, list) and el and isinstance(el[0], S) and el[0].value() == "symbol"):
        continue
    refp = prop(el, "Reference")
    if not refp:
        continue
    ref = refp[2]
    fp = fp_for(ref)
    if not fp:
        continue
    fpp = prop(el, "Footprint")
    if fpp is None:
        continue
    if fpp[2] != fp:
        fpp[2] = fp
        changed.append((ref, fp))

SCH.write_text(sexpdata.dumps(tree), encoding="utf-8")
print(f"patched {len(changed)} symbols:")
for ref, fp in sorted(changed):
    print(f"  {ref:12s} -> {fp.split(':')[-1]}")
