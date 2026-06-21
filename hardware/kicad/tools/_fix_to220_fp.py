"""Correct TO-220 LaserPads footprint variant per component so its pads match the
symbol's pin names: letter pins (G/D/S) -> _GDS variant; digit pins (1/2/3) -> plain.
Driven by the board's netlist json (authoritative pin names). Only touches components
already on one of the two TO-220 LaserPads footprints.
Usage: py -3.13 _fix_to220_fp.py <file.kicad_sch> <netlist.json>
"""
import sys, re, json

sch, js = sys.argv[1], sys.argv[2]
pads = {c["ref"]: set(c["pads"].keys()) for c in json.load(open(js))["components"]}

PLAIN = "energy_system:TO-220-3_Vertical_LaserPads"
GDS = "energy_system:TO-220-3_Vertical_LaserPads_GDS"
s = open(sch, "r", encoding="utf8", newline="").read()


def match_block(s, start):
    d = 0; i = start; ins = False; esc = False
    while i < len(s):
        c = s[i]
        if ins:
            if esc: esc = False
            elif c == "\\": esc = True
            elif c == '"': ins = False
        else:
            if c == '"': ins = True
            elif c == "(": d += 1
            elif c == ")":
                d -= 1
                if d == 0: return i + 1
        i += 1


changed = []
idx = 0
while True:
    j = s.find("\n\t(symbol", idx)
    if j == -1:
        break
    p = s.find("(", j); e = match_block(s, p); block = s[p:e]; idx = e
    fpm = re.search(r'\(property "Footprint" "([^"]*)"', block)
    refm = re.search(r'\(property "Reference" "([^"]+)"', block)
    if not (fpm and refm):
        continue
    cur, ref = fpm.group(1), refm.group(1)
    if cur not in (PLAIN, GDS):
        continue
    pn = pads.get(ref, set())
    if pn and all(x.isdigit() for x in pn):
        want = PLAIN
    elif pn and all(not x.isdigit() for x in pn):
        want = GDS
    else:
        continue
    if want != cur:
        nb = block.replace(f'(property "Footprint" "{cur}"',
                           f'(property "Footprint" "{want}"')
        s = s[:p] + nb + s[e:]
        idx = p + len(nb)
        changed.append(f"{ref}:{cur.split(':')[1].split('_Vertical')[1] or 'plain'}->"
                       f"{want.endswith('GDS') and 'GDS' or 'plain'}")
open(sch, "w", encoding="utf8", newline="").write(s)
print(f"{sch}: {changed or 'no change'}")
