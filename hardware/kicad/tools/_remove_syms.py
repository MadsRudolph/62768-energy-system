"""Remove top-level (symbol ...) instance blocks by Reference, via paren-matched
text splice that respects quoted strings. Usage:
    py -3.13 _remove_syms.py <file.kicad_sch> keep|remove R1 R2 ...
mode 'remove' deletes the listed refs; 'keep' deletes every real component NOT listed
(power symbols #PWR* are always kept)."""
import sys, re

path = sys.argv[1]
mode = sys.argv[2]
listed = set(sys.argv[3:])
s = open(path, "r", encoding="utf8", newline="").read()


def match_block(s, start):
    depth = 0
    i = start
    instr = False
    esc = False
    while i < len(s):
        c = s[i]
        if instr:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                instr = False
        else:
            if c == '"':
                instr = True
            elif c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
                if depth == 0:
                    return i + 1
        i += 1
    raise ValueError("unbalanced parens")


removed = []
spans = []
idx = 0
while True:
    j = s.find("\n\t(symbol", idx)
    if j == -1:
        break
    paren = s.find("(", j)
    end = match_block(s, paren)
    block = s[paren:end]
    m = re.search(r'\(property "Reference" "([^"]+)"', block)
    ref = m.group(1) if m else None
    drop = False
    if ref:
        if mode == "remove":
            drop = ref in listed
        elif mode == "keep":
            drop = (not ref.startswith("#")) and (ref not in listed)
    if drop:
        spans.append((j, end))
        removed.append(ref)
    idx = end

for (a, b) in sorted(spans, reverse=True):
    s = s[:a] + s[b:]

open(path, "w", encoding="utf8", newline="").write(s)
print("removed:", sorted(removed), "count:", len(removed))
