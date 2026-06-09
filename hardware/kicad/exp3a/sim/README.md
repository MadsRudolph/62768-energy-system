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
