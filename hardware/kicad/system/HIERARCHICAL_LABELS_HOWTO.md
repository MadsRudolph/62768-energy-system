# How to build the connected system hierarchical schematic

This is the hands-on procedure for wiring the five real boards into one
netlist-connected `system.kicad_sch`. It pairs with the design contract in
[`docs/superpowers/specs/2026-06-21-system-hierarchical-schematic-design.md`](../../../docs/superpowers/specs/2026-06-21-system-hierarchical-schematic-design.md)
— that file says *what* connects to what; this file says *exactly how to do it in KiCad*.

**Your job is Phase 1 only** (placing hierarchical labels on each board, by hand in the
GUI). Phases 2–3 (building the top sheet + ERC) are scripted — ping me when Phase 1 is
done and I'll generate the top sheet from the labels you placed.

---

## The big picture

```mermaid
flowchart TB
    subgraph TOP["system.kicad_sch (top sheet — I build this in Phase 2)"]
        MP[Motor Power]
        MF[Motor Feedback]
        MPPT[MPPT + PV]
        BO[Boost v2]
        CS[Current Sense]
        ARD([Arduino hub connector])
    end
    MP <-->|V1 bus| MF
    MPPT <-->|STORE bus| BO
    MP -. PWM_MOTOR .-> ARD
    BO -. PWM_BOOST .-> ARD
    MF -. MCU_V1 .-> ARD
    MPPT -. PV_V / PV_I .-> ARD
    CS -. I_SENSE1..3 .-> ARD
```

Each board becomes a **sheet** in the top schematic. A net you want to expose to the
top sheet gets a **hierarchical label** inside the board; that label automatically
becomes a **sheet pin** on the board's box in the top sheet, which I then wire up.

---

## Background: hierarchical label vs sheet pin (30-second version)

- A **hierarchical label** lives *inside* a sub-sheet (a board). Its **name** is the
  contract — `STORE`, `V1`, `GND`, etc.
- When that board is dropped into the top sheet, KiCad imports each hierarchical label
  as a **sheet pin** on the board's rectangle.
- I wire the sheet pins together at the top level (e.g. `mppt:STORE` ↔ `boost:STORE`).
- **The names must match exactly**, including case. `+5V` ≠ `+5v`. This already bit us
  once (the IL300 `+5V` island), so copy the names from the tables below verbatim.

You do **not** rename any existing nets. A net can carry both its current label *and* a
new hierarchical label — they merge into the same net. The hierarchical label is just
the "export this net to the top sheet" tag.

---

## Before you start

1. **Use KiCad 10.** Open each board through its **`.kicad_pro`** (not the bare
   `.kicad_sch`) so the project rules load.
2. **One board at a time.** Finish a board, save, run ERC, close it.
3. **motor_power / motor_feedback are safe to open now** — their PCBs are routed and
   committed. Opening the schematic to add labels won't disturb the board.
4. The three older boards (**mppt, boost_v2, current_sense**) are KiCad-9 files. KiCad 10
   will offer to **upgrade the format on save — say yes.** The big reformatting diff that
   produces is expected, not corruption.

---

## The mechanic: placing one hierarchical label

Do this once and the rest is repetition:

1. In the schematic editor, **Place ▸ Add Hierarchical Label** (hotkey **`H`** — confirm
   the shortcut shown in the Place menu on your install).
2. Type the **exact label name** from the board's table below.
3. Set **Shape** to the value in the table (Input / Output / Bidirectional / Passive).
   This only sets the sheet-pin arrow direction — it does not affect connectivity, but
   set it right so the top sheet reads correctly. Use **Passive** for `GND`/power nets.
