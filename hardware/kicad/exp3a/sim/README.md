# Exp 3A — behavioral simulations

The drive/feedback circuits use ICs (IR2110, MCP601, IL300, ILD74) that ngspice has
**no built-in models** for, so we can't sim the real schematics directly the way we did
the buck/boost (which were all SPICE primitives). Instead these are **behavioral**
models that capture each block's *intent* and run cleanly.

Run with PySpice driving its bundled ngspice DLL (py 3.13):
`py -3.13 run_feedback.py` (or load `feedback_behavioral.cir` in any ngspice).

## `feedback_behavioral.cir` — isolated linear amp ✅

Generic single-supply op-amps (tanh soft-rail, 0–5 V) + a behavioral **IL300**
(LED → two matched photodiodes, K3 = K2/K1 ≈ 1). DC-swept the input 0–15 V.

**Result:** `FB_OUT = INPUT / 6`, **dead linear** (ratio 0.16667 across the whole range,
see `fb_transfer.png` / `fb_sweep.csv`). 15 V in → 2.5 V out — ADC-friendly. The servo
node tracks the input exactly, confirming the IL300 servo loop linearises the opto.
Gain is set by `R1/R2` (÷6) and `R5/R3` (×1) with K3 ≈ 1.

### ⚠️ Polarity finding — the as-drawn schematic latches

The sim only converges to this linear transfer when the **LED is driven anode-side by U3**
(U3 *sources* the LED current, so U3↑ → Iled↑ → SERVO↑ = **negative** feedback).

In `feedback_circuit.kicad_sch` as generated, the LED is wired **anode → +5 V, cathode ←
R4 ← U3** (U3 *sinks* it) while U3's **+in = IN_P**. That combination is **positive
feedback** — the loop latches to a rail instead of regulating. Two equivalent fixes:

- **(a)** drive the LED **anode** from U3 (R4 → IL300 pin 1), cathode → GND; or
- **(b)** swap U3's inputs (+in = SERVO, −in = IN_P).

Check the slide to see which it intends, then apply the matching fix.
**Applied:** fix (a) is now in `feedback_circuit.kicad_sch`.

## `drive_behavioral.cir` — PWM motor drive ✅

The opto + IR2110 have no ngspice model, so they're idealised as a **gate PULSE**
(0→12 V, 10 kHz, 50%). The rest is real: **IRF540N** (VDMOS), **DC motor** (Ra=3 Ω +
La=2 mH + 8 V back-EMF), **1N4007** freewheel. Run: `py -3.13 run_drive.py`.

**Result** (steady state, see `drive_waveforms.png`):

| Quantity | Value | Meaning |
|---|---|---|
| SW node, on | ~0.02 V | MOSFET fully enhanced, motor current to GND |
| SW node, off | ~21 V | **freewheel diode clamps the inductive kick** (not a spike) |
| Motor current | ~0.49 A avg, 0.27 A p-p | winding inductance smooths PWM into near-DC |

The current ramps up while the gate is high (motor sees +20 V) and decays through D2
while the gate is low — classic chopper behaviour. This validates the **power stage +
freewheel**; the opto/IR2110 timing itself is trusted from the datasheets.

