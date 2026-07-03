#!/usr/bin/env python3
"""Strip a kicad-cli DXF export (tables/blocks/header boilerplate) down to a
minimal LINE/CIRCLE/ARC-only ENTITIES section for the xTool laser software,
and rename layers to the short names it expects.

kicad-cli's DXF export already renders KiCad's stroke font as vector LINE/
CIRCLE/ARC segments (no TEXT entities) - see `WORKFLOW.md` s.4. This script
only removes the ACAD boilerplate (APPID/LTYPE/STYLE/LAYER/BLOCK tables) that
the laser software chokes on, shortens layer names, rounds coordinates to
4 decimals, and translates the drawing so its bounding box starts at (0, 0).

Brug (efter `kicad-cli pcb export dxf -l "F.Silkscreen,Edge.Cuts" ...`):
    python dxf_clean_silk.py raw.dxf clean.dxf
"""
import sys
from pathlib import Path

LAYER_MAP = {"F.Silkscreen": "SILK", "Edge.Cuts": "OUTLINE"}
KINDS = ("LINE", "CIRCLE", "ARC")


def parse_entities(lines):
    """Yield (kind, {code: value}) for LINE/CIRCLE/ARC entities."""
    i = 0
    n = len(lines)
    while i < n:
        if lines[i].strip() == "0" and i + 1 < n and lines[i + 1].strip() in KINDS:
            kind = lines[i + 1].strip()
            i += 2
            codes = {}
            while i + 1 < n and lines[i].strip() != "0":
                codes[lines[i].strip()] = lines[i + 1].strip()
                i += 2
            yield kind, codes
        else:
            i += 1


def fmt(v):
    return f"{float(v):.4f}"


def main(src, dst):
    text = Path(src).read_text(encoding="utf-8", errors="ignore")
    lines = text.replace("\r\n", "\n").split("\n")

    ents = [(kind, c) for kind, c in parse_entities(lines) if c.get("8") in LAYER_MAP]

    # normalize so the drawing's bounding box starts at (0, 0). Uses the
    # entities' own reference points (line endpoints / circle+arc centers)
    # same as the original export - this matched the previously-committed
    # CLEAN file byte-for-byte on the (arc-free) board revision.
    xs, ys = [], []
    for kind, c in ents:
        xs.append(float(c["10"])); ys.append(float(c["20"]))
        if kind == "LINE":
            xs.append(float(c["11"])); ys.append(float(c["21"]))
    dx, dy = -min(xs), -min(ys)

    out = ["0", "SECTION", "2", "ENTITIES"]
    for kind, c in ents:
        layer = LAYER_MAP[c.get("8")]
        cx = fmt(float(c["10"]) + dx)
        cy = fmt(float(c["20"]) + dy)
        if kind == "LINE":
            out += ["0", "LINE", "8", layer,
                    "10", cx, "20", cy,
                    "11", fmt(float(c["11"]) + dx), "21", fmt(float(c["21"]) + dy),
                    "30", "0.0", "31", "0.0"]  # flat 2D drawing
        elif kind == "CIRCLE":
            out += ["0", "CIRCLE", "8", layer,
                    "10", cx, "20", cy,
                    "40", fmt(c["40"]), "30", "0.0"]
        else:  # ARC
            out += ["0", "ARC", "8", layer,
                    "10", cx, "20", cy,
                    "40", fmt(c["40"]),
                    "50", fmt(c["50"]), "51", fmt(c["51"]), "30", "0.0"]
    kept = len(ents)
    out += ["0", "ENDSEC", "0", "EOF", ""]

    Path(dst).write_text("\n".join(out), encoding="utf-8")
    print(f"{dst}: {kept} entities kept (layers {sorted(set(LAYER_MAP.values()))})")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage: dxf_clean_silk.py <raw.dxf> <clean.dxf>")
    main(sys.argv[1], sys.argv[2])
