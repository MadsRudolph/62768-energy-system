# Exp 3A reference circuits

The two **Experiment 3A** building blocks, recreated as KiCad 9 schematics
(generated programmatically, connectivity by net labels). These are the
**motor drive** and the **isolated feedback amplifier** — *not* the converters
(see [`../../../docs/system-architecture.md`](../../../docs/system-architecture.md)
for how everything fits together).

| File | What it is |
|---|---|
| `drive_circuit.kicad_sch` | PWM → ILD74 opto → IR2110 → IRF540N → DC motor (the **PWM motor driver**) |
| `feedback_circuit.kicad_sch` | isolated linear amp: MCP601 → IL300 linear opto (servo loop) → MCP601 |
| `build_drive.py` / `build_feedback.py` | generators (edit + re-run) |
| `*_preview.pdf` | rendered figures |

## ⚠️ Verify the drive-circuit wiring against the slide

The schematic was built from the reference **image**, so a few connections are
my best read and **should be checked** before trusting it:

- **Opto output:** ILD74 collector (pin 7) → +15 V, emitter (pin 8) → IR2110
  inputs + R2 pulldown. Confirm the opto isn't wired the other way.
- **IR2110 inputs:** I tied both **HIN (10)** and **LIN (12)** to the opto output,
  and **SD (11) → GND** (not shutdown). For a **low-side** motor switch only
  **LIN** matters (LIN → LO); HIN can go to GND. Check which the slide uses.
- **Gate path:** LO (1) → D1 (1N4007) → R3 (10 Ω) → Q1 gate; R4 (1 k) pulldown.
  Confirm **D1's direction**.
- **High-side pins** (VB/VS/HO): unused here (low-side drive) — I tied VS→GND,
  VB→+15 V, HO = no-connect. Fine for low-side, but confirm.

## ⚠️ Verify the feedback-circuit wiring against the slide

Same caveat — built from the image, using the standard IL300 servo topology. Check:

- **Input:** INPUT → R1 (10 k) → U3 +in; R2 (2 k) to GND (input divider). Confirm scaling.
- **Servo loop:** IL300 servo photodiode (pin 3) → U3 −in (`SERVO`), pin 4 → GND, R3 (33 k)
  on that node. This is what linearises the opto — confirm pins 3/4 vs the slide.
- **LED drive (sim-corrected):** U3 out → R4 (200 Ω) → IL300 LED **anode (pin 1)**; cathode
  (pin 2) → **GND**. This is the *negative-feedback* polarity the behavioral sim validated —
  the original anode→+5 V / cathode-sunk wiring was positive feedback and latched. See [`sim/`](sim/).
- **Output:** IL300 output photodiode (pin 6) → U4 −in (`OUT_PD`), pin 5 → GND; R5 (33 k)
  transimpedance feedback (U4 −in → out); U4 +in → GND; U4 out = `FB_OUT`.

## Open / render / regenerate
```
# open:  drive_circuit.kicad_sch  in KiCad 9
# render: kicad-cli sch export pdf -o drive_preview.pdf drive_circuit.kicad_sch
# regenerate after editing build_drive.py:  py -3.13 build_drive.py
```

ERC shows only benign notes: `lib_symbol_mismatch` (the IR2110/IRF540N/1N4007 are
flattened from KiCad's `extends` symbols — clear with *Tools → Update Symbols from
Library*), the unused 2nd ILD74 channel, and power-flag/external-label notes.
