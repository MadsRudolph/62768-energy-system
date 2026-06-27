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

Komponentnavnene (refdes) er graveret som **kobber-tekst på OVERSIDEN (F.Cu)** ved hver komponent — de følger med i `<board>_top_cu.dxf` (ætses ved dobbeltsidet, eller graveres på toppen sammen med trådbro-planen ved enkeltsidet).

Hvert board er nu et **KiCad-projekt**: `.kicad_pro` + `.kicad_sch` + `.kicad_pcb`
ligger sammen med samme basenavn — åbn `.kicad_pro`-filen, så er skema og PCB
linket (skift editor med knappen). Projektfilen indeholder laser-netclassen
(0.8/1.0 mm), så manuel routing i GUI'en bruger de rigtige regler. Ved *Update
PCB from Schematic*: sæt flueben i **"Re-link footprints to schematic symbols
based on their reference designators"** (boardene er bygget scriptet, så
UUID-links findes ikke første gang).

**ALLE boards er 104×104 mm** (positionerings-jiggens format: kobberplade skæres
til præcis 109×109, edge cuts 104×104 = 2.5 mm rand). Kompakt placering (5 mm
komponent-gab), klyngen **centreret** i omridset — ingen komponenter klods op
ad edge cuts. drive_circuit er håndplaceret (GUI) og derefter to-trins-routet.

| Board | Projekt | Top-baner (trådbroer/side 2) |
|---|---|---|
| Buck | `boards/buck/buck.kicad_pro` | **0 — helt enkeltsidet** |
| **Buck v2 (IR2110 high-side)** | `boards/buck/buck_v2/buck_v2.kicad_pro` | 21 (116 mm) |
| Boost | `boards/boost/boost.kicad_pro` | 2 (35 mm) |
| **Boost v2 (IR2110)** | `boards/boost/boost_v2/boost_v2.kicad_pro` | 17 (255 mm) |
| Motor-drive | `boards/drive_circuit/drive_circuit.kicad_pro` | 20 (135 mm) |
| Feedback | `boards/feedback_circuit/feedback_circuit.kicad_pro` | 15 (73 mm) |
| Rectifier | `boards/rectifier/rectifier.kicad_pro` | 7 (60 mm) |
| MPPT/PV (lineær) | `boards/mppt/mppt.kicad_pro` | 15 (77 mm) |
| **MPPT buck (IR2110 high-side)** | `boards/mppt_buck/mppt_buck.kicad_pro` | 8 (65 mm) |
| Current sense | `boards/current_sense/current_sense.kicad_pro` | 8 (68 mm) |
| **C2000 feedback (TI-port, 3.3 V)** | `boards/c2000_feedback/c2000_feedback.kicad_pro` | 12 trådbroer |

Ingen vias på nogen boards (kvadrat-formatet + kompakt placering routede
bedre end de gamle aflange boards).

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
| **L 470 µH** | **egen-viklet toroid** | målt med skydelære: OD 34.5 mm stående på kant, ben-pitch 28.2 mm c-c, ben Ø1.6 → footprint `energy_system:L_Toroid_Vertical_L34.5mm_W15.0mm_P28.20mm_LaserPads` (buck+boost re-routet, boards nu 145×72). **Genberegn ripple** (Lec 2) med den viklede L |
| 15 mF | **3× 4700 µF/50 V** | = 14.1 mF |

**Kit-dele uden shop-ækvivalent (flagget, IKKE substitueret):** IR2110 (DIP-14),
IL300 (DIP-8, **ingen erstatning** — servoloopet kræver den), ILD74 (DIP-8; 4N25 er
IKKE drop-in), MCP601 (PDIP-8). Alle pakker er verificeret i `docs/datasheets/`.
Brug DIP-sokler fra shoppen til alle IC'er.

## Vigtige el-noter

