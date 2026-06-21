"""Remove leftover graphics of a deleted schematic block by spatial region.
Removes, via paren-matched text splice (format-preserving):
  - wire blocks with ANY endpoint inside the tight box (+wire margin)
  - label/global_label/junction/text blocks whose point is inside the wide box
  - symbol blocks whose Reference starts with '#' (power ports) inside the wide box
Usage: py -3.13 _remove_region.py <file> x0 x1 y0 y1   (tight bbox; margins applied inside)
"""
import sys, re

path = sys.argv[1]
x0, x1, y0, y1 = (float(a) for a in sys.argv[2:6])
WIRE_M = 3.0
WIDE_M = 15.0
s = open(path, "r", encoding="utf8", newline="").read()


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


def coords(block):
    # all (xy x y) and (at x y ...) numeric pairs
    pts = []
    for m in re.finditer(r"\((?:xy|at) (-?\d+\.?\d*) (-?\d+\.?\d*)", block):
        pts.append((float(m.group(1)), float(m.group(2))))
    return pts


def in_tight(x, y, m):
    return (x0 - m) <= x <= (x1 + m) and (y0 - m) <= y <= (y1 + m)


spans = []
removed = {"wire": 0, "label": 0, "global_label": 0, "junction": 0, "text": 0, "pwr": 0}
for kind in ("wire", "label", "global_label", "junction", "text", "symbol"):
    idx = 0
    needle = "\n\t(" + kind
    while True:
        j = s.find(needle, idx)
        if j == -1:
            break
        paren = s.find("(", j)
        end = match_block(s, paren)
        block = s[paren:end]
        idx = end
        pts = coords(block)
        if not pts:
            continue
        hit = False
        if kind == "wire":
            hit = any(in_tight(x, y, WIRE_M) for (x, y) in pts)
            key = "wire"
        elif kind == "symbol":
            mref = re.search(r'\(property "Reference" "([^"]+)"', block)
            ref = mref.group(1) if mref else ""
            if not ref.startswith("#"):
                continue
            hit = all(in_tight(x, y, WIDE_M) for (x, y) in pts)
            key = "pwr"
        else:
            hit = all(in_tight(x, y, WIDE_M) for (x, y) in pts)
            key = kind
        if hit:
            spans.append((j, end))
            removed[key] += 1

for (a, b) in sorted(spans, reverse=True):
    s = s[:a] + s[b:]
open(path, "w", encoding="utf8", newline="").write(s)
print("removed:", removed)
