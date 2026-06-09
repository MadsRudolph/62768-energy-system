# KiCad converter schematics — buck & boost

KiCad 9 schematics of the two self-built DC/DC converters (Krav 8/9), generated
programmatically and matching the LTspice design models in
[`../../../simulation/ltspice/`](../../../simulation/ltspice).

| File | What it is |
|---|---|
| `generate_kicad.py` | Generator (sexpdata) — edit the component tables, re-run to rebuild |
| `buck.kicad_sch` / `boost.kicad_sch` | The KiCad 9 schematics (open directly in KiCad 9) |
| `buck_preview.pdf` / `boost_preview.pdf` | Rendered figures (for the report) |

## How these were generated

The `spicepilot-kicad` library was tried first but its auto-layout only understands
IC topologies (current mirrors, op-amps) and collapsed the whole converter into one
overlapping cluster. So these follow the **proven kicad-skip / sexpdata pattern**
(per the DTU Multimeter project): components placed on an explicit 2.54 mm grid,
connectivity by net labels dropped exactly on each pin, with short wire stubs.

- **Switch** = real N-MOSFET symbol (`Q_NMOS`, valued **IRF540N**) — maps to the kit part.
- **Diode** = `D_Schottky`, valued **1N5819** (freewheel on the buck, output on the boost).
- Internal nets (`SW`, `VOUT_*`, `GND`) are local labels; external interface nets
  (`VIN_*`, `GATE`) are **global-label ports** — they connect to the rest of the system
  (rectifier bus, Arduino PWM) on other sheets.

## Open / render / regenerate

```
# open in KiCad 9 (File > Open)        buck.kicad_sch / boost.kicad_sch
# render a PDF figure
"C:\Program Files\KiCad\9.0\bin\kicad-cli.exe" sch export pdf -o buck_preview.pdf buck.kicad_sch
# regenerate after editing the tables in generate_kicad.py  (needs: pip install sexpdata)
py -3.13 generate_kicad.py
```

## ERC

`kicad-cli sch erc buck.kicad_sch` reports **3 expected notes**, all external-interface:
- `global_label_dangling` ×2 — `VIN_*` and `GATE` "connect elsewhere" (the rectifier
  stage / Arduino). Normal for a standalone sub-circuit sheet.
- `pin_not_driven` ×1 — the MOSFET gate is driven by the external Arduino PWM.

All **internal** nets (SW, VOUT, GND) are clean — the converter itself is fully connected.

## Next steps
- Assign **footprints** (THT/SMD) so the schematic can drive a PCB layout.
- Swap the generic `Q_NMOS` for an IRF540N library symbol + add the **gate driver**
  (IR2110, high-side for the buck — see Exp 3A) and current sense (Krav 10).
- Optionally merge into the main `energy_system.kicad_sch` as sub-sheets.
