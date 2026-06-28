#!/usr/bin/env python3
"""Remove ALL routing from a board (segments, vias, every zone, and copper-layer
text) but keep footprints + placement. Textual via sexpdata -- in-process pcbnew
Remove() corrupts KiCad's SWIG iterators. Unlike strip_routing.py this drops zones
of EVERY net (the GND pour included), so route_prep.py can re-pour from a clean slate
without calling the crash-prone board.Remove() on existing zones.

  py -3.13 tools/strip_all_routing.py <board.kicad_pcb>
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import sexpdata
from sexpdata import Symbol as S

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
        if h in ("segment", "via", "zone"):
            removed[h] += 1
            continue
        if h == "gr_text" and (has(it, "layer", "F.Cu") or has(it, "layer", "B.Cu")):
            removed["gr_text"] += 1
            continue
        keep.append(it)
    Path(path).write_text(sexpdata.dumps(keep), encoding="utf-8")
    print(f"stripped: {removed['segment']} segments, {removed['via']} vias, "
          f"{removed['zone']} zones, {removed['gr_text']} copper texts")

if __name__ == "__main__":
    main(sys.argv[1])
