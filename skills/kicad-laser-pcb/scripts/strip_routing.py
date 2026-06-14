#!/usr/bin/env python3
"""Fjerner AL routing fra et board (baner, vias, kobber-refdes-tekst og
no-net laser-zoner) men beholder footprints/placering. Bruges naar et
haandlagt board skal genroutes med to-trins-flowet.

Goeres TEKSTUELT med sexpdata - in-process Remove() i pcbnew krasjer KiCad
9.0.6's python med access violation.

Brug: py -3.13 strip_routing.py <board>.kicad_pcb   (eller route_board.ps1 -KeepPlacement)
"""
import sys
import sexpdata
from sexpdata import Symbol as S
from pathlib import Path

def head(it):
    return it[0].value() if isinstance(it, list) and it and isinstance(it[0], S) else None

def has(it, key, value=None):
    for c in it:
        if isinstance(c, list) and c and isinstance(c[0], S) and c[0].value() == key:
            if value is None or (len(c) > 1 and c[1] == value):
                return True
    return False

def main(path):
    t = sexpdata.loads(Path(path).read_text(encoding="utf-8"))
    removed = {"segment": 0, "via": 0, "zone": 0, "gr_text": 0}
    keep = []
    for it in t:
        h = head(it)
        if h in ("segment", "via"):
            removed[h] += 1
            continue
        if h == "zone" and has(it, "net", 0):          # kun no-net laser-zoner
            removed["zone"] += 1
            continue
        if h == "gr_text" and (has(it, "layer", "F.Cu") or has(it, "layer", "B.Cu")):
            removed["gr_text"] += 1
            continue
        keep.append(it)
    Path(path).write_text(sexpdata.dumps(keep), encoding="utf-8")
    print(f"strip_routing: {removed['segment']} segmenter, {removed['via']} vias, "
          f"{removed['zone']} zoner, {removed['gr_text']} kobber-tekster fjernet")

if __name__ == "__main__":
    main(sys.argv[1])
