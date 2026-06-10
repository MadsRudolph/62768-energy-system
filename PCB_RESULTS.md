# PCB & footprint results — 62768 energy system

Status efter hardware/PCB-fasen (jf. `PCB_HANDOFF.md`). Alt ligger i `hardware/kicad/`.

## Hvad der er lavet

1. **3 nye system-skemaer** i `hardware/kicad/system/` (ERC: 0 fejl):
   - `rectifier.kicad_sch` — 3-faset 6-diode bro (1N4006) + 3×4700 µF ≈ 14.1 mF → V1 (Krav 1–3)
   - `mppt.kicad_sch` — PV → 1N5817 → 14.1 mF MPPT-cap → **diskret** 5 V-regulator
     (LM358 + BZX55C5V1 + BD139) → lager, + PV-V/I-sense til Arduino (Krav 9, 11)
   - `current_sense.kicad_sch` — 3 kanaler lavside 1 Ω-shunt + LM358 ×10.09 → ADC (Krav 10)
2. **Alle 7 skemaer har footprints** (KiCad stock, verificeret mod datablade) og
   **PCB-stik** (skrueterminaler til effekt, headers til signal). Sim-artefakterne
   `V_in`/`Rload` i buck/boost er erstattet af terminaler.
3. **BOM:** `hardware/kicad/bom/footprint_map.csv` — ref → indkøbsdel (shop/kit) →
   footprint → noter. **Alle substitutioner er flagget der.**
4. **7 PCB'er, alle net routet** (komponenter på top; B.Cu er hoved-etchen, F.Cu kun de få nødvendige kryds = trådbroer/side 2), autoroutet med Freerouting i to trin, **DRC: 0 fejl og 0 uroutede på alle**, render + DRC-rapport pr. board.

## ⚠️ To wiring-fejl FUNDET OG RETTET i drive_circuit (GUI-redigeringen d07ce2a)

1. **Friløbsdioden D1 lå med begge ben på +20 V** (motor+ er +20V-skinnen) — den
   beskyttede ingenting; induktiv kickback ville ramme Q1 uhindret. Anoden er
   flyttet til switch-knuden (M1.2/Q1.D), så D1 nu ligger over motoren.
2. **IR2110'ens HIN/SD/VSS/VS-ø var koblet sammen men IKKE til GND** (flydende
   logikreference + udefineret shutdown). Øen er lagt på GND.

Begge rettelser er lavet direkte i `.kicad_sch` (skemaet er fortsat source of truth);
`retrofit_pcb.py` dokumenterer indgrebet.

## Boards — PRODUKTIONSKLAR til XTool fiberlaser (DRC 0 fejl på alle 7)

Designreglerne fra [SimsesLab/DTU-PCB-prototyping](https://github.com/SimsesLab/DTU-PCB-prototyping)
er anvendt: bane 1.0 mm, clearance 0.8 mm, solid no-net laser-zone på B.Cu,
DIP **LongPads**, TO-220 med 1.7 mm pads (`energy_system:*_LaserPads`, luft 0.84 mm).
**Laser-filer (DXF) + Gerbers + udskæringsmål + jumperliste + xTool-tjekliste:**
→ `hardware/kicad/production/` (README dér er køreplanen).

Komponentnavnene (refdes) er graveret med som **kobber-tekst på B.Cu** ved hver
komponent (læsbare fra loddesiden); en valgfri topside-tekst-DXF ligger også i
`production/` pr. board.

Hvert board er nu et **KiCad-projekt**: `.kicad_pro` + `.kicad_sch` + `.kicad_pcb`
ligger sammen med samme basenavn — åbn `.kicad_pro`-filen, så er skema og PCB
linket (skift editor med knappen). Projektfilen indeholder laser-netclassen
(0.8/1.0 mm), så manuel routing i GUI'en bruger de rigtige regler. Ved *Update
PCB from Schematic*: sæt flueben i **"Re-link footprints to schematic symbols
based on their reference designators"** (boardene er bygget scriptet, så
UUID-links findes ikke første gang).

| Board | Projekt | Str. (mm) | Top-baner (trådbroer/side 2) |
|---|---|---|---|
| Buck | `boards/buck/buck.kicad_pro` | 121×56 | 4 (33 mm) |
| Boost | `boards/boost/boost.kicad_pro` | 121×56 | 12 (144 mm) |
| Motor-drive | `boards/drive_circuit/drive_circuit.kicad_pro` | 134×60 | 17 (104 mm) + 1 via |
| Feedback | `boards/feedback_circuit/feedback_circuit.kicad_pro` | 118×50 | 11 (72 mm) + 1 via |
| Rectifier | `boards/rectifier/rectifier.kicad_pro` | 146×74 | 2 (27 mm) |
| MPPT/PV | `boards/mppt/mppt.kicad_pro` | 140×68 | 27 (149 mm) + 2 vias |
| Current sense | `boards/current_sense/current_sense.kicad_pro` | 120×80 | 17 (113 mm) |

