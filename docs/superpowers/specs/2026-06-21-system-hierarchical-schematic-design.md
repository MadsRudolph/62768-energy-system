# System hierarchical schematic — redo (connected hierarchy)

**Date:** 2026-06-21
**Status:** approved (design), pending build
**Predecessor:** the motor board split (see `2026-06-21-motor-board-split-design.md`) — DONE; `motor_power` + `motor_feedback` are built, ERC 0.

## Goal
Rebuild `hardware/kicad/system/system.kicad_sch` as a **fully netlist-connected**
hierarchical schematic that matches the **real** board set, replacing the stale 7-sheet
version that points at the old per-block boards.

## Decisions (locked)
1. **Board set:** `motor_power` + `motor_feedback` **replace** the four old motor-side
   sheets (`drive_circuit`, `rectifier`, `buck`, `feedback_circuit`).
2. **V1/Store topology = "as-built (a)":** the 5 V **store is MPPT-fed only**.
   `motor_power`'s internal buck regulates **V1** (15 V) for the motor/load chain.
   So **V1** and **Store** are two independent buses (no buck→store link).
3. **Fidelity:** fully connected hierarchy (ERC-clean across sheets), not just a block
   diagram.

## Target structure — 5 sheets (was 7)
| Sheet name | Sub-sheet file |
|---|---|
| Motor Power | `../boards/motor_power/motor_power.kicad_sch` |
| Motor Feedback | `../boards/motor_feedback/motor_feedback.kicad_sch` |
| MPPT + PV | `../boards/mppt/mppt.kicad_sch` |
| Boost | `../boards/boost/boost.kicad_sch` |
| Current Sense | `../boards/current_sense/current_sense.kicad_sch` |

## Interface contract — hierarchical labels per board
Each label below is a **hierarchical label** placed on the named net (near its connector).
It becomes a **sheet pin** in the top sheet. Names are the contract — keep them exact.

### motor_power (connectors J1/J2/J3/J4/J5/J6/J7)
| Net / connector | Hierarchical label | Dir |
|---|---|---|
| J1.1 (`Net-(J1-Pin_1)`, "PWM fra MCU") | `PWM_MOTOR` | input |
| J2.1 (`Net-(J2-Pin_1)`, "MCP PWM") | `PWM_MOTOR_ALT` | input |
| J3 (motor, `+15V1`/`Net-(D4-A)`) | `MOTOR_A` / `MOTOR_B` | output |
| J4/J5 (3-phase, 3 nets) | `3PH_U` / `3PH_V` / `3PH_W` | bidir |
| `V1` net (J6.2 / J7.1) | `V1` | output |
| `GND` | `GND` | power |
| `+5v` (J7.3) | `+5V_PWR` | input |

### motor_feedback (connectors J1=power side, J3=MCU side)
| Net | Hierarchical label | Dir |
|---|---|---|
| `V1` (J1.1) | `V1` | input |
| `GND` (J1.2) | `GND` | power |
| `+5V` (J1.3) | `+5V_PWR` | input |
| `MCU` (J3.1) | `MCU_V1` | output |
| `GND_MCU` (J3.2) | `GND_MCU` | power |
| `+5V_MCU` (J3.3) | `+5V_MCU` | input |

### mppt (J1=PV, J2=store, J3=sense)
| Net | Hierarchical label | Dir |
|---|---|---|
| `PV_PLUS`/`PV_RET` (J1) | `PV_PLUS` / `PV_RET` | input |
| `V3_OUT` (J2.1) | `STORE` | output |
| `PV_V`/`PV_I` (J3) | `PV_V` / `PV_I` | output |
| `GND` | `GND` | power |

### boost (J1=store in, J2=load, J3=PWM, J4=gate supply)
| Net | Hierarchical label | Dir |
|---|---|---|
| `VIN_5V` (J1.1) | `STORE` | input |
| `VOUT_V2` (J2.1) | `LOAD` | output |
| `PWM` (J3.1) | `PWM_BOOST` | input |
| `GND_MCU` (J3.2) | `GND_MCU` | power |
| `+12V` (J4.1) | `+12V_GATE` | input |
| `GND` | `GND` | power |

### current_sense (J1/J2/J3=channel returns, J4=Arduino)
| Net | Hierarchical label | Dir |
|---|---|---|
| `RET1`/`RET2`/`RET3` (J1/J2/J3) | `RET1` / `RET2` / `RET3` | input |
| `I_SENSE1/2/3` (J4) | `I_SENSE1` / `I_SENSE2` / `I_SENSE3` | output |
| `+5V` (J4.1) | `+5V_PWR` | input |
| `GND` | `GND` | power |

## Top-sheet wiring map
- **V1 bus:** `motor_power.V1` ↔ `motor_feedback.V1`. Power tap: `motor_power.GND`↔`motor_feedback.GND`, `motor_power.+5V_PWR`↔`motor_feedback.+5V_PWR`.
- **Store bus:** `mppt.STORE` ↔ `boost.STORE`. (`GND` common.)
- **Arduino hub** (one multi-pin connector symbol at top level, e.g. `J_ARD`): collects
  `PWM_MOTOR`, `PWM_BOOST`, `MCU_V1`, `PV_V`, `PV_I`, `I_SENSE1/2/3`, `GND_MCU`, `+5V_MCU`, `+5V_PWR`.
- **External terminals** at top level: `PV_PLUS`/`PV_RET` (panel), `MOTOR_A`/`MOTOR_B`,
  `3PH_U/V/W` (generator), `LOAD`.
- **Two ground domains:** power `GND` (motor_power/mppt/boost/current_sense) and Arduino
  `GND_MCU` (motor_feedback MCU side + boost PWM opto). Keep them distinct at top level;
  tie at a single star point only if the real build does.

## Build plan
**Phase 1 — hierarchical labels (KiCad GUI, per board).** Using the tables above, place a
hierarchical label on each interface net of each board, named exactly. Save each board.
Reliable in the GUI; brittle to script (geometry on exact net points), so done by hand.
Verify per board: the hierarchical labels appear, ERC still 0.

**Phase 2 — top sheet (scripted/generated).** Rebuild `system.kicad_sch`: 5 sheet symbols
pointing at the board files, with sheet pins imported from the Phase-1 hierarchical
labels, wired per the top-sheet map; add the Arduino hub connector + external terminals +
PWR_FLAGs on externally-fed rails. Generatable cleanly (no per-board geometry needed).

**Phase 3 — verify.** ERC the top sheet (hierarchical): 0 errors. Confirm V1 and Store are
two separate buses, the two ground domains are distinct, and every sheet pin is wired.

## Acceptance criteria
- `system.kicad_sch` has exactly the 5 sheets above, pointing at the real boards.
- Every interface net in the contract is a sheet pin, wired at top level.
- Hierarchical ERC: 0 errors.
- V1 ≠ Store (separate buses); `GND` ≠ `GND_MCU` (two domains).
- The four old motor-side sheets are gone from the top sheet.

## Current state / resume pointer
Board split done + committed; PR #30 (srm-cam submodule) merged. Next action on resume:
**Phase 1** — place the hierarchical labels per the tables (user, in KiCad), board by
board, then ping for Phase-2 top-sheet generation.
