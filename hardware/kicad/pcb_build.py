#!/usr/bin/env python3
"""
JSON-netliste -> placeret .kicad_pcb (enkeltsidet: THT-komponenter paa toppen,
kobber paa bagsiden/B.Cu).

Placering: J-stik paa kanterne (ulige J + M1-terminal venstre, lige J hoejre),
oevrige komponenter i gitter ordnet efter ref-klasse. Ikke koent, men korrekt
netliste + fornuftige afstande; Freerouting/manuel routing tager resten.

Koeres med KiCads python: & "C:\\Program Files\\KiCad\\9.0\\bin\\python.exe"
    pcb_build.py netliste.json ud.kicad_pcb
"""
import json, sys, math
import pcbnew
from pcbnew import VECTOR2I, FromMM

FPLIB = r"C:\Program Files\KiCad\9.0\share\kicad\footprints"

def load_fp(fpid):
    lib, name = fpid.split(":")
    fp = pcbnew.FootprintLoad(rf"{FPLIB}\{lib}.pretty", name)
    if fp is None:
        raise SystemExit(f"footprint ikke fundet: {fpid}")
    return fp

def bbox_mm(fp):
    bb = fp.GetBoundingBox(False)
    return (pcbnew.ToMM(bb.GetWidth()), pcbnew.ToMM(bb.GetHeight()))

def main(jsonf, outf):
    data = json.loads(open(jsonf, encoding="utf-8").read())
    board = pcbnew.NewBoard(outf)
    ds = board.GetDesignSettings()

    netmap = {}
    for name in data["nets"]:
        ni = pcbnew.NETINFO_ITEM(board, name)
        board.Add(ni)
        netmap[name] = ni

    fps = {}
    for c in data["components"]:
        if not c["footprint"]:
            raise SystemExit(f"{c['ref']} mangler footprint")
        fp = load_fp(c["footprint"])
        fp.SetReference(c["ref"])
        fp.SetValue(c["value"] or "")
        board.Add(fp)
        for pad in fp.Pads():
            net = c["pads"].get(pad.GetNumber())
            if net:
                pad.SetNet(netmap[net])
        fps[c["ref"]] = fp

    # --- placering ---------------------------------------------------------
    left  = sorted([r for r in fps if (r.startswith("J") and int(r[1:]) % 2 == 1)])
    right = sorted([r for r in fps if (r.startswith("J") and int(r[1:]) % 2 == 0)
                    or r == "M1" and fps[r].GetFPID().GetLibItemName().__str__().startswith("TerminalBlock")])
    mid = [r for r in sorted(fps, key=lambda r: (r[0] not in "DLQU", r))
           if r not in left and r not in right]

    PITCH = 8.0
    X0, Y0 = 20, 20                      # boardets overste venstre hjoerne
    EDGE = 15                            # stik-indryk fra kanten (DRC edge clearance)

    # midter-komponenter pakkes i raekker med individuel bredde
    conn_h = max((bbox_mm(fps[r])[1] for r in left + right), default=10) + 6
    row_w_max = max(40.0, math.sqrt(
        sum((bbox_mm(fps[r])[0] + PITCH) * (bbox_mm(fps[r])[1] + 5) for r in mid)) * 1.6)
    rows = [[]]; xacc = 0.0
    for r in mid:
        w = bbox_mm(fps[r])[0] + PITCH
        if xacc + w > row_w_max and rows[-1]:
            rows.append([]); xacc = 0.0
        rows[-1].append(r); xacc += w

    mid_w = max((sum(bbox_mm(fps[r])[0] + PITCH for r in row) for row in rows),
                default=0)
    row_hs = [max((bbox_mm(fps[r])[1] for r in row), default=0) + 5 for row in rows]
    H = max(sum(row_hs), len(left) * conn_h, len(right) * conn_h) + 18
    W = mid_w + 2 * (EDGE + 14) + 4

    def put(ref, x, y, angle=0):
        """Placerer footprintens BBOX-CENTRUM i (x,y) - ankeret er ofte pad 1."""
        fp = fps[ref]
        fp.SetOrientationDegrees(angle)
        t = VECTOR2I(FromMM(x), FromMM(y))
        fp.SetPosition(t)
        c = fp.GetBoundingBox(False).Centre()
        fp.SetPosition(VECTOR2I(t.x + (t.x - c.x), t.y + (t.y - c.y)))

    for i, r in enumerate(left):
        put(r, X0 + EDGE, Y0 + 12 + i * conn_h, 180)  # stik vender ud mod kanten
    for i, r in enumerate(right):
        put(r, X0 + W - EDGE, Y0 + 12 + i * conn_h, 0)
    y = Y0 + 10
    for row, rh in zip(rows, row_hs):
        x = X0 + EDGE + 14
        for r in row:
            w = bbox_mm(fps[r])[0] + PITCH
            put(r, x + w / 2, y + rh / 2, 0)   # centreret i raekken
            x += w
        y += rh

    # --- omrids (RECT = altid lukket, ingen segment-kaedning) ----------------
    W, H = math.ceil(W), math.ceil(H)
    rect = pcbnew.PCB_SHAPE(board)
    rect.SetShape(pcbnew.SHAPE_T_RECT)
    rect.SetStart(VECTOR2I(FromMM(X0), FromMM(Y0)))
    rect.SetEnd(VECTOR2I(FromMM(X0 + W), FromMM(Y0 + H)))
    rect.SetLayer(pcbnew.Edge_Cuts)
    rect.SetWidth(FromMM(0.1))
    rect.SetFilled(False)
    board.Add(rect)

    # --- enkeltsidet opsaetning ---------------------------------------------
    ds.SetCopperLayerCount(2)            # KiCad kraever min. 2; vi router kun B.Cu
    ds.m_TrackMinWidth = FromMM(0.5)
    nc = board.GetAllNetClasses()["Default"]
    nc.SetTrackWidth(FromMM(1.0))        # THT/hobby: brede baner
    nc.SetClearance(FromMM(0.4))

    pcbnew.SaveBoard(outf, board)
    print(f"wrote {outf}  ({len(fps)} footprints, {W:.0f}x{H:.0f} mm)")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
