# 62768 Electrical Energy Systems — Project Overview

Synthesis of the course material (7 lecture decks, Exp 3A, Three-Phase Transformer
lab, the Kravspecifikation, and the intro slides). Shared reference for the team.

## What this project is
A 6-person **CDIO** project: build a **two-source electrical energy system**.
- **Deliverables:** group **report** + **poster** → upload to **DTU Learn by 26 June**.
  Plus **peer review** of the report and a **poster presentation**.
- **Grading:** **Pass / Fail**, on the overall impression of the report.
- **Timeline:** 8 June intro + project box; 9 June Simulink code-gen + converter design
  + MPPT (Sam); work through 3 weeks; 26 June hand-in.
- **Kit (from EIS, MCA-143):** Motraxx SR555 DC-motor, Hacker A20-L22 3-phase PMSM
  generator (14 poles, 924 rev/V), 3× ring-core transformers (1:8, Y/Δ choosable,
  ~20–400 Hz), Phaesun Sun Plus 10 PV panel (10 W), 4×400 W halogen "sun", 1 F
  super-cap, Arduino, NI USB-6008 DAQ.

## The system + authoritative targets (from the spec table)
Two branches feed a shared **1 F** super-capacitor store → boost → pulsing load.

| Node | Requirement | Priority |
|---|---|---|
| **V1** (rectifier bus) | 15 V ±1 V at 100 mA buck draw; generator delivers 300 mA; hold through a 100→300 mA step in ≤1.0 s | 1 |
| **V2** (load) | within ±1.0 V; deliver ≥150 mA; hold through a 50→150 mA step in ≤1.0 s | 1 |
| **V3** (energy store) | 5 V ±0.5 V for currents > 20 mA | 1 |
| Converters | self-built **buck & boost**, **discrete components** (no converter ICs) | 1 |
| Current sensing | discrete components, **op-amps allowed**, no other ICs | 1 |
| Source priority | **PV consumed first**, generator is the supplementary source | 1 |
| System test | drive a **100 W LED light at 0.5 m** from the PV branch | 1 |
| Monitoring + Arduino ADC/timer/PWM | PC monitoring, 1.0 s update | 2 (optional) |

> Priority 1 = must design + implement. Priority 2 = optional.

## Subsystems + which lecture drives each
| Subsystem | What to do | Theory source |
|---|---|---|
| **Generator stage** | PWM-drive DC motor → 3-phase PMSM generator → 3× transformer (**1:8, Y-Δ** — avoids 3rd-harmonic issues), 20–400 Hz → **6-diode rectifier + 15 mF** → V1 = 15 V | Lec 1 (PMDC 2-state model), Lec 2 (motor+gen transfer functions), Lec 3 (PMSM), Lec 4 (3φ rectifier: V_dc = 1.654·V_m, diode rating, L/C filter) |
| **Buck converter** (discrete) | feed V2; `k=V_a/V_s`, `ΔI=V_s·k(1−k)/(fL)`, `ΔV_c=V_s·k(1−k)/(8LCf²)`, `L_c=(1−k)R/2f`, `C_c=(1−k)/16Lf²` | Lec 5 |
| **Boost converter** (discrete) | store → pulsing load; `V_a=V_s/(1−k)`, `L_c=k(1−k)R/2f`, `C_c=k/2fR` | Lec 5 |
| **PV + MPPT** | Sun Plus 10 under 4×400 W halogen → **discrete MPPT (Perturb & Observe)** → linear-reg/buck → 1 F store at V3 = 5 V | Lec 2 (P&O flowchart) |
| **Gate drive + current sense** | the **Exp 3A** circuit: ILD74 opto → IR2110 → IRF540N + 1N4007 freewheel; isolated feedback via IL300 + MCP601 op-amps | Exp 3A lab |
| **Arduino control** | motor PID + MPPT + monitoring (see below) | Lec 2 (digital PID in C) |

## The Arduino's role (important)
- The Arduino's **PID regulates V1 by driving the motor's PWM** (closed loop on the
  generator output) — **not** the converters. The buck/boost are **discrete/analog**.
- So the Arduino does: **motor PID + MPPT + (optional) PC monitoring**.
- Lec 2 shows **proportional-only control fails** (≈3 V steady-state error, or ringing if
  gain is pushed) → **full PID required**.
- **For the PID C-code:** build the controller model from **Lec 2's motor+generator
  transfer functions** (this is the loop the Arduino runs). `dcdc120_cl.slx` is the
  *converter* model — a separate thing, not the Arduino's deployed controller.

## How the repo maps to this
| Repo | Role |
|---|---|
| `firmware/` | Motor PID + ADC + monitoring (bare-metal C skeletons — team writes) |
| `simulation/` | Converter models + `load_parameters.m`; **still need a motor+generator model from Lec 2** for the PID |
| `hardware/kicad/` | The discrete buck/boost/MPPT/current-sense/gate-drive board |
| `report/` + Figma poster | The two graded deliverables (due 26 June) |
| `docs/datasheets/` | Exactly the Exp 3A parts (IR2110, IRF540, MCP601, IL300, ILD74) |

## Suggested division of labour (group of 6)
The intro slides suggest: mechanical (2), electronics (2), code (2). A workable split:
- **Generator/mechanical:** motor mount, generator, transformer wiring, rectifier + filter → V1.
- **Power electronics:** discrete buck + boost + MPPT + current-sense + gate-drive → PCB (KiCad).
- **Firmware + control:** motor PID, MPPT, monitoring + the Simulink modeling/code-gen.
- **Report + poster:** continuous, everyone contributes; owners coordinate.

Track tasks via the GitHub issues/board.

## Confirm with the supervisor
- **V2 nominal value** — diagram shows buck "4.8 V" and load "10 V", but the spec table
  only says "within ±1 V" without the nominal. Pin this down.
- **Energy store**: 1 F super-cap vs the 6 V / 2.8 Ah gel battery (spec leaves it open).
- Requirement 10's priority field is blank in the spec.