**Status:** ALLE net er routet (0 uroutede, DRC 0 fejl). To-trins-routing: bunden (B.Cu) er hoved-etchen; toppen (F.Cu) indeholder kun de kryds der er umulige enkeltsidet — byg dem som trådbroer (anbefalet) eller ets toppen som side 2. Se `hardware/kicad/production/README.md`.

**To fejl mere fanget i produktions-passet:**
- Buck/boost brugte det generiske `Device:Q_NMOS`-symbol med **bogstav-pinnumre
  (G/D/S)** — TO-220-footprintens pads hedder 1/2/3, så MOSFET'ens pads fik ALDRIG
  net i de første board-versioner (no-net pads tæller ikke som "unconnected"!).
  Fixet med G/D/S→1/2/3-mapping + en fail-hard kontrol i `pcb_build.py`.
- MPPT'ens pass-transistor er skiftet **BD139 → TIP41A** (shoppen har den):
  TO-126's 2.28 mm pitch kan fysisk ikke overholde 0.8 mm clearance, og TO-220
  er alligevel bedre til de ~7 W.

## Substitutioner (fra footprint_map.csv — bestil efter den)

| Skema-del | Køb i stedet | Note |
|---|---|---|
| 1N5819 | **1N5817** | shoppen har kun 5817; OK ved 15 V bus |
| 1N4007 | **1N4006** | 800 V rigeligt ved 20 V |
| IRF530N/IRF540N | **IRF530/IRF540** | samme die/pinout, uden N-suffix i shoppen |
| 330 Ω / 33 k | **332R / 33k2** | E96-shop; 0.6 % afvigelse |
| **L 470 µH** | ⚠️ **findes ikke** | nærmeste 270 µH (ukendt strøm) eller 2.7 mH, eller vikl på shop-toroid. **Genberegn ripple** (Lec 2) før valg |
| 15 mF | **3× 4700 µF/50 V** | = 14.1 mF |

**Kit-dele uden shop-ækvivalent (flagget, IKKE substitueret):** IR2110 (DIP-14),
IL300 (DIP-8, **ingen erstatning** — servoloopet kræver den), ILD74 (DIP-8; 4N25 er
IKKE drop-in), MCP601 (PDIP-8). Alle pakker er verificeret i `docs/datasheets/`.
Brug DIP-sokler fra shoppen til alle IC'er.

## Vigtige el-noter

- **Buck J4 (+12V_SW) er refereret til SW-knuden**, ikke GND — high-side switch
  kræver flydende/bootstrap gate-forsyning. Sådan er teamets opto-gate-drive tegnet;
  overvej IR2110-løsningen fra drive-kredsen, jf. `docs/system-architecture.md`.
- **MPPT: BD139 afsætter op til ~7 W** ved fuld PV-strøm (lineær 17→5 V) —
  **køleplade påkrævet**, eller erstat med buck (Krav 17 tillader det).
- Current-sense er **lavside**: grenens returledning ind på J*k* pin 1, system-GND
  videre fra pin 2. PV-strømkanalen på MPPT-boardet er inverterende (gain −9.09).
- Feedback-boardet deler +5 V/GND på begge sider af IL300 — som teamets sim;
  galvanisk isolation er der ikke (bevidst valg, bare vid det).

## Værktøjskæde (reproducérbart)

```
.\tools\pcb_make_all.ps1 -Jar <sti>\freerouting-2.0.1.jar [-Boards buck,...]
```
netliste → pcb_netlist_json.py → pcb_build.py (placering, omrids, .kicad_pro) →
TRIN 1: DSN med F.Cu maskeret som power-lag → Freerouting 2.0.1 (Java 21) → import →
TRIN 2: bagside-kobberet låses (type fix) → Freerouting med toppen tilladt →
merge-import + refdes-kobbertekst + laser-zoner (pcb_route.py) → DRC + render.
NB: KiCad-stable popper en harmløs debug-assert-dialog under DSN-eksport
("non-closed outline") — klik **No**; `pcb_make_all` kører videre.

## Hvad I selv skal gøre

1. **Produktion på fiberlaseren:** følg `hardware/kicad/production/README.md` —
   DXF-filerne ligger klar pr. board, med udskæringsmål og xTool-tjekliste.
2. **Bestil efter `bom/footprint_map.csv`** + afklar spolen (470 µH-flaget).
3. Loddejumpere: træk de listede luftledninger som trådbroer på toppen (åbn boardet
   i KiCad og se ratsnest). MPPT/current-sense: overvej 30 min manuel omroute først.
4. **Mål de fysiske 4700 µF-kolber** (diameter/pitch) — footprintet antager D18/P7.5.
5. Verificér drive-rettelserne mod Exp 3A-sliden (D1-friløb + IR2110-ø på GND).
6. Efter gravering: bor hullerne (drill marks er små centreringsmærker), skær til mål.
