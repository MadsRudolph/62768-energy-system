"""Remove geometry that ERC flags as dangling, by coordinate. Safe: only touches
items ERC reports (never a connected wire). Handles wire_dangling / label_dangling /
junction_dangling / 'endpoint' wire warnings.
Usage: py -3.13 _clean_from_erc.py <file.kicad_sch> <erc_report.txt>
Prints how many blocks removed; run in a loop until ERC is clean.
"""
import sys, re

sch, erc = sys.argv[1], sys.argv[2]
report = open(erc, encoding="utf8").read()

# collect flagged coordinates and their violation type
flagged = []  # (kindword, x, y)
for block in re.split(r"\n(?=\[)", report):
    head = block.split("\n", 1)[0]
    m = re.match(r"\[(\w+)\]", head)
    if not m:
        continue
    typ = m.group(1)
    if typ not in ("wire_dangling", "label_dangling", "junction_dangling"):
        continue
    for mc in re.finditer(r"@\((-?\d+\.?\d*) mm, (-?\d+\.?\d*) mm\)", block):
        flagged.append((typ, float(mc.group(1)), float(mc.group(2))))

s = open(sch, "r", encoding="utf8", newline="").read()


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


TOL = 0.05
spans = []
for kind in ("wire", "label", "global_label", "junction"):
    idx = 0
    while True:
        j = s.find("\n\t(" + kind, idx)
        if j == -1:
            break
        paren = s.find("(", j)
        end = match_block(s, paren)
        idx = end
        pts = coords(s[paren:end])
        # remove this block if any of its points matches any flagged coord
        if any(abs(px - fx) < TOL and abs(py - fy) < TOL
               for (px, py) in pts for (_, fx, fy) in flagged):
            spans.append((j, end))

# dedupe overlapping spans, splice reverse
spans = sorted(set(spans), reverse=True)
for (a, b) in spans:
    s = s[:a] + s[b:]
open(sch, "w", encoding="utf8", newline="").write(s)
print("removed", len(spans), "dangling blocks")
