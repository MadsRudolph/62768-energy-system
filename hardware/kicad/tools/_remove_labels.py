"""Remove specific global_label blocks matching (name, x, y) within tolerance.
Usage: py -3.13 _remove_labels.py <file> name1 x1 y1 [name2 x2 y2 ...]
"""
import sys, re

path = sys.argv[1]
args = sys.argv[2:]
targets = [(args[i], float(args[i + 1]), float(args[i + 2])) for i in range(0, len(args), 3)]
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


spans = []
removed = []
idx = 0
while True:
    j = s.find("\n\t(global_label", idx)
    if j == -1:
        break
    paren = s.find("(", j)
    end = match_block(s, paren)
    block = s[paren:end]
    idx = end
    mn = re.search(r'\(global_label "([^"]*)"', block)
    ma = re.search(r"\(at (-?\d+\.?\d*) (-?\d+\.?\d*)", block)
    if not (mn and ma):
        continue
    name = mn.group(1)
    x, y = float(ma.group(1)), float(ma.group(2))
    for (tn, tx, ty) in targets:
        if name == tn and abs(x - tx) < 0.05 and abs(y - ty) < 0.05:
            spans.append((j, end))
            removed.append((name, x, y))
            break

for (a, b) in sorted(spans, reverse=True):
    s = s[:a] + s[b:]
open(path, "w", encoding="utf8", newline="").write(s)
print("removed labels:", removed)
