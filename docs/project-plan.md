# Project Plan — 62768 Electrical Energy Systems

Structure per Lecture 1. Pre-filled from the spec + [`project-overview.md`](project-overview.md);
**[TBD]** / **[assign]** markers are for the group to complete at the kickoff.

## 1. Identification
| | |
|---|---|
| Course | 62768 Electrical Energy Systems (project), June 2026 |
| Project title | Elektrisk Energisystem |
| Project-ID | [TBD] |
| Group no. | [TBD] |
| Project leader | Bjørn Bjarnason |
| Members | Mads Rudolph (s246132), Jonas Beck Jensen (s240324), Andreas Skånning (s241123), Bjørn Bjarnason (s233928), Nikolas Skånning (s245428), [member 6] |
| Date | [TBD] |

## 2. Introduction to the problem
Design and build a complete **electrical energy system** with two sources — a
motor-driven 3-phase generator and a solar (PV) branch — feeding a shared energy
store and a pulsing load, per the course *Kravspecifikation*. The system must regulate
several voltage rails within tight tolerances and use self-built, discrete-component
power converters. _[expand]_

## 3. Problem formulation
Key questions and how we intend to answer them:
- **V1 regulation:** how do we hold the rectifier bus at 15 V ±1 V through a 100→300 mA
  load step in <1 s? → Arduino PID on the motor PWM (model in Simulink, Lec 2).
- **Converters:** how do we design discrete buck/boost converters meeting the ripple and
  load-step specs? → Lec 5 design equations + QSPICE simulation, then build.
- **PV/MPPT:** how do we extract max PV power and prioritise PV over the generator? →
  Perturb & Observe MPPT (Lec 2) + source-prioritisation logic.
- **Measurement & monitoring:** discrete current sensing (op-amps only) + PC monitoring
  at 1 s. → Exp 3A feedback circuit + Arduino/NI USB-6008.
_[refine the questions]_

## 4. Tasks (with owners)
| # | Task | Owner(s) | Notes |
|---|------|----------|-------|
| 1 | Generator stage: motor drive, 3φ generator, transformer, rectifier+filter → V1 | [assign] | Lec 1/2/3/4 |
| 2 | Buck converter (discrete) | [assign] | Lec 5 |
| 3 | Boost converter (discrete) | [assign] | Lec 5 |
| 4 | PV + MPPT + linear/buck reg → V3 | [assign] | Lec 2 |
| 5 | Gate drive + discrete current sensing | [assign] | Exp 3A |
| 6 | Arduino firmware: motor PID, MPPT, monitoring | [assign] | bare-metal C / Simulink codegen |
| 7 | Simulink modeling + code generation | [assign] | day 9 topic |
| 8 | PCB design (KiCad) | [assign] | hardware/kicad |
| 9 | System integration + tests (incl. 100 W LED) | [assign] | |
| 10 | Report + poster | all | due 26 June |

## 5. Outcomes
- **Theoretical:** transfer-function model of motor+generator; converter design from first
  principles; control design (PID, MPPT); rectifier/transformer analysis.
- **Technical:** a working functional model hitting all Priority-1 requirements, validated
  by measurement. _[expand]_

## 6. Methodology
CDIO. Flow: **model** (MATLAB/Simulink) → **circuit-simulate** (QSPICE) → **design PCB**
(KiCad) → **build + firmware** (Arduino) → **integrate + test** → **document**
(report + poster). Work tracked via GitHub issues/board.

## 7. Resources (components + budget)
| Component | Qty | Source | Est. cost |
|---|---|---|---|
| DC motor (Motraxx SR555) + Hacker A20-L22 generator | 1 | EIS kit MCA-143 | — |
| 3× ring-core transformer (1:8) | 1 set | EIS kit | — |
| PV panel (Phaesun Sun Plus 10) + halogen "sun" | 1 | EIS kit | — |
| MOSFET IRF540N, gate driver IR2110 | [qty] | [src] | [TBD] |
| Opto ILD74 / IL300, op-amp MCP601, diode 1N4007 | [qty] | [src] | [TBD] |
| Inductors / capacitors (per L/C sizing) | [qty] | [src] | [TBD] |
| Arduino (×~4) + NI USB-6008 DAQ | 4 + 1 | EIS / dept | — |
| 1 F super-capacitor (energy store) | 1 | EIS kit | — |
| _[add as identified]_ | | | |

Equipment via **EIS (eis.dtu.dk), kit MCA-143** — contact Dan Burer.

## 8. Activities plan
**Authoritative schedule — [Gantt (Google Sheets)](https://docs.google.com/spreadsheets/d/19ZzGKzBEv2S9PaVvXlEKpNqkHAYsdZk_XWM64Xs1Ixg/edit?gid=1115838130)**,
maintained by Bjørn (project leader). WBS across 3 phases, which map to the 3 course weeks
(≈ 8–12 / 15–19 / 22–26 June — confirm the exact phase→date mapping in the sheet).

| WBS | Task | Phase |
|---|---|---|
| 1.2 | Undersøgelser | 1 |
| 1.3 | Planlægning | 1 |
| 2.1 | Buck converter | 1–2 |
| 2.2 | Buck converter 2 | 1–2 |
| 2.3 | Rectifier | 1–2 |
| 2.4 | Boost converter | 2 |
| 3.1 | Opto coupler | 2–3 |
| 3.1 | PWM driver | 2–3 |
| 4.1 | PID 1 | 3 |
| 4.2 | PID 2 | 3 |
| 4.3 | MPPT | 3 |
| 4.4 | UI / monitoring | 3 |

> The Google Sheet is the **source of truth** for the schedule — keep owners, dates, and
> % completion there; this table is just an offline snapshot.

## 9. References
- Kravspecifikation (`Project Specifications.pdf`)
- Lectures 1–5 + Exp 3A + Three-Phase Transformer (course slides)
- Component datasheets (`datasheets/`)
- [`project-overview.md`](project-overview.md)

## Green Challenge (optional)
_[decide whether to enter; note any sustainability angle of the energy system]_
