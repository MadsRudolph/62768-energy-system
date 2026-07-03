#!/usr/bin/env python3
"""Follow-up fix: kicad-cli's DXF exporter silently skips the footprint
"Value" FIELD even when its layer is set to F.SilkS and it isn't hidden
(verified empirically - a generic fp_text "user" item at the identical
position/layer DOES get plotted). fix_tp_silk_labels.py moved Value onto
silk as a field, which looked right in the GUI/SVG but produced an empty
gap in the DXF/xTool file.

This script: for each TP1xx footprint, takes the CURRENT Value field
position (preserves any manual repositioning already done in the GUI to
fix label-vs-label overlaps), adds a plain fp_text "user" with the same
content/position/layer/font, and reverts Value back to hidden on F.Fab
(its original, normal state - same as every other component on the
board) so nothing duplicates in the 3D/GUI view.

Brug: python fix_tp_silk_labels2.py <board>.kicad_pcb
"""
import re
import sys
import uuid
from pathlib import Path


def sexp_end(text, start):
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


def main(path):
    path = Path(path)
    text = path.read_text(encoding="utf-8")

    fp_spans = []
    for m in re.finditer(r"\(footprint ", text):
        fp_spans.append((m.start(), sexp_end(text, m.start())))

    out = []
    pos = 0
    fixed = []
    for fp_start, fp_end in fp_spans:
        if fp_start < pos:
            continue
        fp_block = text[fp_start:fp_end]
        ref_m = re.search(r'\(property "Reference" "(TP1\d\d)"', fp_block)
        if not ref_m:
            continue
        ref = ref_m.group(1)

        val_m = re.search(
            r'\(property "Value" "([^"]*)"\s*\n(\s*)\(at ([^)]*)\)\s*\n\s*\(layer "F\.SilkS"\)',
            fp_block)
        if not val_m:
            continue  # not in the "Value already moved to silk" state
        value, indent, at = val_m.group(1), val_m.group(2), val_m.group(3)

        val_prop_start = fp_start + val_m.start()
        val_prop_end = sexp_end(text, val_prop_start)
        val_block = text[val_prop_start:val_prop_end]

        # revert Value field to its normal hidden/F.Fab state
        reverted = val_block.replace('(layer "F.SilkS")', '(layer "F.Fab")', 1)
        if "(hide yes)" not in reverted:
            uuid_idx = re.search(r"\(uuid ", reverted)
            reverted = (reverted[:uuid_idx.start()] + "(hide yes)\n" + indent
                        + reverted[uuid_idx.start():])

        new_text_elem = (
            f'\n{indent}(fp_text user "{value}"\n'
            f'{indent}\t(at {at})\n'
            f'{indent}\t(layer "F.SilkS")\n'
            f'{indent}\t(uuid "{uuid.uuid4()}")\n'
            f'{indent}\t(effects\n'
            f'{indent}\t\t(font\n'
            f'{indent}\t\t\t(size 1 1)\n'
            f'{indent}\t\t\t(thickness 0.15)\n'
            f'{indent}\t\t)\n'
            f'{indent}\t)\n'
            f'{indent})'
        )

        out.append(text[pos:val_prop_start])
        out.append(reverted)
        pos = val_prop_end
        # insert the new fp_text right before the footprint's closing paren
        out.append(text[pos:fp_end - 1])
        out.append(new_text_elem)
        out.append("\n\t")
        pos = fp_end - 1
        fixed.append(f"{ref} -> {value}")

    out.append(text[pos:])
    path.write_text("".join(out), encoding="utf-8")
    print(f"{path}: {len(fixed)} testpunkt-labels konverteret til fp_text")
    for line in fixed:
        print(" ", line)


if __name__ == "__main__":
    main(sys.argv[1])
