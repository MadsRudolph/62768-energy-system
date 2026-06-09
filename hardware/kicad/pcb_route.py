#!/usr/bin/env python3
"""DSN-eksport eller SES-import omkring Freerouting.
Brug (KiCads python):
  python pcb_route.py dsn board.kicad_pcb ud.dsn
  python pcb_route.py ses board.kicad_pcb ind.ses     (gemmer boardet bagefter)
"""
import sys
import pcbnew

mode, boardf = sys.argv[1], sys.argv[2]
board = pcbnew.LoadBoard(boardf)
if mode == "dsn":
    ok = pcbnew.ExportSpecctraDSN(board, sys.argv[3])
    print("dsn:", ok)
def add_refdes_copper(board):
    """Komponentnavne som kobber-tekst paa B.Cu (laseren har ingen silkscreen).

    Teksten lægges spejlvendt ved siden af hver komponent og graveres som en
    fritliggende kobber-ø i zonen. Placeringen undgår baner/pads/anden tekst -
    kobber-tekst OVER en bane ville kortslutte eller skære den. Kandidater
    proeves over/under/venstre/hoejre; ingen plads -> tekst droppes (med log)."""
    from pcbnew import VECTOR2I, FromMM, ToMM

    bbox_brd = board.GetBoardEdgesBoundingBox()
    margin = FromMM(1.2)
    CLR = FromMM(0.85)                       # afstand til andet kobber

    obstacles = []                           # BOX2I'er, allerede inflateret
    for t in board.GetTracks():
        # diagonale baner har kaempe bounding box -> sampl segmentet i smaa
        # bokse, ellers kasseres tekst-positioner paa falsk grundlag
        s, e = t.GetStart(), t.GetEnd()
        length = max(1, int(((e.x - s.x) ** 2 + (e.y - s.y) ** 2) ** 0.5))
        n = max(1, length // FromMM(1.5))
        r = t.GetWidth() // 2 + CLR
        for i in range(n + 1):
            px = s.x + (e.x - s.x) * i // n
            py = s.y + (e.y - s.y) * i // n
            bb = pcbnew.BOX2I(pcbnew.VECTOR2I(px - r, py - r),
                              pcbnew.VECTOR2I(2 * r, 2 * r))
            obstacles.append(bb)
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            bb = pad.GetBoundingBox()
            bb.Inflate(CLR)
            obstacles.append(bb)

    def free(bb):
        if bb.GetLeft() < bbox_brd.GetLeft() + margin: return False
        if bb.GetRight() > bbox_brd.GetRight() - margin: return False
        if bb.GetTop() < bbox_brd.GetTop() + margin: return False
        if bb.GetBottom() > bbox_brd.GetBottom() - margin: return False
        return not any(bb.Intersects(o) for o in obstacles)

    placed = skipped = 0
    for fp in sorted(board.GetFootprints(), key=lambda f: f.GetReference()):
        ref = fp.GetReference()
        fbb = fp.GetBoundingBox(False)
        txt = pcbnew.PCB_TEXT(board)
        txt.SetText(ref)
        txt.SetLayer(pcbnew.B_Cu)
        txt.SetMirrored(True)                # laesbar set fra bagsiden
        txt.SetTextSize(VECTOR2I(FromMM(1.5), FromMM(1.5)))
        txt.SetTextThickness(FromMM(0.3))
        board.Add(txt)
        cx, cy = fbb.Centre().x, fbb.Centre().y
        half_h = fbb.GetHeight() // 2
        half_w = fbb.GetWidth() // 2
        step = FromMM(1.7)
        cands = []
        for extra in (0, FromMM(1.5), FromMM(3.0), FromMM(4.5)):
            dy = half_h + step + extra
            dx = half_w + step + extra
            cands += [(cx, cy - dy), (cx, cy + dy), (cx - dx, cy), (cx + dx, cy),
                      (cx - dx, cy - dy), (cx + dx, cy - dy),
                      (cx - dx, cy + dy), (cx + dx, cy + dy)]
        ok_pos = None
        for px, py in cands:
            txt.SetPosition(VECTOR2I(int(px), int(py)))
            tb = txt.GetBoundingBox()
            tb.Inflate(FromMM(0.2))
            if free(tb):
                ok_pos = (px, py)
                break
        if ok_pos is None:
            board.Remove(txt)
            skipped += 1
            print(f"  refdes {ref}: ingen fri plads - droppet")
            continue
        tb = txt.GetBoundingBox()
        tb.Inflate(CLR)
        obstacles.append(tb)                 # naeste tekster skal ogsaa undgaa denne
        placed += 1
    print(f"  refdes paa B.Cu: {placed} placeret, {skipped} droppet")

if mode == "ses":
    ok = pcbnew.ImportSpecctraSES(board, sys.argv[3])
    add_refdes_copper(board)
    # Fiberlaser-zone jf. DTU-PCB-prototyping-guiden: solid B.Cu-zone UDEN net og
    # UDEN pad-forbindelse. Laseren fjerner kun isolations-kanalerne omkring
    # baner/pads i stedet for alt kobberet - hurtigere og mindre slid.
    bbox = board.GetBoardEdgesBoundingBox()
    zone = pcbnew.ZONE(board)
    zone.SetLayer(pcbnew.B_Cu)
    zone.SetNetCode(0)                                   # <no net>
    chain = pcbnew.SHAPE_LINE_CHAIN()
    for px, py in [(bbox.GetLeft(), bbox.GetTop()), (bbox.GetRight(), bbox.GetTop()),
                   (bbox.GetRight(), bbox.GetBottom()), (bbox.GetLeft(), bbox.GetBottom())]:
        chain.Append(px, py)
    chain.SetClosed(True)
    zone.Outline().AddOutline(chain)
    zone.SetLocalClearance(pcbnew.FromMM(0.8))           # guide: 0.75; 0.8 matcher netclass
    zone.SetMinThickness(pcbnew.FromMM(0.25))
    zone.SetPadConnection(pcbnew.ZONE_CONNECTION_NONE)
    zone.SetFillMode(pcbnew.ZONE_FILL_MODE_POLYGONS)     # solid fill
    board.Add(zone)
    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())
    pcbnew.SaveBoard(boardf, board)
    print("ses:", ok, "+ laser-zone (no net)")
