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
4. **7 enkeltsidede PCB'er** (komponenter på top, kobber + GND-plane på B.Cu),
   autoroutet med Freerouting, **DRC: 0 fejl på alle**, render + DRC-rapport pr. board.

## ⚠️ To wiring-fejl FUNDET OG RETTET i drive_circuit (GUI-redigeringen d07ce2a)

1. **Friløbsdioden D1 lå med begge ben på +20 V** (motor+ er +20V-skinnen) — den
   beskyttede ingenting; induktiv kickback ville ramme Q1 uhindret. Anoden er
   flyttet til switch-knuden (M1.2/Q1.D), så D1 nu ligger over motoren.
2. **IR2110'ens HIN/SD/VSS/VS-ø var koblet sammen men IKKE til GND** (flydende
   logikreference + udefineret shutdown). Øen er lagt på GND.

Begge rettelser er lavet direkte i `.kicad_sch` (skemaet er fortsat source of truth);
`retrofit_pcb.py` dokumenterer indgrebet.

## Boards (alle: DRC 0 fejl, enkeltsidet B.Cu + GND-pour)

| Board | Fil | Str. (mm) | Uroutede luftledninger = **jumpere** |
|---|---|---|---|
| Buck | `converters/design/pcb/buck.kicad_pcb` | 120×56 | 1 (VOUT_5V) |
| Boost | `converters/design/pcb/boost.kicad_pcb` | 120×56 | 1 (VOUT_V2) |
| Motor-drive | `exp3a/pcb/drive_circuit.kicad_pcb` | 134×60 | 3 (+20V, D2-A, D2-K) |
| Feedback | `exp3a/pcb/feedback_circuit.kicad_pcb` | 116×50 | 4 (IN_P, 3× GND) |
| Rectifier | `system/pcb/rectifier.kicad_pcb` | 146×74 | 2 (V1) |
| MPPT/PV | `system/pcb/mppt.kicad_pcb` | 164×82 | 8 (2× PV_BUS, Q1_B, U1A_OUT, 4× GND) |
| Current sense | `system/pcb/current_sense.kicad_pcb` | 134×58 | 11 (FB1, FB3, RET3, U2B_FB, 7× GND) |

**Ærlig status:** buck/boost/rectifier/drive er reelt færdige (1–3 jumpere er normalt
for enkeltsidet). MPPT og current-sense har for mange jumpere til at være pæne — de
*virker* med trådbroer (de fleste er GND, som også kan tages som én bus-tråd på
toppen), men vil have godt af manuel omplacering + omroute i KiCad GUI, eller
dobbeltsidet print. Ratsnest er intakt i filerne, så de kan åbnes og routes videre direkte.

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
.\pcb_make_all.ps1 -Jar <sti>\freerouting-2.0.1.jar [-Boards buck,...]
```
netliste → `pcb_netlist_json.py` → `pcb_build.py` (placering, omrids, enkeltsidet)
→ DSN (F.Cu sættes til `power` så Freerouting kun bruger bagsiden) → Freerouting
2.0.1 (Java 21) → SES-import + GND-pour (`pcb_route.py`) → DRC + render.
NB: KiCad-stable popper en harmløs debug-assert-dialog under DSN-eksport
("non-closed outline") — klik **No**; `pcb_make_all` kører videre.

## Hvad I selv skal gøre

1. **Bestil efter `bom/footprint_map.csv`** + afklar spolen (470 µH-flaget).
2. Loddejumpere: træk de listede luftledninger som trådbroer på toppen (åbn boardet
   i KiCad og se ratsnest). MPPT/current-sense: overvej 30 min manuel omroute først.
3. **Mål de fysiske 4700 µF-kolber** (diameter/pitch) — footprintet antager D18/P7.5.
4. Verificér drive-rettelserne mod Exp 3A-sliden (D1-friløb + IR2110-ø på GND).
5. Print: tonertransfer/fræsning af B.Cu; alle huller bores (THT).