- **Buck J4 (+12V_SW) er refereret til SW-knuden**, ikke GND — high-side switch
  kræver flydende/bootstrap gate-forsyning. Sådan er teamets opto-gate-drive tegnet;
  overvej IR2110-løsningen fra drive-kredsen, jf. `docs/system-architecture.md`.
- **Boost v2 = boost med rigtig IR2110 gate-driver** (`boards/boost/boost_v2/`).
  Den gamle boost drev MOSFET-gaten direkte fra en 4N25-opto; optoens ~20 µs
  sluk-tid strakte dutyen voldsomt (20 % → 65 % @ 10 kHz), så boardet kun duede ved
  1–2 kHz med stor ripple. v2 indsætter kæden **opto (CNY17) → IR2110 LO → R3‖D2 →
  gate** (lavside, ingen bootstrap), så gaten slås hårdt høj *og* lav på ns — duelig
  ved 20–50 kHz med ren duty. Effekttrinet (L1/M1/D1/C1) er uændret. Separat **+15 V**
  drive-forsyning (J4), isoleret PWM-jord (GND_MCU) bevaret. ERC 0 fejl, netliste
  verificeret pin-for-pin, DRC 0 fejl/0 uroutede (1 benign track_dangling-stump).
  Genereres med `tools/generators/build_boost_v2.py` (schbuild). Production-DXF +
  Gerbers i `production/boost_v2/`.
- **Buck v2 = buck med IR2110 HIGH-SIDE driver** (`boards/buck/buck_v2/`). Den gamle
  high-side-drive var en 4N25-opto med et 9V-batteri flydende paa SW-knuden — langsom og
  klodset. v2 beholder hele front-enden (LM7805 -> NE555 + RV1/trimmer timing, SW1 valg
  555/ekstern PWM, opto-LED) og effekttrinet, men erstatter selve gate-driveren:
  opto (5V PWM, level-shiftet til ~15V) -> **IR2110 HIN** ; **HO -> R5(10)||D5 -> gate** ;
  **VS -> SW** ; bootstrap **D4(+15V->VB) + C7(VB->VS)** ; LIN/SD til GND. 9V-batteriet er
  fjernet, +15V driver-forsyning via J5 (jordrefereret). R4 = gate->SW pulldown.
  Skemaet er **GUI-lavet** (source of truth) og redigeret kirurgisk med
  `tools/generators/patch_buck_v2_ir2110.py` (sexpdata) — front-enden er uroert.
  ERC 0 fejl, netliste verificeret pin-for-pin, DRC 0 fejl/0 uroutede (4 benigne
  track_dangling-stumper). 31 dele, haandplaceret (toroiden L1 fylder ~35x35 mm =
  egen kvadrant). Production-DXF + Gerbers i `production/buck_v2/`.
