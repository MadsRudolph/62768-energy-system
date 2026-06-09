# System schematics — rectifier / PV front-end / current sense

The three remaining system blocks (per the Kravspecifikation + `docs/system-architecture.md`),
generated the same way as `exp3a/` (sexpdata, net-label connectivity, stock symbols).
Footprints are assigned at generation time — see `../bom/footprint_map.csv`.

| File | Block | Krav |
|---|---|---|
| `rectifier.kicad_sch` | 3-phase 6-diode bridge + ~15 mF → **V1 = 15 V** | 1–3 |
| `mppt.kicad_sch` | PV → 1N5817 → ~15 mF MPPT cap → discrete 5 V linear reg (LM358 + BZX55C5V1 + BD139) → store, + PV V/I sense til Arduino | 9, 11 |
| `current_sense.kicad_sch` | 3× low-side 1 Ω shunt + LM358 ×10.09 → Arduino ADC | 10 |

## Design notes / assumptions

- **"15 mF"** is realised as **3× 4700 µF/50 V in parallel = 14.1 mF** (largest cap in
  the component shop). Close enough for the filter/MPPT-cap job; swap to the kit cap if
  one is supplied.
- **MPPT actuation:** per the spec block diagram the PV branch is *cap + linear
  regulator* (Krav 17 explicitly allows replacing the linear reg with a buck later).
  The P&O algorithm runs on the Arduino using the `PV_V`/`PV_I` sense outputs on J3.
- **MPPT thermals:** the BD139 pass transistor dissipates up to ~7 W at full PV current
  (17 V → 5 V linear drop). It **needs a heatsink**, or replace the stage with a buck.
- **Current sense is low-side** (shunt in each branch's return path). Wiring rule: the
  branch's return wire goes into `J_k pin 1`, system ground continues from `pin 2`.
  PV current channel on the MPPT board is **inverting** (the PV return node sits below
  ground) — gain −9.09, output is positive.
- LM358 chosen because its input range includes ground (TL07x doesn't; MCP6002 max 6 V
  supply can't sit on the PV bus).
- ERC: 0 errors. Remaining warnings are `lib_symbol_mismatch` from flattening `extends`
  symbols — clears with *Tools → Update Symbols from Library* (same as exp3a).

## Regenerate / render

```
py -3.13 build_rectifier.py        # -> rectifier.kicad_sch
kicad-cli sch export pdf -o rectifier_preview.pdf rectifier.kicad_sch
kicad-cli sch erc -o rectifier.erc.txt rectifier.kicad_sch
```
