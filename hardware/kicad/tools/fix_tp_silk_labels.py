#!/usr/bin/env python3
"""Engangs-fix: testpunkt-footprints (TP101..TP117) viser refdes ("TP111") paa
F.SilkS, men det siger ingenting om signalet. Value-feltet har allerede det
rigtige navn (fra TestPoint-symbolerne i system.kicad_sch, fx TP111 -> PWM_MPPT).

Skjuler Reference-property og flytter Value-property over paa F.SilkS (samme
position/rotation som Reference havde), saa silketrykket viser signalnavnet
i stedet for TP-nummeret. Reference-designatoren i sig selv aendres IKKE (den
skal blive TPxxx for at matche skematikkets refdes).

Rent tekstbaseret (ingen sexpdata-afhaengighed) med parentes-matching, da
strukturen i praksis varierer let (nogle Reference-properties har allerede
en (hide yes) linje).

Brug: python fix_tp_silk_labels.py <board>.kicad_pcb
"""
import re
import sys
from pathlib import Path


def sexp_end(text, start):
    """text[start] == '('; returner index lige efter den matchende ')'."""
    assert text[start] == "("
    depth = 0
    i = start
    while i < len(text):
        if text[i] == "(":
            depth += 1
        elif text[i] == ")":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    raise ValueError("unbalanced parens")


def fix_block(block, new_pos_line):
    """block = fuld '(property "Value" ... )' tekst. Saet layer til F.SilkS
    og (at ...) til new_pos_line (Reference's gamle position)."""
    block = re.sub(r'\(layer "F\.Fab"\)', '(layer "F.SilkS")', block, count=1)
    block = re.sub(r"\(at [^)]*\)", new_pos_line, block, count=1)
    return block


def main(path):
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    fixed = []
    out = []
    pos = 0
    for m in re.finditer(r'\(property "Reference" "(TP1\d\d)"', text):
        ref = m.group(1)
        start = m.start()
        if start < pos:
            continue  # already consumed as part of a previous block copy
        end = sexp_end(text, start)
        ref_block = text[start:end]

        layer_m = re.search(r'\(layer "([^"]+)"\)', ref_block)
        if not layer_m or layer_m.group(1) != "F.SilkS":
            continue  # not a silk-labelled test point (already fixed?)

        at_m = re.search(r"\(at [^)]*\)", ref_block)
        ref_at = at_m.group(0)

        if "(hide yes)" not in ref_block:
            ref_block_new = ref_block[:-1].rstrip() + "\n\t\t\t(hide yes)\n\t\t)"
        else:
            ref_block_new = ref_block

        # the very next sibling property must be "Value"
        rest = text[end:]
        val_m = re.match(r'(\s*)(\(property "Value" "[^"]*")', rest)
        if not val_m:
            raise RuntimeError(f"{ref}: expected Value property right after Reference")
        val_start = end + val_m.start(2)
        val_end = sexp_end(text, val_start)
        val_block = text[val_start:val_end]
        val_block_new = fix_block(val_block, ref_at)

        out.append(text[pos:start])
        out.append(ref_block_new)
        out.append(text[end:val_start])
        out.append(val_block_new)
        pos = val_end
        fixed.append(ref)

    out.append(text[pos:])
    path.write_text("".join(out), encoding="utf-8")
    print(f"{path}: {len(fixed)} testpunkt-labels rettet -> {', '.join(fixed)}")


if __name__ == "__main__":
    main(sys.argv[1])
