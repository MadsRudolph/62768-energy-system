# System integrated PCB — interface contract (split-MCU, double-sided CNC)

**Date:** 2026-06-27
**Status:** approved (Phase-0 locked), pending build
**Supersedes:** the board-set, MCU, and Arduino-hub parts of
`2026-06-21-system-hierarchical-schematic-design.md`. The hierarchical-schematic
*mechanism* (Phase-1 manual labels → Phase-2 scripted top sheet → Phase-3 ERC) from
that doc still stands; only the contents below change.

## What changed vs the 2026-06-21 contract
1. **Board set is 5 sheets** — `mppt` (linear) → `mppt_buck` (switching); `c2000_feedback`
   added (the C2000 analog front-end); the discrete **`current_sense` board is DROPPED**
   (current sensing is done with an INA219 — see #3). Boost = `boost_v2_mill`.
2. **Split MCU** (was Arduino-only): **Arduino Nano (5 V)** does sensing/telemetry, **TI
   C2000 LaunchPad (3.3 V)** does all PID. The single "Arduino hub" becomes **two MCU
   connectors**.
3. **Current sensing = a single INA219** on **PV current** (reqs 9/10, teacher-approved IC),
   **on-board via a 6-pin header**, on I2C → Arduino. No discrete shunt/amp board, no analog
   `I_SENSE1/2/3`. (Motor/load/store currents are not separately sensed.)
6. **The two MCUs are FULLY INDEPENDENT — no inter-MCU communication.** Arduino owns the whole
   MPPT loop (reads PV INA219 + drives `mppt_buck` PWM directly at 5 V); C2000 drives only
   motor-buck + boost. No `MPP_SET`, no level-shifter. Each MCU has its own sensors + actuators.
4. **`c2000_feedback` rework** (DONE): keep the 3 voltage-divider channels; **removed the
   I1/I2/I3 current channels** and the **single PWM pass** (C2000 EPWM goes straight to each
   converter's existing opto front-end). ERC 0.
5. Manufacturing = **in-house SRM-20 CNC, double-sided** (see
   `hardware/kicad/HANDOFF_system_double_sided_pcb.md`): track ≥1.0 mm, clearance 0.9–1.0 mm,
   hand-stitched vias, GND pour both layers, KiCad 10. Netclass already written to
   `hardware/kicad/system/system.kicad_pro` (clearance 1.0, track 1.0, via 2.4/1.0).

## Board set — 5 hierarchical sheets
| Sheet | File | Role | Gnd domain |
|---|---|---|---|
| Motor Power | `boards/motor_power/motor_power.kicad_sch` | rectifier + V1 buck + motor drive | power GND |
| Motor Feedback | `boards/motor_feedback/motor_feedback.kicad_sch` | V1 sense (IL300-isolated) → Arduino | GND ↔ GND_MCU |
| Boost | `boards/boost/boost_v2_mill/boost_v2_mill.kicad_sch` | store → pulsing load | power GND + GND_MCU (opto) |
| MPPT buck | `boards/mppt_buck/mppt_buck.kicad_sch` | PV → 5 V store (switching) | power GND + GND_MCU (opto) |
| C2000 Feedback | `boards/c2000_feedback/c2000_feedback.kicad_sch` | V1/LOAD/STORE dividers → C2000 ADC | power GND |

**Not a sheet:** the **PV INA219** is a breakout on a 6-pin header, added at the top sheet
(in-line on the PV path + I2C to Arduino). The discrete `current_sense` board is dropped.

## Interface contract — per board (real nets, verified against the schematics/generators)
Each row = a **hierarchical label** placed on the named net (becomes a top-sheet pin).
The "contract net" column is the system-bus name to wire to at the top level.

### motor_power (J1..J7)
| Board net / pin | Contract net | Dir |
|---|---|---|
| J1.1 `PWM_MOTOR` ("PWM fra MCU") | `PWM_MOTOR` | input ← C2000 EPWM |
| J2.1 `PWM_MOTOR_ALT` | `PWM_MOTOR_ALT` | input (alt/MCP) |
| J3 motor out (`+15V1` / `Net-(D4-A)`) | `MOTOR_A` / `MOTOR_B` | output (off-board) |
| J4/J5 3-phase (3 nets) | `3PH_U` / `3PH_V` / `3PH_W` | input (off-board) |
| `V1` (J6.2 / J7.1) | `V1` | output (15 V bus) |
| `+5v` (J7.3) | `+5V_PWR` | input |
| `GND` | `GND` | power |

### motor_feedback (J1 = power side, J3 = MCU side)
| Board net | Contract net | Dir |
|---|---|---|
| `V1` (J1.1) | `V1` | input |
| `GND` (J1.2) | `GND` | power |
| `+5V` (J1.3) | `+5V_PWR` | input |
| `MCU` (J3.1) | `MCU_V1` | output → Arduino ADC |
| `GND_MCU` (J3.2) | `GND_MCU` | power |
| `+5V_MCU` (J3.3) | `+5V_MCU` | input |

### boost_v2 (J1 store in, J2 load, J3 PWM, J4 gate supply)
| Board global label | Contract net | Dir |
|---|---|---|
| `VIN_5V` (J1.1) | `STORE` | input |
| `VOUT_V2` (J2.1) | `LOAD` | output (off-board) |
| `PWM` (J3.1) | `PWM_BOOST` | input ← C2000 EPWM |
| `GND_MCU` (J3.2) | `GND_MCU` | power |
| `+15V` (J4.1) | `+15V_GATE` | input |
| `GND` | `GND` | power |

### mppt_buck (J1 PV via INA219, J2 store out, J3 PWM, J4 gate supply)
| Board global label | Contract net | Dir |
|---|---|---|
| `VPV` (J1.1) | `PV_BUCK_IN` | input ← INA219 OUT |
| `VOUT_5V` (J2.1) | `STORE` | output |
| `PWM` (J3.1) | `PWM_MPPT` | input ← **Arduino** (5 V) |
| `GND_MCU` (J3.2) | `GND_MCU` | power |
| `+15V` (J4.1) | `+15V_GATE` | input |
| `GND` | `GND` | power |
| `SW` | (probe only) | — switch node |

### PV INA219 (breakout on 6-pin header — top-sheet, not a board sheet)
| Header pin | Wires to | Note |
|---|---|---|
| `Vin+` | `PV_PLUS` terminal | high-side: panel + in |
| `Vin−` | `PV_BUCK_IN` (mppt_buck `VPV`, J1.1) | shunt out → buck input |
| `VCC` | `+5V_PWR` | breakout logic supply |
| `GND` | `GND` | power GND |
| `SDA` / `SCL` | `PV_SDA` / `PV_SCL` → J_ARD | I2C to Arduino |

### c2000_feedback — **AFTER rework** (J1/J3/J5 sense in, J2/J4 LaunchPad)
Channel→bus mapping (locked): **V1IN←V1 (÷11), V2IN←LOAD (÷7), V3IN←STORE (÷3)**.
| Board net | Contract net | Dir |
|---|---|---|
| `V1IN` (J1.1) | `V1` | input |
| `V2IN` (J3.1) | `LOAD` | input |
| `V3IN` (J5.1) | `STORE` | input |
| `ADCV1/2/3` (J4) | `ADC_V1` / `ADC_LOAD` / `ADC_STORE` | output → C2000 ADC |
| `+3V3` (J2.1) | `+3V3` | input (from LaunchPad) |
| `GND` (J2.2) | `GND` | power — **power GND** (analog ref for the dividers) |
| ~~I1/I2/I3 channels~~ | **REMOVED** | currents via current_sense→Arduino |
| ~~PWM pass~~ | **REMOVED** | C2000 EPWM → converter optos directly |

## The two MCU connectors (replace the single Arduino hub)

### J_ARD — Arduino Nano (5 V, **socketed on-board**)
Self-contained: V1 telemetry + the whole PV/MPPT loop. No link to the C2000.
| Signal | Source/Dest | Note |
|---|---|---|
| `MCU_V1` | motor_feedback J3 | isolated V1 monitor |
| `PV_SDA` / `PV_SCL` | PV INA219 breakout | I2C, PV V/I for P&O |
| `PWM_MPPT` | → mppt_buck J3.1 | Arduino drives MPPT duty directly (5 V) |
| `+5V_PWR` / `GND` | rail | Arduino + INA219 supply/ref (power GND) |

### J_C2K — TI C2000 LaunchPad (3.3 V, **off-board via header**)
Self-contained: V-sense in, 2 converter PWM out. No link to the Arduino.
| Signal | Dest | Note |
|---|---|---|
| `ADC_V1` / `ADC_LOAD` / `ADC_STORE` | from c2000_feedback J4 | 0–3.3 V analog sense |
| `EPWM_MOTOR` → `PWM_MOTOR` | motor_power | motor-buck duty |
| `EPWM_BOOST` → `PWM_BOOST` | boost_v2_mill | boost duty |
| `+3V3` / `GND` | rail | LaunchPad supply; **GND = power GND** (analog ref) |

> **⚠ Verify before build — C2000 EPWM drive strength (motor + boost only).** Those two optos
> (CNY17, 200 Ω series) need ~10 mA. A C2000 EPWM GPIO at 3.3 V may **not** source that. If the
> LaunchPad pin can't, add a **small NPN buffer per PWM line** (BC547 + base R, opto in
> collector). Confirm against the F28027 GPIO drive spec. (MPPT is Arduino-driven at 5 V →
> ~19 mA, no buffer needed — that's the board's original design.)

## Top-sheet wiring map
- **V1 bus (15 V):** `motor_power.V1` ↔ `motor_feedback.V1` ↔ `c2000_feedback.V1IN`.
- **STORE bus (5 V):** `mppt_buck.VOUT_5V` ↔ `boost_v2.VIN_5V` ↔ `c2000_feedback.V3IN` ↔ 1 F supercap terminal.
- **LOAD bus:** `boost_v2.VOUT_V2` ↔ `c2000_feedback.V2IN` ↔ pulsing-load terminal.
- **+15V_GATE:** `boost_v2.+15V` ↔ `mppt_buck.+15V` ↔ bench-supply terminal. (motor_power has its own +15V1/+15V2.)
- **+5V_PWR:** `motor_power.+5v` ↔ `motor_feedback.+5V` ↔ Arduino 5 V ↔ PV INA219 VCC ↔ +5 V supply terminal.
- **PV path:** `PV_PLUS` terminal → INA219 `Vin+`; INA219 `Vin−` → `PV_BUCK_IN` (mppt_buck). `PV_RET` → `GND`.
- **PWM:** C2000 `EPWM_MOTOR/BOOST` → `PWM_MOTOR` / `PWM_BOOST` (through buffers if needed); **Arduino** → `PWM_MPPT` (5 V, direct).
- **External terminals:** `3PH_U/V/W` (transformer secondary), `MOTOR_A/B` (motor), `PV_PLUS/PV_RET` (panel → INA219), `STORE` (supercap), `LOAD` (pulsing load), `+15V_GATE`, `+5V_PWR`.

### Ground domains
- **Power GND:** motor_power, mppt_buck/boost_v2 power stages, the PV INA219, **and the C2000
  analog ground** (c2000_feedback divider bottoms + LaunchPad GND), plus the Arduino. All
  sensing is power-GND-referenced (c2000_feedback dividers → C2000; PV INA219 → Arduino) so the
  measured values are correct.
- **GND_MCU:** motor_feedback's MCU side + the boost/mppt PWM **opto cathodes**. This is the
  only nominally-separate return. (Per `PCB_RESULTS.md`, the opto/IL300 isolation is nominal —
  grounds are shared as in the team's sim, not galvanically isolated.)
- **Star tie REQUIRED:** GND and GND_MCU **meet at a single star point** (one stitch via /
  short link). The C2000 EPWM (power-GND-referenced) drives the GND_MCU-referenced converter
  optos through this tie. Mark the point explicitly; do not pour the two grounds into each
  other elsewhere.

## Diagnostic probe points (1-pin header test points, labelled rows near the edge)
- **Rails:** `V1`, `STORE`, `LOAD`, `+5V_PWR`, `+3V3`, `+15V_GATE`; **GND** ×2 (one per domain: power GND and GND_MCU).
- **Switch nodes:** motor-buck SW (motor_power internal), `boost_v2` SW, `mppt_buck.SW`.
- **PWM chain** (probe both ends to localise a dead converter): C2000-side `EPWM_*` and post-opto gate at each converter.
- **Feedback:** `ADC_V1/ADC_LOAD/ADC_STORE` (3.3 V), `MCU_V1`, PV INA219 `PV_SDA/PV_SCL`.

## Build plan (which steps are scripted vs done in KiCad by the user)
1. **c2000_feedback rework (scripted — me). DONE.** I1/I2/I3 channels + PWM pass removed,
   V-channel inputs relabelled V1/LOAD/STORE, ERC 0.
2. **Hierarchical labels (KiCad GUI — user).** Per the tables above, place a hierarchical label
   on each interface net of each of the **5 boards**, named exactly. Save each.
   (`system/HIERARCHICAL_LABELS_HOWTO.md` is the procedure.)
3. **Top sheet (scripted — me).** Rebuild `system/system.kicad_sch`: 5 sheet symbols, sheet
   pins from the Phase-2 labels, wired per the map; add `J_ARD` + `J_C2K` + the PV INA219 header
   + external terminals + probe-point test points + PWR_FLAGs on externally-fed rails.
4. **ERC (scripted — me).** Hierarchical ERC 0 errors; V1 ≠ STORE ≠ LOAD; the single GND star tie present.

## Acceptance criteria
- `system.kicad_sch` has exactly the 5 sheets above + the PV INA219 header.
- Every contract net is a sheet pin, wired at top level; the two MCU connectors carry the split.
- `c2000_feedback` has no current channels and no PWM pass (unless the buffer block is added).
- Hierarchical ERC: 0 errors.
- Distinct buses V1 / STORE / LOAD; two ground domains with exactly one star tie.
- Probe points present on every net in the diagnostics list.
