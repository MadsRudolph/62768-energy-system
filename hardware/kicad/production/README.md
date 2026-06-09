# Produktion på XTool fiberlaseren — klar til kørsel

Følger [SimsesLab/DTU-PCB-prototyping](https://github.com/SimsesLab/DTU-PCB-prototyping)-guiden.
Alle 7 boards overholder guidens designregler og **DRC = 0 fejl**:

- Bane ≥ 1.0 mm, clearance 0.8 mm (netclass)
- Alt kobber på **B.Cu** (komponenter på toppen, THT)
- Solid **no-net fill zone** på B.Cu (pad-forbindelse: ingen) — laseren fjerner kun
  isolations-kanalerne, jf. guidens "Correcting your design for the Laser"
- DIP-footprints = **LongPads**-varianter (guidens shop-tabel)
- TO-220 = `energy_system:TO-220-3_Vertical_LaserPads` (pads klemt til 1.7 mm så
  ben-til-ben luften bliver 0.84 mm ≥ 0.8). MPPT'ens pass-transistor er skiftet
  BD139→**TIP41A** (TO-126's 2.28 mm pitch kan fysisk ikke overholde 0.8 mm)
- DXF eksporteret med guidens indstillinger: B.Cu + Edge.Cuts i én fil,
  drill marks **Small**, mm, ingen konturer

## Filer pr. board

`production/<board>/<board>.dxf` ← **denne fil importeres i xTool Creative Space**
`production/<board>/gerbers/` ← komplet Gerber-sæt + Excellon-drill (dokumentation/alternativ fab)

## Udskæringsmål (board + 2 mm jf. guiden — skær GERNE større, juster hellere efter)

| Board | Print (mm) | Skær mindst (mm) |
|---|---|---|
| buck | 121×56 | **123×58** |
| boost | 121×56 | **123×58** |
| drive_circuit | 134×60 | **136×62** |
| feedback_circuit | 118×50 | **120×52** |
| rectifier | 146×74 | **148×76** |
| mppt | 165×82 | **167×84** |
| current_sense | 134×58 | **136×60** |

## Loddejumpere pr. board (uroutede på enkeltsidet — træk som tråd på toppen)

| Board | Antal | Net |
|---|---|---|
| buck | 3 | GND ×1, SW ×1, R1-opto ×1 |
| boost | 1 | GND ×1 |
| drive_circuit | 5 | +20V ×1, GND ×4 |
| feedback_circuit | 7 | LED, OUT_PD, SERVO, GND ×4 |
| rectifier | 2 | GND ×1, V1 ×1 |
| mppt | 11 | PV_BUS ×3, V3_OUT ×2, GND ×2, PV_I, PV_V, U1A_OUT, U1B_FB |
| current_sense | 13 | GND ×6, I_SENSE2 ×2, +5V, FB2, I_SENSE1, I_SENSE3, U2B_FB |

Åbn boardet i KiCad og se ratsnest-linjerne for præcis placering. GND-jumperne kan
oftest samles som én bus-tråd. mppt/current_sense har mange — overvej 20–30 min
manuel omroute i KiCad GUI før gravering, ellers virker trådbroer fint.

## Tjekliste på laseren (fra guiden — læs hele guiden først!)

1. Sikkerhedskursus gennemført? Ellers STOP.
2. Skær board efter tabellen ovenfor (IKKE de blå-film-plader; IKKE dobbeltsidet).
3. 400-grit sandpapir, let — kun oxidlaget af.
4. xTool Creative Space → Import image → vælg `<board>.dxf`.
5. **FLIP designet (spejlvend!)** og gør det **compound**.
6. Engrave-mode, Output grøn. **Banerne skal være HVIDE, området omkring SORT**
   (sort = fjernes).
7. Huller: *Edit compound* → slet hver hul-markering så de bliver sorte
   (standard-importen graverer dem ikke).
8. Board på offerpladen, så centreret som muligt. *Framing* → juster så rammen
   IKKE går ud over kanten. For stramt? Skær et større stykke.
9. *Auto height adjustment*.
10. Preset **PCB** under Engrave-fanen — tjek parametre mod opslagene/TA'erne.
11. Sidste tjek: spejlvendt? hvide baner? parametre OK? → *Process*.
12. Kig IKKE ind i brændpunktet. Bagefter: bor hullerne (drill marks er graveret
    som små centreringsmærker), skær til endeligt mål.
