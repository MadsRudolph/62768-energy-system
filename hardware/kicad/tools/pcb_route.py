#!/usr/bin/env python3
"""DSN-eksport eller SES-import omkring Freerouting (to-trins-flow).
Brug (KiCads python):
  python pcb_route.py dsn     board.kicad_pcb ud.dsn   trin 1: raa DSN
  python pcb_route.py sesraw  board.kicad_pcb ind.ses  trin 1: import, gem, intet pynt
  python pcb_route.py lockdsn board.kicad_pcb ud.dsn   trin 2: laas eksisterende kobber
                                                       som (type fix) og eksporter DSN
                                                       (boardet gemmes IKKE - laasen er
                                                       kun til freerouting)
  python pcb_route.py ses     board.kicad_pcb ind.ses  finale: import + refdes-tekst +
                                                       laser-zoner, gem
"""
import sys
import pcbnew

mode, boardf = sys.argv[1], sys.argv[2]
board = pcbnew.LoadBoard(boardf)
if mode == "dsn":
    ok = pcbnew.ExportSpecctraDSN(board, sys.argv[3])
    print("dsn:", ok)
elif mode == "lockdsn":
    for t in board.GetTracks():
        t.SetLocked(True)
    ok = pcbnew.ExportSpecctraDSN(board, sys.argv[3])
    print("lockdsn:", ok)
elif mode == "sesraw":
    ok = pcbnew.ImportSpecctraSES(board, sys.argv[3])
    pcbnew.SaveBoard(boardf, board)
    print("sesraw:", ok)
def add_refdes_silk(board):
    """Komponentnavne som SILKETRYK paa F.SilkS - OVERSIDEN, komponentsiden.
    ALDRIG i kobber: et navn paa F.Cu ville blive aetset som top-kobber. Silke
    er et separat lag, saa teksten maa gerne ligge over baner; vi undgaar kun
    pads (saa labels forbliver laeselige) og anden silketekst. Footprintets egen
    reference skjules, saa der staar praecis EEN label pr. komponent. Kandidater
    proeves over/under/venstre/hoejre; ingen plads -> tekst droppes (med log)."""
    from pcbnew import VECTOR2I, FromMM, ToMM

    bbox_brd = board.GetBoardEdgesBoundingBox()
    margin = FromMM(1.2)
    CLR = FromMM(0.6)                        # afstand til pads / anden silketekst

    obstacles = []                          # kun pads - silke over kobber er OK
    for fp in board.GetFootprints():
        fp.Reference().SetVisible(False)    # skjul default-ref -> ingen dublet-label
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
        txt.SetLayer(pcbnew.F_SilkS)
        txt.SetMirrored(False)               # laeses fra oversiden (komponentsiden)
        txt.SetTextSize(VECTOR2I(FromMM(1.0), FromMM(1.0)))
        txt.SetTextThickness(FromMM(0.15))
        board.Add(txt)
        cx, cy = fbb.Centre().x, fbb.Centre().y
        half_h = fbb.GetHeight() // 2
        half_w = fbb.GetWidth() // 2
        step = FromMM(1.2)
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
    print(f"  refdes paa F.SilkS: {placed} placeret, {skipped} droppet")

if mode == "ses":
    # idempotent: fjern evt. tidligere refdes-tekst og laser-zoner foer de
    # tilfoejes igen (ellers dublerer en gen-koersel dem). VIGTIGT: materialiser
    # BEGGE slettelister FOER nogen board.Remove() - et Remove() invaliderer
    # KiCads live SWIG-iteratorer (baade GetDrawings og Zones), som derefter
    # giver raa SwigPyObject'er (mangler GetNetCode). GetArea(i) er indeks-baseret
    # og robust mod det. Gammel kobber-refdes (F.Cu/B.Cu) ryddes ogsaa, saa aeldre
    # boards migrerer til silketryk.
    old_text = [d for d in board.GetDrawings()
                if d.GetClass() == "PCB_TEXT"
                and d.GetLayer() in (pcbnew.F_Cu, pcbnew.B_Cu,
                                     pcbnew.F_SilkS, pcbnew.B_SilkS)]
    old_zones = [board.GetArea(i) for i in range(board.GetAreaCount())]
    old_zones = [z for z in old_zones if z.GetNetCode() == 0]
    for t in old_text:
        board.Remove(t)
    for z in old_zones:
        board.Remove(z)
    # "-" som ses-sti = spring importen over (finish-only: tekst + zoner)
    if sys.argv[3] != "-":
        # Freerouting genudsender IKKE fixed wires i sin session - en raa import
        # ville altsaa SLETTE trin 1-kobberet. Tag en kopi foer importen og
        # genindsaet de baner der forsvandt.
        def sig(t):
            s, e = t.GetStart(), t.GetEnd()
            return (t.GetClass(), s.x, s.y, e.x, e.y, t.GetWidth(), t.GetLayer(),
                    t.GetNetCode())
        before = [(sig(t), t.Duplicate()) for t in board.GetTracks()]
        ok = pcbnew.ImportSpecctraSES(board, sys.argv[3])
        after = {sig(t) for t in board.GetTracks()}
        readded = 0
        for s, dup in before:
            if s not in after:
                board.Add(dup)
                readded += 1
        if readded:
            print(f"  genindsatte {readded} trin 1-baner efter SES-import")
    else:
        ok = "skip"
    add_refdes_silk(board)
    # Fiberlaser-zoner jf. DTU-PCB-prototyping-guiden: solid zone UDEN net og
    # UDEN pad-forbindelse pr. kobberlag. Laseren fjerner kun isolations-
    # kanalerne omkring baner/pads i stedet for alt kobberet.
    # B.Cu = etch-siden; F.Cu-zonen er kun relevant hvis toppen ogsaa aetses
    # (ved enkeltsidet bygges F.Cu-banerne som traadbroer i stedet).
    bbox = board.GetBoardEdgesBoundingBox()
    for layer in (pcbnew.B_Cu, pcbnew.F_Cu):
        zone = pcbnew.ZONE(board)
        zone.SetLayer(layer)
        zone.SetNetCode(0)                               # <no net>
        chain = pcbnew.SHAPE_LINE_CHAIN()
        for px, py in [(bbox.GetLeft(), bbox.GetTop()), (bbox.GetRight(), bbox.GetTop()),
                       (bbox.GetRight(), bbox.GetBottom()), (bbox.GetLeft(), bbox.GetBottom())]:
            chain.Append(px, py)
        chain.SetClosed(True)
        zone.Outline().AddOutline(chain)
        zone.SetLocalClearance(pcbnew.FromMM(0.8))       # guide: 0.75; 0.8 matcher netclass
        zone.SetMinThickness(pcbnew.FromMM(0.25))
        zone.SetPadConnection(pcbnew.ZONE_CONNECTION_NONE)
        zone.SetFillMode(pcbnew.ZONE_FILL_MODE_POLYGONS) # solid fill
        board.Add(zone)
    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())
    pcbnew.SaveBoard(boardf, board)
    print("ses:", ok, "+ laser-zoner (no net, begge lag)")
