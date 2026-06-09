# LTspice converter models — buck & boost

First-pass open-loop models of the two self-built DC/DC converters (Krav 8/9),
generated with **SpicePilot / PySpice** and verified in **LTspice** batch mode.

| File | What it is |
|---|---|
| `buck_converter.py` / `boost_converter.py` | SpicePilot/PySpice generators — edit values here, re-run to regenerate |
| `buck.net` / `boost.net` | The LTspice-ready SPICE netlists (open these directly in LTspice) |
| `*.raw`, `*.log` | LTspice simulation output (gitignored) |

## How to use

**Just simulate (no Python needed):** open `buck.net` or `boost.net` in LTspice
(`File > Open`), then `Run`. Probe `V(out)`, `V(sw)`, `I(L1)`.

**Regenerate after changing a value:** edit the design block at the top of the
`.py`, then:
```
py -3.13 buck_converter.py        # rewrites buck.net
```
(Needs PySpice: `py -3.13 -m pip install pyspice`. ngspice is NOT required — we
only generate the netlist; LTspice does the simulating.)

**Batch-verify from the command line** (writes measurements into the `.log`):
```
"C:\Users\<you>\AppData\Local\Programs\ADI\LTspice\LTspice.exe" -b -ascii buck.net
```
then read the `.meas` results from `buck.log`.

## Design

Targets from the project diagram (Lec 1) and the Kravspecifikation. Formulas from
the [Lec 2 (Erickson)](../../../../Obsidian) / Lec 5 (Rashid) converter notes.

| | Buck | Boost |
|---|---|---|
| In → Out | 15 V (V1 bus) → 5 V (charges V3 store) | 5 V (V3 store) → 15 V (V2 load) |
| Duty `D` | `Vout/Vin` = 0.333 | `1 − Vin/Vout` = 0.667 |
| `f_sw` | 50 kHz | 50 kHz |
| `L` | 470 µH | 470 µH |
| `C` | 47 µF | 47 µF |
| `R_load` | 10 Ω (~0.5 A) | 100 Ω (150 mA) |

Inductor sized for continuous conduction (~30 % peak-peak ripple); capacitor sized
to keep output ripple inside the ± tolerance.

## Verified results (LTspice, steady state)

| Converter | Sim Vout | Output ripple (pp) | Inductor ripple (pp) | Spec | Pass |
|---|---|---|---|---|---|
| Buck 15→5 V | 4.66 V | 46 mV | 0.16 A | V3 = 5 V ±0.5 V | ✓ |
| Boost 5→15 V | 14.45 V | 109 mV | 0.16 A | V2 ±1.0 V | ✓ |

**Why Vout is a bit low:** open-loop, the switch `Ron` and the diode forward drop
eat ~0.3 V (buck) and ~0.55 V (boost). In the real system the converters are
**closed-loop** (discrete op-amp feedback), which trims the duty up to hit the
target exactly. Good thing to show in the report: ideal `D·Vin` vs measured, and
the loss budget.

> Note: the boost needs a long enough sim to settle — its output time constant is
> `R·C = 100 Ω × 47 µF = 4.7 ms`, so `boost.net` runs 25 ms (~5 τ) before measuring.
> The buck (`R·C = 0.47 ms`) settles inside 5 ms.

## From model to hardware (the discrete build)

These models use ideal SPICE primitives (`SW` switch + a Schottky-ish diode). The
actual board (Krav 9: **discrete components, no converter ICs**) maps them to:

| Model element | Real part |
|---|---|
| `S1` (SW switch) | **IRF530N** power MOSFET (in the kit) |
| gate `PULSE` source | Arduino PWM → **gate driver** (IR2110, high-side for the buck — see Exp 3A) |
| `MYDIODE` | Schottky freewheel/output diode (e.g. 1N5819) |
| — | + current sense (discrete + op-amp, Krav 10) |

## Next steps
- Swap the ideal `SW` for a real IRF530N SPICE model and the diode for a Schottky model.
- Close the loop (op-amp PI feedback) and re-check the step-response specs
  (V1 100→300 mA, V2 50→150 mA in ≤1 s).
- Optionally draw the graphical `.asc` schematics for the report figures.
