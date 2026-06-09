# KiCad converter schematics — buck & boost

KiCad 9 schematics of the two self-built DC/DC converters (Krav 8/9), generated
programmatically and matching the LTspice design models in
[`../../../simulation/ltspice/`](../../../simulation/ltspice).

| File | What it is |
|---|---|
| `buck.kicad_sch` / `boost.kicad_sch` | The KiCad 9 design schematics (open directly in KiCad 9) |
| `buck_sim.kicad_sch` / `boost_sim.kicad_sch` | Simulation copies (opto excluded, gate driven by a PULSE source, ngspice models assigned) — open and Run in the KiCad simulator |
| `models/` | ngspice device models loaded by the sim sheets: `IRF530N.lib` (VDMOS), `1N5819.lib` (Schottky) |
| `buck_preview.pdf` / `boost_preview.pdf` | Rendered figures (for the report) |
| `buck_build.py` | Builds the wired buck (rotation-aware, V_in source + GND rail) |
| `add_optocoupler.py` | Injects the isolated optocoupler gate-drive block (`GND`- or `SW`-referenced) |
| `generate_kicad.py` | Original from-scratch generator (label-stub style, pre-rework) |

> **Simulating:** the `*_sim.kicad_sch` sheets drive the gate with a PULSE source
> (the opto is excluded — its isolated grounds break ngspice). Open one, set a
> transient (`5m`/`1u` for buck, `25m`/`1u` for boost), Run, and probe `V(VOUT_*)`.
> Models are referenced relatively as `models/*.lib`.

## How these were generated

The `spicepilot-kicad` library was tried first but its auto-layout only understands
IC topologies (current mirrors, op-amps) and collapsed the whole converter into one
overlapping cluster. So these follow the **proven kicad-skip / sexpdata pattern**
(per the DTU Multimeter project): components placed on an explicit 2.54 mm grid,
connectivity by net labels dropped exactly on each pin, with short wire stubs.

- **Switch** = real N-MOSFET symbol (`Q_NMOS`, valued **IRF530N**) — maps to the kit part.
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

## Isolated gate drive (optocoupler)

Each converter's MOSFET gate is driven through a **4N25 optocoupler** for galvanic
isolation between the Arduino and the power stage (non-inverting):

```
PWM (Arduino) -> R1 330 -> 4N25 LED -> GND_MCU        (isolated logic side)
4N25 transistor: collector -> +12V supply, emitter -> GATE
R2 10k: gate pulldown -> reference
```

- **Boost** (low-side switch): pulldown -> `GND`, supply `+12V`.
- **Buck** (high-side switch): pulldown -> `SW`, floating supply `+12V_SW`. The gate is
  referenced to the MOSFET **source = SW node** (not GND), since V_gs is measured against
  the source. The opto's isolation is what lets this side float on SW.

> ⚠️ **Drive strength:** a 4N25 phototransistor gives isolation but only ~2 mA of drive.
> The IRF530N's gate charge (~34 nC) charges in ~17 µs at 2 mA — workable at **10 kHz**
> but still marginal at 50 kHz. For fast, clean switching add a **BJT totem-pole buffer**
> (BD139 + PNP) after the opto, and/or keep the switching frequency low.

## ERC

Both report **3 expected notes**, all external-interface `global_label_dangling`:
`PWM`, `GND_MCU`, and the `+12V*` gate-drive rail — they connect to the rest of the
system on other sheets. All **internal** nets (SW, VOUT, GND, GATE) are clean.

## Next steps
- Add the **BJT gate-drive buffer** after each optocoupler (see drive-strength note).
- Assign **footprints** (THT) so the schematic can drive a PCB layout.
- Add current sense (Krav 10); optionally merge into `energy_system.kicad_sch` as sub-sheets.
