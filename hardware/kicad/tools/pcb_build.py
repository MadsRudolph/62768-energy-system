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
# Windows (teamets PC'er) som standard; Linux/proot via $KICAD_FOOTPRINT_DIR-override.
FPLIB = os.environ.get("KICAD_FOOTPRINT_DIR") or (
    r"C:\Program Files\KiCad\9.0\share\kicad\footprints" if os.name == "nt"
    else "/usr/share/kicad/footprints")
PRJLIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib")

def load_fp(fpid):
    lib, name = fpid.split(":")
    base = PRJLIB if lib == "energy_system" else FPLIB
    fp = pcbnew.FootprintLoad(os.path.join(base, f"{lib}.pretty"), name)
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
        # buck_v2: signalflow venstre->hoejre: 5V-forsyning oeverst, 555-PWM,
        # valg/opto-raekke, effekt-tog (Q1/D3/L1/C5) mod hoejre/bund.
        # (refs foelger teamets re-annotering: 555=U2, opto=U3, batteri=J1)
        "buck_v2": {"refs": {
            "U1": (38, 32, 0), "C1": (50, 32, 0), "C2": (60, 32, 0),
            "R1": (36, 46, 0), "R2": (48, 46, 0), "D1": (60, 46, 0),
            "D2": (72, 46, 0), "RV1": (84, 46, 0),
            "U2": (40, 58, 0), "C6": (54, 58, 0), "C3": (64, 58, 0), "C5": (74, 58, 0),
            "J2": (32, 72, 0), "SW1": (46, 72, 0), "R3": (60, 72, 0),
            "U3": (74, 72, 0), "R4": (88, 72, 0),
            "Q1": (100, 46, 0), "D3": (100, 58, 0), "J1": (113, 72, 0),
            "L1": (76, 92, 0), "C4": (102, 92, 0), "J3": (113, 92, 0),
        }},
        "current_sense": {"refs": {
            "J1": (35, 30, 180), "R11": (50, 30, 0), "R12": (64, 24, 0), "R13": (64, 36, 0),
            "J2": (35, 50, 180), "R21": (50, 50, 0), "R22": (64, 44, 0), "R23": (64, 56, 0),
            "J3": (35, 70, 180), "R31": (50, 70, 0), "R32": (64, 64, 0), "R33": (64, 76, 0),
            "U1": (78, 38, 0), "U2": (78, 62, 0),
            "C1": (90, 30, 0), "C2": (90, 54, 0),
            "J4": (105, 50, 0),
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

        # stik-kolonnerne KLODS op ad midter-blokken (venstre/hoejre side) -
        # hele klyngen pakkes kompakt og centreres bagefter i jig-omridset.
        conn_h = max((bbox_mm(fps[r])[1] for r in left + right), default=10) + 4

        widest = max((bbox_mm(fps[r])[0] + PITCH for r in mid), default=40.0)
        row_w_max = min(W - 43, max(40.0, widest, math.sqrt(
            sum((bbox_mm(fps[r])[0] + PITCH) * (bbox_mm(fps[r])[1] + 3) for r in mid)) * 1.3))
        rows = [[]]; xacc = 0.0
        for r in mid:
            w = bbox_mm(fps[r])[0] + PITCH
            if xacc + w > row_w_max and rows[-1]:
                rows.append([]); xacc = 0.0
            rows[-1].append(r); xacc += w

        mid_w = max((sum(bbox_mm(fps[r])[0] + PITCH for r in row) for row in rows),
                    default=0)
        row_hs = [max((bbox_mm(fps[r])[1] for r in row), default=0) + 3 for row in rows]
        mid_x0 = X0 + 30                    # vilkaarligt anker - klyngen centreres
        y = Y0 + 12
        for row, rh in zip(rows, row_hs):
            x = mid_x0
            for r in row:
                w = bbox_mm(fps[r])[0] + PITCH
                put(r, x + w / 2, y + rh / 2, 0)   # centreret i raekken
                x += w
            y += rh
        for i, r in enumerate(left):
            put(r, mid_x0 - 13, Y0 + 12 + i * conn_h, 180)  # stik vender ud mod kanten
        for i, r in enumerate(right):
            put(r, mid_x0 + mid_w + 13, Y0 + 12 + i * conn_h, 0)

    # --- centrer komponent-klyngen i jig-omridset ----------------------------
    # Klyngen pakkes kompakt oppe i hjoernet; her flyttes ALT (stik inkl.) saa
    # klyngens bbox ligger midt i 104x104-omridset - ingen komponenter klods
    # op ad edge cuts.
    lo_x = min(pcbnew.ToMM(fp.GetBoundingBox(False).GetLeft()) for fp in fps.values())
    hi_x = max(pcbnew.ToMM(fp.GetBoundingBox(False).GetRight()) for fp in fps.values())
    lo_y = min(pcbnew.ToMM(fp.GetBoundingBox(False).GetTop()) for fp in fps.values())
    hi_y = max(pcbnew.ToMM(fp.GetBoundingBox(False).GetBottom()) for fp in fps.values())
    if hi_x - lo_x > W - 6 or hi_y - lo_y > H - 6:
        raise SystemExit(
            f"{bname}: klyngen er {hi_x - lo_x:.0f}x{hi_y - lo_y:.0f} mm - "
            f"passer ikke i jiggens {W}x{H} (juster PLACE/marginer)")
    dx = (X0 + W / 2) - (lo_x + hi_x) / 2
    dy = (Y0 + H / 2) - (lo_y + hi_y) / 2
    for fp in fps.values():
        p = fp.GetPosition()
        fp.SetPosition(VECTOR2I(p.x + FromMM(dx), p.y + FromMM(dy)))

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
