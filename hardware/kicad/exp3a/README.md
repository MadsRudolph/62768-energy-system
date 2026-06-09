# Exp 3A reference circuits

The two **Experiment 3A** building blocks, recreated as KiCad 9 schematics
(generated programmatically, connectivity by net labels). These are the
**motor drive** and the **isolated feedback amplifier** — *not* the converters
(see [`../../../docs/system-architecture.md`](../../../docs/system-architecture.md)
for how everything fits together).

| File | What it is |
|---|---|
| `drive_circuit.kicad_sch` | PWM → ILD74 opto → IR2110 → IRF540N → DC motor (the **PWM motor driver**) |
| `feedback_circuit.kicad_sch` | *(planned)* isolated feedback: MCP601 → IL300 linear opto → MCP601 |
| `build_drive.py` | generator for the drive circuit (edit + re-run) |
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

## Open / render / regenerate
```
# open:  drive_circuit.kicad_sch  in KiCad 9
# render: kicad-cli sch export pdf -o drive_preview.pdf drive_circuit.kicad_sch
# regenerate after editing build_drive.py:  py -3.13 build_drive.py
```

ERC shows only benign notes: `lib_symbol_mismatch` (the IR2110/IRF540N/1N4007 are
flattened from KiCad's `extends` symbols — clear with *Tools → Update Symbols from
Library*), the unused 2nd ILD74 channel, and power-flag/external-label notes.