- **MPPT buck = switching buck der erstatter den lineaere MPPT** (`boards/mppt_buck/`).
  Den gamle MPPT var lineaer (TIP41A pass-transistor + LM358-servo) og braendte op til
  ~7 W af; rapporten (`solcelle-mppt.tex`) beskriver i forvejen en **buck styret af
  Arduino P&O**. Dette board er den buck: PV (MPP 17.6 V / 0.57 A / ~10 W) → high-side
  IRF530 → friloeb → L → 5 V-lager (1 F). **Samme IR2110 high-side driver som buck_v2,
  men UDEN 555** — dutyen kommer 100 % fra Arduinoens PWM gennem opto → IR2110 HIN.
  Strøm/spaendingsmaaling er **eksternt** (INA219). **Effekt dimensioneret til ~2 A**
  (Vout 5 V): friloebsdioden er opgraderet fra 1N5819 (1 A) til en **≥3 A Schottky**
  (1N5822 paa DO-201AD — **shoppen har ingen ≥3 A Schottky, bestil 1N5822/SB540**), og
  L1 = 150 µH ≈ 31 kHz (vikles til den faktiske PWM-frekvens; kerne skal taale ≥2.5 A
  peak). ERC 0 fejl, netliste verificeret mod high-side-acceptkriterierne, DRC 0 fejl/
  0 uroutede/**0 vias** (2 benigne track_dangling), 8 traadbroer/65 mm. Genereres med
  `tools/generators/build_mppt_buck.py`. Production-DXF + Gerbers i `production/mppt_buck/`.
  **Verificer foer aetsning:** PWM-frekvens (saetter L), de fysiske kondensator-pitch
  (PV-bulk, boot-cap), og toroidens strømrating — se `AUDIT_buck_boost_ir2110.md` §8.
- **C2000 feedback/sensorprint (TI-port)** (`boards/c2000_feedback/`). **NB (2026-06-27):
  revideret til det integrerede system-board** — nu KUN 3 spændingskanaler (V1/LOAD/STORE →
  ADC); strømkanalerne I1/I2/I3 og PWM-pass er FJERNET (strøm måles af current_sense → Arduino;
  C2000 EPWM går direkte til konverter-optoerne). ERC 0. Se
  `docs/superpowers/specs/2026-06-27-system-integrated-pcb-interface-contract.md`.
  Den oprindelige 6-kanals standalone-beskrivelse herunder er historik. Front-end mellem
  effektsystemet og LAUNCHXL-F28027 — **alt skaleret til 0–3.3 V** (C2000 ADC abs-max 3.3 V,
  modsat de 5 V-skalerede current_sense/feedback-print). 6 kanaler + PWM-pass:
  V1/V2/V3-delere (÷11 / ÷7 / ÷3) med 1k serie + **3.0 V zener-klemme** + 10n;
  I1/I2 lavside 1R-shunt + **MCP601 ikke-inv.** (gain 7.5 / 10), I3 bidir 1R-shunt +
  MCP601 **differensforstærker** (gain 5, 1.65 V midt-skala); EPWM1A → 220R → drivkreds-opto.
  **MCP601 valgt frem for LM358:** ved 3V3-forsyning når LM358 kun ~1.8 V ud, MCP601 ~3.3 V.
  Skrueterminaler (effekt/retur) på venstre kant, korte 1×2/1×3-headers til LaunchPad på
  højre. Genereres med `tools/generators/build_c2000_feedback.py`. ERC 0 fejl, netliste
  verificeret pin-for-pin mod `docs/c2000-pinmap.md`, **DRC 0 fejl / 0 uroutede / 0 vias**,
  **12 trådbroer**. NB: boardet er for tæt til auto-placeringen (autoroutede 1–5 uroutede,
  ikke-deterministisk) — det bruger en **håndlavet signalflow-placering** i `PLACE`-dicten
  i `tools/pcb_build.py` (og skill-kopien), så routingen er stabil. Production-DXF + Gerbers i
  `production/c2000_feedback/`.
  **Verificér før ætsning:** delere/gains mod de faktiske rails, og at EPWM1A/ADC-ben matcher
  `c2000-pinmap.md` (header-rækkefølgen J2/J4/J6/J8 = +3V3·GND / V1·V2·V3 / I1·I2·I3 / PWM).
- **MPPT: BD139 afsætter op til ~7 W** ved fuld PV-strøm (lineær 17→5 V) —
  **køleplade påkrævet**, eller erstat med buck (Krav 17 tillader det).
- Current-sense er **lavside**: grenens returledning ind på J*k* pin 1, system-GND
  videre fra pin 2. PV-strømkanalen på MPPT-boardet er inverterende (gain −9.09).
- Feedback-boardet deler +5 V/GND på begge sider af IL300 — som teamets sim;
  galvanisk isolation er der ikke (bevidst valg, bare vid det).

## Værktøjskæde (reproducérbart)

```
.\tools\pcb_make_all.ps1 [-Jar <sti>\freerouting-1.9.0.jar] [-Boards buck,...]
```
netliste → pcb_netlist_json.py → pcb_build.py (placering, omrids, .kicad_pro) →
TRIN 1: DSN med F.Cu maskeret som power-lag → Freerouting 1.9.0 (Java 21) → import →
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
