# Motor subsystem: split into two isolated boards

**Date:** 2026-06-21
**Status:** approved (design), pending implementation

## Background

`hardware/kicad/boards/CompleteMotorCircuit/` is Ask-ham's integrated motor-side
schematic: 3-phase rectifier → buck → DC-motor drive, plus a NE555/opto PWM front-end
and an "isolated linear amp" (MCP601 → IL300 → MCP601) that senses the DC bus (V1) for
the Arduino. After footprint assignment it is ERC-clean (0 errors, 65 components, all
THT laser footprints).

It is too much for one 104×104 mm fiber-laser board, and — more importantly — it mixes a
mV-level sense amplifier with two hard-switching power stages. The IL300 feedback amp is
also **not actually isolating**: both op-amps (U9 input, U11 output) share the same `GND`
and `+5v`, so the feedback path bridges the very ground domains the PWM opto-couplers
(4N25/ILD74) are there to separate. The current circuit pays for isolation on the PWM
path in, then shorts it on the feedback path out.

## Hard constraint

**Ask-ham's `CompleteMotorCircuit` project is never modified.** It stays as the intact
integrated reference. Both new boards are new, independent KiCad projects in their own
folders.

## Decision

Split into two boards along the isolation barrier, and make the barrier real:

### Board A — `hardware/kicad/boards/motor_power/` (power + drive domain)
Everything except the feedback amp (~57 components): 3-phase rectifier + 4700 µF bus,
buck stage, motor drive, both IR2110 gate drivers, LM7805, NE555 + pots + PWM optos +
SW1, all supply caps, and **R13** (Q2 gate pulldown — confirmed by netlist, *not* a
feedback resistor).

- **Add one 3-pin output connector** to the feedback board: **{ V1, power GND, power +5V }**
  where V1 is the measured bus node (`Net-(C12-Pin_2)`).

### Board B — `hardware/kicad/boards/motor_feedback/` (isolated linear amp)
8 components: `U9, U10 (IL300), U11, R14, R15, R16, R17, R18`.

- **Power/input side** (U9, IL300 LED + servo photodiode): power `GND` / power `+5V`.
- **MCU/output side** (IL300 output photodiode + U11): re-referenced to **new
  `GND_MCU` / `+5V_MCU`** rails. Concretely, move `U10.6`, `U11.4`, `U11.7`, `R18.2`
  off the shared `+5v`/`GND` onto the Arduino-side rails. *This re-reference is what
  makes the IL300 actually isolate.*
- **Connector P1** (power side, 3-pin): { V1, GND, +5V } — mates with Board A.
- **Connector P2** (MCU side, 3-pin): { ADC_out (→ Arduino analog in), GND_MCU, +5V_MCU }.

### Inter-board wiring
`motor_power` → `motor_feedback` P1: V1, power GND, power +5V.
`motor_feedback` P2 → Arduino: ADC signal, Arduino GND, Arduino +5V.

## Component partition (authoritative)

| Board | Components |
|---|---|
| `motor_feedback` | U9, U10, U11, R14, R15, R16, R17, R18 |
| `motor_power` | all other 57 (rectifier D5–D12 + C11, buck, motor drive, both IR2110, LM7805, NE555 U2, optos U3/U7, pots, SW1, R13, caps, terminals J1–J6/L1/C12) |

Boundary signals: **V1** (`Net-(C12-Pin_2)`) is the only signal crossing; the rest of
the interface is the power-side rails (GND, +5V) and the MCU-side rails (GND_MCU,
+5V_MCU, MCU/ADC).

## Build method

**Derive by copying**, not regenerate from scratch. Copy `CompleteMotorCircuit` into the
two new project folders, then trim each to its half and add the connectors + the
feedback-side isolation re-reference. This preserves the exact ERC-clean nets and
already-assigned laser footprints, rather than re-authoring 57 components in a script and
risking divergence. Original project untouched either way.

## Acceptance criteria

- `CompleteMotorCircuit` unchanged (git shows no diff to it).
- `motor_power` and `motor_feedback` are new projects, each **ERC 0 errors**.
- Every component retains a THT laser footprint (no NONE/SMD).
- `motor_feedback` has two ground nets (`GND` power-side, `GND_MCU` MCU-side) that meet
  only across the IL300 barrier — verified in the netlist.
- Inter-board connectors present and labelled on both boards.

## Out of scope (separate follow-up)

Redoing the system hierarchical schematic (`hardware/kicad/system/system.kicad_sch`) to
point its sheets at the new `motor_power` / `motor_feedback` boards instead of the stale
`rectifier`/`buck`/`drive_circuit`/`feedback_circuit` sheets. Done as its own step after
both boards are ERC-clean.
