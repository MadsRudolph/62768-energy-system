#!/usr/bin/env python3
"""kicadsexpr-netliste -> simpel JSON til pcb_build.py (KiCads python har ikke sexpdata).
Brug: py -3.13 pcb_netlist_json.py netliste.net ud.json"""
import json, sys
import sexpdata
from sexpdata import Symbol as S
from pathlib import Path

def val(c): return c.value() if isinstance(c, S) else c

def main(netf, outf):
    t = sexpdata.loads(Path(netf).read_text(encoding="utf-8"))
    comps, nets = {}, []
    for it in t:
        if not (isinstance(it, list) and it and isinstance(it[0], S)):
            continue
        if it[0].value() == "components":
            for c in it[1:]:
                ref = value = fp = None
                for f in c:
                    if isinstance(f, list) and f and isinstance(f[0], S):
                        k = f[0].value()
                        if k == "ref": ref = f[1]
                        elif k == "value": value = str(f[1])
                        elif k == "footprint": fp = f[1]
                if ref and not ref.startswith("#"):
                    comps[ref] = {"ref": ref, "value": value, "footprint": fp, "pads": {}}
        elif it[0].value() == "nets":
            for net in it[1:]:
                name = None; nodes = []
                for f in net:
                    if isinstance(f, list) and f and isinstance(f[0], S):
                        if f[0].value() == "name": name = f[1]
                        elif f[0].value() == "node":
                            ref = pin = None
                            for g in f:
                                if isinstance(g, list) and g and isinstance(g[0], S):
                                    if g[0].value() == "ref": ref = g[1]
                                    elif g[0].value() == "pin": pin = str(g[1])
                            nodes.append((ref, pin))
                if name and not name.startswith("unconnected-"):
                    nets.append(name)
                    for ref, pin in nodes:
                        if ref in comps:
                            comps[ref]["pads"][pin] = name
    Path(outf).write_text(json.dumps(
        {"components": list(comps.values()), "nets": nets}, indent=1), encoding="utf-8")
    print(f"{outf}: {len(comps)} komponenter, {len(nets)} net")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