4. Click to drop the label **directly on the target net's wire** so its anchor (the little
   connection square) touches the wire. If it's not on the wire, it won't connect.
   - **Finding the right wire:** most interface nets already show a label (e.g. boost_v2
     literally has `VIN_5V`, `GND`, `PWM` printed on the wire). Drop the hierarchical
     label on that same wire. If a net has no visible label, hover the wire — KiCad shows
     the net name (e.g. `Net-(J4-Pin_1)`) in the status bar / at the cursor.
   - If the connector pin has no wire stub to land on, draw a short wire off the pin first
     (hotkey **`W`**), then attach the label to that stub.
5. **Save** (`Ctrl+S`).

> Tip: place the label so its text points *away* from the components, toward where the
> board edge / sheet pin will be. Cosmetic only, but it keeps the top sheet tidy.

---

## Per-board label tables

Place exactly these labels on each board. "Where" tells you which connector pin / existing
net to land on. Names are **case-sensitive** — type them as written.

### 1. motor_power  (`boards/motor_power/motor_power.kicad_sch`) — 10 labels
Interface nets are mostly auto-named (`Net-(Jx-Pin_n)`), so anchor by **connector pin**.

| Where (connector · existing net) | Label name | Shape |
|---|---|---|
| J1 pin 1 · "PWM fra MCU" (`Net-(J1-Pin_1)`) | `PWM_MOTOR` | Input |
| J2 pin 1 · "MCP PWM" (`Net-(J2-Pin_1)`) | `PWM_MOTOR_ALT` | Input |
| J3 motor + · `+15V1` | `MOTOR_A` | Output |
| J3 motor − · `Net-(D4-A)` | `MOTOR_B` | Output |
| J4 / J5 three phase nodes (3 wires) | `3PH_U` / `3PH_V` / `3PH_W` | Bidirectional |
| `V1` net (J6 pin 2 / J7 pin 1) | `V1` | Output |
| `GND` | `GND` | Passive |
| `+5v` (J7 pin 3) | `+5V_PWR` | Input |

### 2. motor_feedback  (`boards/motor_feedback/motor_feedback.kicad_sch`) — 6 labels
Two isolated domains: **power side** (J1) vs **MCU side** (J3). Keep them distinct.

| Where (connector pin · net) | Label name | Shape |
|---|---|---|
| J1 pin 1 · `V1` | `V1` | Input |
| J1 pin 2 · `GND` | `GND` | Passive |
| J1 pin 3 · `+5V` | `+5V_PWR` | Input |
| J3 pin 1 · `MCU` | `MCU_V1` | Output |
| J3 pin 2 · `GND_MCU` | `GND_MCU` | Passive |
| J3 pin 3 · `+5V_MCU` | `+5V_MCU` | Input |

### 3. mppt  (`boards/mppt/mppt.kicad_sch`) — 6 labels
These nets already have labels — land on them.

| Where (existing label) | Label name | Shape |
|---|---|---|
| `PV_PLUS` (J1) | `PV_PLUS` | Input |
| `PV_RET` (J1) | `PV_RET` | Input |
| `V3_OUT` (J2 pin 1) | `STORE` | Output |
| `PV_V` (J3) | `PV_V` | Output |
| `PV_I` (J3) | `PV_I` | Output |
| `GND` | `GND` | Passive |

### 4. boost_v2  (`boards/boost/boost_v2/boost_v2.kicad_sch`) — 6 labels
**Use boost_v2** (the routed/measured board), not the old plain `boost/`. The nets are
already **global labels** — drop the hierarchical label on the same wire.

| Where (existing global label) | Label name | Shape |
|---|---|---|
| `VIN_5V` (J1 pin 1) | `STORE` | Input |
| `VOUT_V2` (J2 pin 1) | `LOAD` | Output |
| `PWM` (J3 pin 1) | `PWM_BOOST` | Input |
| `GND_MCU` (J3 pin 2) | `GND_MCU` | Passive |
| `+15V` (J4 pin 1) | `+15V_GATE` | Input |
| `GND` | `GND` | Passive |

### 5. current_sense  (`boards/current_sense/current_sense.kicad_sch`) — 8 labels

