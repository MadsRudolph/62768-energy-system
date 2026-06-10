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

import os
FPLIB = r"C:\Program Files\KiCad\9.0\share\kicad\footprints"
PRJLIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib")

def load_fp(fpid):
    lib, name = fpid.split(":")
    base = PRJLIB if lib == "energy_system" else FPLIB
    fp = pcbnew.FootprintLoad(rf"{base}\{lib}.pretty", name)
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
        # Device:Q_NMOS o.l. har bogstav-pinnumre (G/D/S) mens TO-220-pads
        # hedder 1/2/3 - uden denne mapping faar MOSFET'ens pads INTET net.
        GDS = {"1": "G", "2": "D", "3": "S"}
        for pad in fp.Pads():
            num = pad.GetNumber()
            net = c["pads"].get(num) or c["pads"].get(GDS.get(num, ""))
            if net:
                pad.SetNet(netmap[net])
        fps[c["ref"]] = fp
    # ingen pad maa ende uden net hvis komponenten har net i netlisten
    for c in data["components"]:
        fp = fps[c["ref"]]
        if c["pads"] and all(p.GetNetCode() == 0 for p in fp.Pads()):
            raise SystemExit(f"{c['ref']}: ingen pads fik net - pinnummer-mismatch?")

    # --- fast boardstoerrelse: jiggen til fiberlaseren ----------------------
    # Jiggen tager en 109x109 mm kobberplade; edge cuts er 104x104 (2.5 mm rand
    # hele vejen rundt). ALLE boards har samme omrids - komponenterne skal passe
    # indenfor, ellers fejler scriptet haardt nedenfor.
    JIG_W, JIG_H = 104, 104

    # --- haandlagt placering for de svaere boards --------------------------
    # Gitter-autoplaceringen spreder kanal-komponenterne og sulter routeren paa
    # enkeltsidet. Her foelger placeringen signalflowet (venstre -> hoejre).
    # Koordinaterne er absolutte (X0/Y0 = 20, board 20..124).
    PLACE = {
        "current_sense": {"refs": {
            "J1": (35, 30, 180), "R11": (50, 30, 0), "R12": (64, 24, 0), "R13": (64, 36, 0),
            "J2": (35, 50, 180), "R21": (50, 50, 0), "R22": (64, 44, 0), "R23": (64, 56, 0),
            "J3": (35, 70, 180), "R31": (50, 70, 0), "R32": (64, 64, 0), "R33": (64, 76, 0),
            "U1": (78, 38, 0), "U2": (78, 62, 0),
            "C1": (90, 30, 0), "C2": (90, 54, 0),
            "J4": (109, 50, 0),
        }},
        "mppt": {"refs": {
            "J1": (35, 30, 180), "D1": (52, 26, 0),
            "C1": (70, 33, 0), "C2": (90, 33, 0), "C3": (110, 33, 0),
            "R5": (38, 47, 0), "R6": (38, 55, 180),
            "R7": (52, 50, 0), "R8": (64, 50, 0), "U1": (78, 52, 0), "C4": (90, 48, 0),
            "R1": (38, 66, 0), "R2": (50, 66, 0),
            "R3": (62, 66, 0), "DZ1": (74, 66, 0), "C6": (86, 66, 0),
            "R4": (38, 78, 0), "Q1": (56, 76, 0), "C5": (70, 78, 0),
            "J2": (109, 58, 0), "J3": (109, 78, 0),
        }},
    }
    import os as _os
    bname = _os.path.splitext(_os.path.basename(outf))[0]

    # --- placering ---------------------------------------------------------
    # PITCH 5 mm bbox-gab: kompakt, men stadig en routing-kanal (1.0 mm bane +
    # 2x0.8 clearance = 2.6 mm) mellem naboers pads.
    PITCH = 5.0
    X0, Y0 = 20, 20                      # boardets overste venstre hjoerne
    EDGE = 15                            # stik-indryk fra kanten (DRC edge clearance)

    def put(ref, x, y, angle=0):
        """Placerer footprintens BBOX-CENTRUM i (x,y) - ankeret er ofte pad 1."""
        fp = fps[ref]
        fp.SetOrientationDegrees(angle)
        t = VECTOR2I(FromMM(x), FromMM(y))
        fp.SetPosition(t)
        c = fp.GetBoundingBox(False).Centre()
        fp.SetPosition(VECTOR2I(t.x + (t.x - c.x), t.y + (t.y - c.y)))

    W, H = JIG_W, JIG_H
    if bname in PLACE:
        spec = PLACE[bname]
        missing = set(fps) - set(spec["refs"])
        if missing:
            raise SystemExit(f"{bname}: manuel placering mangler refs: {missing}")
        for ref, (x, y, ang) in spec["refs"].items():
            put(ref, x, y, ang)
    else:
        left  = sorted([r for r in fps if (r.startswith("J") and int(r[1:]) % 2 == 1)])
        right = sorted([r for r in fps if (r.startswith("J") and int(r[1:]) % 2 == 0)
                        or r == "M1" and fps[r].GetFPID().GetLibItemName().__str__().startswith("TerminalBlock")])
        mid = [r for r in sorted(fps, key=lambda r: (r[0] not in "DLQU", r))
               if r not in left and r not in right]

        # stik oeverst paa venstre/hoejre kant; midter-komponenterne pakkes
        # KOMPAKT i et kvadratisk-agtigt blok under stik-zonen - spildplads paa
        # det faste jig-format er OK, men korte baner er bedre routing.
        conn_h = max((bbox_mm(fps[r])[1] for r in left + right), default=10) + 4
        n_conn = max(len(left), len(right))
        conn_bottom = Y0 + 12 + (n_conn - 1) * conn_h + conn_h / 2 if n_conn else Y0 + 4

        for i, r in enumerate(left):
            put(r, X0 + EDGE, Y0 + 12 + i * conn_h, 180)  # stik vender ud mod kanten
        for i, r in enumerate(right):
            put(r, X0 + W - EDGE, Y0 + 12 + i * conn_h, 0)

        widest = max((bbox_mm(fps[r])[0] + PITCH for r in mid), default=40.0)
        row_w_max = min(W - 16, max(40.0, widest, math.sqrt(
            sum((bbox_mm(fps[r])[0] + PITCH) * (bbox_mm(fps[r])[1] + 3) for r in mid)) * 1.3))
        rows = [[]]; xacc = 0.0
        for r in mid:
            w = bbox_mm(fps[r])[0] + PITCH
            if xacc + w > row_w_max and rows[-1]:
                rows.append([]); xacc = 0.0
            rows[-1].append(r); xacc += w

        row_hs = [max((bbox_mm(fps[r])[1] for r in row), default=0) + 3 for row in rows]
        y = conn_bottom + 5
        for row, rh in zip(rows, row_hs):
            x = X0 + 8
            for r in row:
                w = bbox_mm(fps[r])[0] + PITCH
                put(r, x + w / 2, y + rh / 2, 0)   # centreret i raekken
                x += w
            y += rh
        if y > Y0 + H - 4:
            raise SystemExit(
                f"{bname}: komponenterne ender ved y={y - Y0:.0f} mm - "
                f"passer ikke i jiggens {H} mm (juster PLACE/marginer)")

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
    ds.m_TrackMinWidth = FromMM(0.8)
    # DTU-PCB-prototyping-guiden (fiberlaser): clearance >= 0.8, bane >= 0.8 (1.0 foretrukket)
    nc = board.GetAllNetClasses()["Default"]
    nc.SetTrackWidth(FromMM(1.0))
    nc.SetClearance(FromMM(0.8))

    pcbnew.SaveBoard(outf, board)
    print(f"wrote {outf}  ({len(fps)} footprints, {W:.0f}x{H:.0f} mm)")

    # .kicad_pro ved siden af boardet, saa KiCad linker skema <-> PCB naar de
    # ligger i samme mappe med samme basenavn. Netclass-reglerne SKAL med her -
    # ellers falder GUI'en tilbage til 0.2 mm defaults ved manuel routing.
    prof = os.path.splitext(outf)[0] + ".kicad_pro"
    if not os.path.exists(prof):
        pro = {
            "meta": {"filename": os.path.basename(prof), "version": 3},
            "board": {
                "design_settings": {
                    "rules": {
                        "min_clearance": 0.0,
                        "min_track_width": 0.8,
                        "min_copper_edge_clearance": 0.5,
                    },
                    "defaults": {},
                },
            },
            "net_settings": {
                "meta": {"version": 4},
                "classes": [{
                    "name": "Default",
                    "clearance": 0.8,
                    "track_width": 1.0,
                    "via_diameter": 1.6,
                    "via_drill": 0.8,
                    "wire_width": 6,
                    "bus_width": 12,
                    "line_style": 0,
                    "microvia_diameter": 0.3,
                    "microvia_drill": 0.1,
                    "diff_pair_width": 1.0,
                    "diff_pair_gap": 0.8,
                    "diff_pair_via_gap": 0.8,
                    "pcb_color": "rgba(0, 0, 0, 0.000)",
                    "schematic_color": "rgba(0, 0, 0, 0.000)",
                }],
            },
            "project": {"files": []},
        }
        with open(prof, "w", encoding="utf-8") as f:
            json.dump(pro, f, indent=2)
        print(f"wrote {prof}")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
