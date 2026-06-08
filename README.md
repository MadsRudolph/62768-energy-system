# 62768 — Electrical Energy System

Team project for **62768 Electrical Energy Systems** (DTU, June 2026, 3-week course).
We design and build a complete electrical energy system per the course requirement spec
(*Kravspecifikation*), from idea to a working functional model (CDIO).

> 📋 **Start here:** [`docs/project-overview.md`](docs/project-overview.md) — what to build,
> targets, subsystem plan, deadlines, and division of labour (synthesised from the course material).
> 🗂️ **Kickoff:** [`docs/project-plan.md`](docs/project-plan.md) — the 9-section project plan
> (Lecture 1 structure) to fill in on day 1: tasks/owners, budget, Gantt.

## Team

| Name | GitHub | Role / area |
|------|--------|-------------|
| Mads Rudolph | @MadsRudolph | |
| Jonas Beck Jensen | | |
| Andreas Skånning | | |
| Bjørn Bjarnason | | |
| Nikolas Jacobsen | @nikolas-jacobsen | |
| _teammate 6_ | | |

## System overview

```mermaid
flowchart LR
    SOL[Solar panel] --> MPPT["MPPT cap (15 mF)"]
    MPPT --> LIN["Linear reg (5V)"]
    LIN --> STORE(("Energy store<br/>1F · V3=5V"))

    MOT[DC-Motor] --> GEN["AC-generator<br/>(3-phase)"]
    GEN --> TR["3× transformer"]
    TR --> REC["Rectifier + cap (15 mF)"]
    REC --> BUCK["Buck (Vout=4.8V)"]
    BUCK -->|V1=15V| STORE

    STORE --> BOOST[Boost]
    BOOST -->|V2=10V| LOAD["Pulsing load 10V"]

    PID["PID (Arduino)"] --> PWM[PWM driver]
    PWM --> MOT
    STORE -.monitor.-> DAQ["PC monitoring"]
```

**Key targets:** V1 = 15 V ±1 V (≥300 mA to buck) · V2 = 10 V ±1 V (≥150 mA) · V3 = 5 V ±0.5 V.
Converters and current sensing must use **discrete components** (op-amps allowed; no integrated converter ICs).
Full requirement list lives in the course spec (see `docs/`).

## Repository layout

| Folder | Contents |
|--------|----------|
| `firmware/` | Arduino code — PID control, ADC, timer/PWM, monitoring |
| `simulation/` | Simulink models (`.slx`) + parameter scripts (`.m`) |
| `hardware/schematics/` | Circuit schematics |
| `hardware/bom/` | Bill of materials |
| `report/` | LaTeX project report — compile `report/main.tex` (`latexmk -pdf main.tex`) |
| `docs/` | Spec, lab guides, design notes; `docs/datasheets/` for component PDFs |
| `measurements/` | Lab/test data (csv, xlsx) |

## Getting started

- **Firmware:** Arduino IDE (or PlatformIO). Boards used: Arduino + (optionally) TI LAUNCHXL-F28027.
- **Simulation:** MATLAB/Simulink — open `.slx` models in `simulation/`, run the `Parameters*.m` scripts first to load workspace variables.
- **Report:** LaTeX in `report/`. Compile with `latexmk -pdf main.tex` (or `pdflatex main` twice). Each `sections/*.tex` can also be compiled standalone. Fill in the frontpage group members and the kravsporing table.

## Workflow (6-person team)

- **Branch per feature/task:** `git checkout -b firmware/pid-loop` (or `sim/...`, `hw/...`, `docs/...`).
- **Pull request into `main`** — keep `main` always working. Ask one teammate to review before merge.
- **Commit small and often**, with clear messages. Pull before you push.
- **Avoid committing binaries that change every save** — `.gitignore` already excludes MATLAB/Arduino build artifacts.
- Heavy binary files (videos, big captures): link from a shared drive instead of committing.

## Course

- DTU 62768, June 2026 · groups of up to 6 · assessment = report + functional model.
- Lab: V1.01-04 · Lecturers: Ashraf, Sam, Audrey.