| Where (existing label) | Label name | Shape |
|---|---|---|
| `RET1` / `RET2` / `RET3` (J1 / J2 / J3) | `RET1` / `RET2` / `RET3` | Input |
| `I_SENSE1` / `I_SENSE2` / `I_SENSE3` (J4) | `I_SENSE1` / `I_SENSE2` / `I_SENSE3` | Output |
| `+5V` (J4 pin 1) | `+5V_PWR` | Input |
| `GND` | `GND` | Passive |

**Total: 36 labels across 5 boards.**

---

## Verify each board before moving on

After labelling a board:

1. **Eyeball:** every label in the table is present and sitting on a wire (green
   connection dot, not a floating square).
2. **ERC:** *Inspect ▸ Electrical Rules Checker ▸ Run ERC*. It should stay at **0 errors**.
   Benign and ignorable: `lib_symbol_mismatch`, and single-pin "not connected" notices.
   A **new** "label not connected to anything" error means the label missed the wire —
   nudge it onto the wire and re-run.
3. **Save** (and accept the KiCad-10 format upgrade for mppt / boost_v2 / current_sense).

---

## Gotchas (these are the ones that actually cost time)

- **Case sensitivity.** `+5V` and `+5v` are different nets. Type names exactly as in the
  tables. (motor_power uses lowercase `+5v`; motor_feedback/current_sense use `+5V` —
  that's fine, they connect at the top sheet through the contract, not by raw name.)
- **The anchor must touch the wire.** A label 0.5 mm off the wire is electrically a
  floating label. Zoom in; look for the connection dot.
- **Don't rename existing nets.** Add the hierarchical label alongside; both names refer
  to the same net.
- **Two ground domains.** `GND` (power) and `GND_MCU` (Arduino side of the feedback amp +
  the boost PWM opto) are intentionally separate. Label them separately and **don't tie
  them together on any board** — I join them (or not) at a single star point in the top
  sheet per the contract.
- **Global labels already on boost_v2.** Leaving the existing globals in place is fine;
  the hierarchical label is what creates the sheet pin. If ERC later flags global-label
  bleed between sheets, that's a Phase-3 cleanup I'll handle — don't worry about it now.

---

## What happens after Phase 1 (so you know where this is going)

**Phase 2 — top sheet (I script this).** I rebuild `system.kicad_sch` with five sheet
symbols pointing at the board files, import the sheet pins from the labels you placed,
and wire them per the contract: the **V1 bus** (motor_power ↔ motor_feedback), the
**STORE bus** (mppt ↔ boost_v2), an **Arduino hub** connector collecting all the MCU
signals (`PWM_MOTOR`, `PWM_BOOST`, `MCU_V1`, `PV_V`, `PV_I`, `I_SENSE1..3`, …), and
external terminals (`PV_PLUS/PV_RET`, `MOTOR_A/MOTOR_B`, `3PH_U/V/W`, `LOAD`,
`+15V_GATE`). I add `PWR_FLAG`s on externally-fed rails so ERC is happy.

**Phase 3 — verify.** Hierarchical ERC to **0 errors**; confirm `V1` ≠ `STORE` (two
independent buses) and `GND` ≠ `GND_MCU` (two domains), and that every sheet pin is wired.

**When you finish a board (or all five), tell me** and I'll read the labels straight out
of the `.kicad_sch` to confirm they landed, then run Phase 2.

---

## Quick checklist

- [ ] motor_power — 10 labels, ERC 0, saved
- [ ] motor_feedback — 6 labels, ERC 0, saved
- [ ] mppt — 6 labels, ERC 0, saved (format upgraded)
- [ ] boost_v2 — 6 labels, ERC 0, saved (format upgraded)
- [ ] current_sense — 8 labels, ERC 0, saved (format upgraded)
- [ ] ping me → Phase 2 (top sheet) → Phase 3 (ERC 0)
