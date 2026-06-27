#!/usr/bin/env python3
"""
Delete the redundant board-level I/O connectors from the 5 sub-sheets.

On the integrated board these are either inter-board nets (now copper traces) or
duplicates of a top-level edge connector (J_3PH/J_MOT/J_PV/J_STO/J_LOAD/J_15V/
J_5V/J_ARD/J_C2K/J_INA). The nets survive via the hierarchical sheet pins.

Paren-balanced text surgery: removes ONLY the named (symbol ...) instance blocks,
leaving every hierarchical label, wire, and the file's formatting otherwise intact.
Run with KiCad CLOSED.  Keeps a .bak of each file.
"""
from pathlib import Path

ROOT = Path(__file__).parents[1] / "boards"
TARGETS = {
    "motor_power/motor_power.kicad_sch":
        ["J201", "J202", "J203", "J204", "J205", "J206", "J207"],
    "motor_feedback/motor_feedback.kicad_sch":
        ["J301", "J302"],
    "mppt_buck/mppt_buck.kicad_sch":
        ["J401", "J402", "J403", "J404"],
    "boost/boost_v2_mill/boost_v2_mill.kicad_sch":
        ["J501", "J502", "J503", "J504"],
    "c2000_feedback/c2000_feedback.kicad_sch":
        ["J601", "J602", "J603", "J604", "J605"],
}

def block_end(s, start):
    """Index just past the ')' matching the '(' at s[start], respecting quotes."""
    depth = 0; in_str = False; esc = False; j = start
    while j < len(s):
        c = s[j]
        if in_str:
            if esc: esc = False
            elif c == "\\": esc = True
            elif c == '"': in_str = False
        elif c == '"': in_str = True
        elif c == "(": depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return j + 1
        j += 1
    raise ValueError("unbalanced")

def remove_symbol(text, ref):
    marker = f'(property "Reference" "{ref}"'
    i = text.find(marker)
    if i < 0:
        return text, False
    start = text.rfind("(symbol", 0, i)        # enclosing instance symbol
    end = block_end(text, start)
    # swallow leading indent and trailing newline so we don't leave a blank gap
    ls = start
    while ls > 0 and text[ls-1] in " \t":
        ls -= 1
    te = end
    while te < len(text) and text[te] in " \t":
        te += 1
    if te < len(text) and text[te] == "\n":
        te += 1
    return text[:ls] + text[te:], True

total = 0
for rel, refs in TARGETS.items():
    f = ROOT / rel
    txt = f.read_text(encoding="utf-8")
    f.with_suffix(f.suffix + ".bak").write_text(txt, encoding="utf-8")
    done = []
    for r in refs:
        txt, ok = remove_symbol(txt, r)
        if ok: done.append(r)
        else: print(f"  !! {rel}: {r} NOT found")
    f.write_text(txt, encoding="utf-8")
    total += len(done)
    print(f"{rel}: removed {len(done)} -> {', '.join(done)}")
print(f"\nTOTAL removed: {total}  (expected 22)")
