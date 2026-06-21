"""Reassign Device:Q_NMOS MOSFETs from the numbered TO-220 footprint to the _GDS
variant (so symbol pins G/D/S match footprint pads in the KiCad GUI). Only touches
symbols whose lib_id is Device:Q_NMOS and whose Footprint is the plain numbered
TO-220 LaserPads. Leaves regulators (numbered pins) alone.
Usage: py -3.13 _reassign_mosfet_fp.py <file.kicad_sch> [...more files]
"""
import sys, re

OLD = "energy_system:TO-220-3_Vertical_LaserPads"
NEW = "energy_system:TO-220-3_Vertical_LaserPads_GDS"


def match_block(s, start):
    depth = 0; i = start; instr = False; esc = False
    while i < len(s):
        c = s[i]
        if instr:
            if esc: esc = False
            elif c == "\\": esc = True
            elif c == '"': instr = False
        else:
            if c == '"': instr = True
            elif c == "(": depth += 1
            elif c == ")":
                depth -= 1
                if depth == 0:
                    return i + 1
        i += 1
    raise ValueError("unbalanced")


for path in sys.argv[1:]:
    s = open(path, "r", encoding="utf8", newline="").read()
    out = []
    idx = 0
    changed = []
    while True:
        j = s.find("\n\t(symbol", idx)
        if j == -1:
            break
        paren = s.find("(", j)
        end = match_block(s, paren)
        block = s[paren:end]
        idx = end
        is_nmos = '(lib_id "Device:Q_NMOS")' in block
        ref_m = re.search(r'\(property "Reference" "([^"]+)"', block)
        ref = ref_m.group(1) if ref_m else "?"
        # only rewrite the Footprint property value, and only for Q_NMOS using OLD
        fp_old = f'(property "Footprint" "{OLD}"'
        if is_nmos and fp_old in block:
            new_block = block.replace(fp_old, f'(property "Footprint" "{NEW}"')
            s = s[:paren] + new_block + s[end:]
            # recompute idx because length changed
            idx = paren + len(new_block)
            changed.append(ref)
    open(path, "w", encoding="utf8", newline="").write(s)
    print(f"{path}: reassigned {changed or 'none'}")
