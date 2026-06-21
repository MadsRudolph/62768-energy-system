"""Inverse of _remove_region: remove wire/label/global_label/junction/text and #PWR
symbol blocks whose coordinates are ALL outside the keep box. Keeps internal block
wiring and straddling wires (any endpoint inside); ERC-loop cleans the straddler stubs.
Usage: py -3.13 _keep_region.py <file> x0 x1 y0 y1
"""
import sys, re

path = sys.argv[1]
x0, x1, y0, y1 = (float(a) for a in sys.argv[2:6])
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
    return [(float(a), float(b)) for a, b in
            re.findall(r"\((?:xy|at) (-?\d+\.?\d*) (-?\d+\.?\d*)", block)]


def inside(x, y):
    return x0 <= x <= x1 and y0 <= y <= y1


spans = []
n = {"wire": 0, "label": 0, "global_label": 0, "junction": 0, "text": 0, "pwr": 0}
for kind in ("wire", "label", "global_label", "junction", "text", "symbol"):
    idx = 0
    while True:
        j = s.find("\n\t(" + kind, idx)
        if j == -1:
            break
        paren = s.find("(", j)
        end = match_block(s, paren)
        block = s[paren:end]
        idx = end
        pts = coords(block)
        if not pts:
            continue
        if kind == "symbol":
            mref = re.search(r'\(property "Reference" "([^"]+)"', block)
            ref = mref.group(1) if mref else ""
            if not ref.startswith("#"):
                continue   # never touch real components (already filtered to the 8)
            key = "pwr"
        else:
            key = kind
        if all(not inside(x, y) for (x, y) in pts):   # entirely outside -> drop
            spans.append((j, end))
            n[key] += 1

for (a, b) in sorted(set(spans), reverse=True):
    s = s[:a] + s[b:]
open(path, "w", encoding="utf8", newline="").write(s)
print("removed (outside keep-box):", n)
