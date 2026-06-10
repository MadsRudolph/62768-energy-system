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
`production/<board>/<board>_silk_top.dxf` ← *valgfri* topside-tekst (se nedenfor)
`production/<board>/gerbers/` ← komplet Gerber-sæt + Excellon-drill (dokumentation/alternativ fab)

## Komponentnavne på printet

Reference-navnene (R1, C2, U1 …) er lagt som **kobber-tekst på B.Cu** ved siden af
hver komponent — de graveres automatisk med i samme kørsel som banerne og kan
læses fra loddesiden (spejlvendt i KiCad, så de vender rigtigt på det færdige
print). Placeringen er kollisions-checket mod baner/pads; i de tætteste områder
er enkelte navne droppet (1-2 pr. board i de taetteste klynger) — de fremgår af bestykningstegningen
(`gerbers/<board>-F_Fab.gbr`) og af KiCad-filen.

**Valgfrit — navne på OVERSIDEN (komponentsiden):** `<board>_silk_top.dxf`
indeholder F.Silkscreen (ALLE refdes) + omrids. Den kan graveres let på
oversiden FØR kobberkørslen: gravér toppen, vend pladen, kør kobber-DXF'en.
OBS: silk-top-filen må **IKKE spejlvendes** (den køres direkte fra toppen), og
flip-justeringen er manuel — spring den over hvis tiden er knap; B.Cu-navnene
er nok til bestykning.

## Udskæringsmål (board + 2 mm jf. guiden — skær GERNE større, juster hellere efter)

| Board | Print (mm) | Skær mindst (mm) |
|---|---|---|
| buck | 121×56 | **123×58** |
| boost | 121×56 | **123×58** |
| drive_circuit | 134×60 | **136×62** |
| feedback_circuit | 118×50 | **120×52** |
| rectifier | 146×74 | **148×76** |
| mppt | 140×68 | **142×70** |
| current_sense | 120×80 | **122×82** |

## Loddejumpere pr. board (uroutede på enkeltsidet — træk som tråd på toppen)

| Board | Antal | Net |
|---|---|---|
| buck | 2 | VIN_15V ×1, VOUT_5V ×1 |
| boost | 4 | VOUT_V2, GATE, GND_MCU, R1-opto |
| drive_circuit | 5 | +15V, +20V, GND ×2, D2-K |
| feedback_circuit | 7 | +5V, IN_P, OUT_PD, GND ×4 |
| rectifier | 5 | PH_B, GND ×1, V1 ×3 |
| mppt | 7 | GND ×3, PV_BUS, Q1_B, U1B_FB, VREF |
| current_sense | 10 | GND ×6, +5V ×3, U2B_FB |

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
