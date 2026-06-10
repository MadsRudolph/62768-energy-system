# Produktion på XTool fiberlaseren — klar til kørsel

Følger [SimsesLab/DTU-PCB-prototyping](https://github.com/SimsesLab/DTU-PCB-prototyping)-guiden.
Alle 7 boards overholder guidens designregler, **DRC = 0 fejl** og **0 uroutede net**:

- Bane ≥ 1.0 mm, clearance 0.8 mm (netclass — ligger i hvert boards `.kicad_pro`)
- **To-trins-routet:** alt der kan, ligger på **B.Cu** (etch-siden); kun de kryds
  der er umulige enkeltsidet, ligger på **F.Cu** (toppen) — se tabellen nederst
- Solid **no-net fill zone** pr. kobberlag (pad-forbindelse: ingen) — laseren
  fjerner kun isolations-kanalerne, jf. guidens "Correcting your design for the Laser"
- DIP **LongPads** + `energy_system:*_LaserPads` TO-220 (luft 0.84 mm ≥ 0.8)
- DXF eksporteret med guidens indstillinger: kobberlag + Edge.Cuts i én fil,
  drill marks **Small**, mm, ingen konturer

## Filer pr. board

| Fil | Hvad | Spejlvendes i xTool? |
|---|---|---|
| `<board>.dxf` | **BUNDEN** (B.Cu) — hoved-etch | **JA** |
| `<board>_top_cu.dxf` | **TOPPEN** (F.Cu) — trådbro-plan ELLER side 2 ved dobbeltsidet | NEJ |
| `<board>_silk_top.dxf` | valgfri topside-tekst (alle refdes) | NEJ |
| `gerbers/` | komplet Gerber-sæt (begge lag) + Excellon-drill | — |

## Top-laget: to måder at bygge det på

Alle net er routet — toppen indeholder kun det, der ikke kunne ligge enkeltsidet:

| Board | Top-baner | Længde | Vias | Net på toppen |
|---|---|---|---|---|
| buck | 3 | 33 mm | 0 | SW |
| boost | 4 | 79 mm | 0 | VIN_5V, VOUT_V2 |
| drive_circuit | 43 | 263 mm | 1 | +15V, +20V, GND, D1-A, D2-A, D2-K, U2-LIN (manuel reroute) |
| feedback_circuit | 15 | 96 mm | 0 | GND, LED, OUT_PD |
| rectifier | 2 | 22 mm | 0 | V1 |
| mppt | 19 | 174 mm | 0 | GND, PV_V, U1A_OUT, U1B_FB |
| current_sense | 18 | 99 mm | 0 | +5V, FB1, GND, RET1, U2B_FB |

**Mulighed A — enkeltsidet etch + trådbroer (anbefalet, hurtigst):** ets kun
bunden (`<board>.dxf`). Byg topbanerne som trådbroer mellem THT-benene —
`<board>_top_cu.dxf` ER tegningen (åbn evt. boardet i KiCad og se F.Cu-laget).
Vias (kun drive/feedback/mppt, 1–2 stk.) = bor hullet og lod en tråd igennem
til begge sider.

**Mulighed B — dobbeltsidet etch:** ets bunden, vend pladen, justér og ets
toppen med `<board>_top_cu.dxf` (IKKE spejlvendt). Guiden advarer: dobbeltsidet
er på eget ansvar/uprøvet — flip-justering er den svære del. Vias loddes som tråd.

## Komponentnavne på printet

Refdes (R1, U1 …) ligger som **kobber-tekst på F.Cu — OVERSIDEN, komponentsiden**
ved hver komponent (ikke spejlvendt). De er med i `<board>_top_cu.dxf`:
- **Mulighed B (dobbeltsidet):** navnene ætses i top-kobberet — færdig.
- **Mulighed A (enkeltsidet):** gravér `_top_cu.dxf` let på oversiden FØR
  kobberkørslen — så får du navnene OG trådbro-planen tegnet på toppen i én
  arbejdsgang. (Alternativt `_silk_top.dxf`, som kun har navne.)
Enkelte navne er flyttet/droppet i de tætteste klynger (fremgår af
`gerbers/<board>-F_Fab.gbr`).

## Udskæringsmål — positionerings-jiggen

**ALLE 7 boards har samme format:** edge cuts **104×104 mm**, skåret kobberplade
**præcis 109×109 mm** (jiggens åbning). Det giver 2.5 mm rand hele vejen rundt
mellem plade og print — efter gravering skæres/files ned til edge cuts-linjen.

## Tjekliste på laseren (fra guiden — læs hele guiden først!)

1. Sikkerhedskursus gennemført? Ellers STOP.
2. Skær kobberpladen til **præcis 109×109 mm** — jiggens åbning (IKKE de
   blå-film-plader; IKKE dobbeltsidet plade medmindre du kører Mulighed B).
3. 400-grit sandpapir, let — kun oxidlaget af.
4. xTool Creative Space → Import image → vælg `<board>.dxf`.
5. **FLIP designet (spejlvend!)** og gør det **compound**. (Kun bund-DXF'en!)
6. Engrave-mode, Output grøn. **Banerne skal være HVIDE, området omkring SORT**
   (sort = fjernes).
7. Huller: *Edit compound* → slet hver hul-markering så de bliver sorte
   (standard-importen graverer dem ikke).
8. Pladen i positionerings-jiggen (109×109-åbningen). *Framing* → juster så
   rammen IKKE går ud over kanten — der er 2.5 mm rand til edge cuts-linjen.
9. *Auto height adjustment*.
10. Preset **PCB** under Engrave-fanen — tjek parametre mod opslagene/TA'erne.
11. Sidste tjek: spejlvendt? hvide baner? parametre OK? → *Process*.
12. Kig IKKE ind i brændpunktet. Bagefter: bor hullerne (drill marks er graveret
    som små centreringsmærker), skær til endeligt mål, og byg toppen
    (trådbroer jf. Mulighed A — eller anden etch jf. Mulighed B).
