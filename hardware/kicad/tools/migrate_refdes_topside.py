#!/usr/bin/env python3
"""Engangs-migrering: flyt kobber-refdes-teksterne fra B.Cu til F.Cu (oversiden).

Goeres TEKSTUELT med sexpdata fordi in-process Remove()+refill krasjer KiCad
9.0.6's python (access violation). Zonerne refilles bagefter i en REN pcbnew-
session (tools/refill_zones.py).

Brug: py -3.13 tools/migrate_refdes_topside.py boards/<b>/<b>.kicad_pcb
"""
import sys
import sexpdata
from sexpdata import Symbol as S
from pathlib import Path

def main(path):
    t = sexpdata.loads(Path(path).read_text(encoding="utf-8"))
    moved = 0
    for it in t:
        if not (isinstance(it, list) and it and isinstance(it[0], S)
                and it[0].value() == "gr_text"):
            continue
        on_bcu = False
        for c in it:
            if isinstance(c, list) and c and isinstance(c[0], S) \
                    and c[0].value() == "layer" and c[1] == "B.Cu":
                c[1] = "F.Cu"
                on_bcu = True
        if not on_bcu:
            continue
        for c in it:
            if isinstance(c, list) and c and isinstance(c[0], S) \
                    and c[0].value() == "effects":
                for j in [j for j in c if isinstance(j, list) and j
                          and isinstance(j[0], S) and j[0].value() == "justify"]:
                    while S("mirror") in j:
                        j.remove(S("mirror"))
                    if len(j) == 1:          # tom (justify) -> fjern helt
                        c.remove(j)
        moved += 1
    Path(path).write_text(sexpdata.dumps(t), encoding="utf-8")
    print(f"{path}: {moved} tekster flyttet B.Cu -> F.Cu")

if __name__ == "__main__":
    main(sys.argv[1])
