"""Compute absolute pin coordinates for every component pin in a .kicad_sch.
For each instance, tries the 8 orthogonal orientation transforms and picks the one
whose pins best coincide with wire endpoints / junctions (validation). Prints a match
rate and any queried pins.
Usage: py -3.13 pinmap.py <file.kicad_sch> [ref.pin ...]
"""
import sys, re
import sexpdata
from sexpdata import Symbol

path = sys.argv[1]
queries = sys.argv[2:]
d = sexpdata.load(open(path, encoding="utf8"))
car = lambda x: x[0] if isinstance(x, list) and x else None


def num(v):
    return float(v.value()) if hasattr(v, "value") else float(v)


# --- lib pins: lib_id -> [(pinnum, px, py)] ---
libpins = {}
libs = [e for e in d if isinstance(e, list) and car(e) == Symbol("lib_symbols")]
if libs:
    for sym in libs[0][1:]:
        if not (isinstance(sym, list) and car(sym) == Symbol("symbol")):
            continue
        name = str(sym[1])
        pins = []
        for sub in sym:
            if isinstance(sub, list) and car(sub) == Symbol("symbol"):
                for p in sub:
                    if isinstance(p, list) and car(p) == Symbol("pin"):
                        at = [q for q in p if car(q) == Symbol("at")][0]
                        nm = [q for q in p if car(q) == Symbol("number")][0]
                        pins.append((str(nm[1]), num(at[1]), num(at[2])))
        libpins[name] = pins

# --- connection points: wire endpoints + junctions ---
conn = set()
for e in d:
    if not isinstance(e, list):
        continue
    if car(e) == Symbol("wire"):
        pts = [p for p in e if car(p) == Symbol("pts")][0]
        for p in pts:
            if car(p) == Symbol("xy"):
                conn.add((round(num(p[1]), 2), round(num(p[2]), 2)))
    elif car(e) == Symbol("junction"):
        at = [p for p in e if car(p) == Symbol("at")][0]
        conn.add((round(num(at[1]), 2), round(num(at[2]), 2)))

TF = [(1,0,0,-1),(0,1,1,0),(-1,0,0,1),(0,-1,-1,0),
      (-1,0,0,-1),(0,1,-1,0),(1,0,0,1),(0,-1,1,0)]

pinmap = {}
hit = tot = 0
for e in d:
    if not (isinstance(e, list) and car(e) == Symbol("symbol")):
        continue
    libid = str([p for p in e if car(p) == Symbol("lib_id")][0][1])
    ref = None
    for p in e:
        if isinstance(p, list) and car(p) == Symbol("property") and p[1] == "Reference":
            ref = p[2]
    at = [p for p in e if car(p) == Symbol("at")][0]
    sx, sy = num(at[1]), num(at[2])
    pins = libpins.get(libid, [])
    if not pins or not ref:
        continue
    best, bestscore = TF[0], -1
    for (a, b, c, dd) in TF:
        sc = 0
        for (_, px, py) in pins:
            X = round(sx + a * px + b * py, 2)
            Y = round(sy + c * px + dd * py, 2)
            if (X, Y) in conn:
                sc += 1
        if sc > bestscore:
            bestscore, best = sc, (a, b, c, dd)
    a, b, c, dd = best
    for (pn, px, py) in pins:
        X = round(sx + a * px + b * py, 2)
        Y = round(sy + c * px + dd * py, 2)
        pinmap[f"{ref}.{pn}"] = (X, Y)
        tot += 1
        if (X, Y) in conn:
            hit += 1

print(f"validation: {hit}/{tot} pins land on a wire endpoint/junction "
      f"({100*hit//max(tot,1)}%)")
for q in queries:
    print(f"  {q} -> {pinmap.get(q, 'NOT FOUND')}")
