# QSPICE project — 62768 Electrical Energy System

Circuit-level (SPICE) simulation of the **discrete power electronics** — buck/boost
converters, 3-phase rectifier, gate-drive — to verify designs before building the PCB.
(Complements the Simulink models, which are more system/control level.)

## Open it
Open `energy_system.qsch` in **QSPICE** (free, from Qorvo — installed at
`C:\Program Files\QSPICE`). It's a **blank schematic** to build in.

> The file was created to match QSPICE's `.qsch` format (verified byte-for-byte against
> the installed examples). If for any reason it doesn't open, just make a fresh one in
> QSPICE (**File → New Schematic → Save as `energy_system.qsch`**) — the rest of this
> folder (README, .gitignore) still applies.

## Workflow
1. Draw the converter/rectifier circuit, add a `.tran` directive, simulate.
2. Use it to size L/C, check ripple and switching behaviour, and confirm the discrete
   design before committing it to the KiCad PCB (`../../hardware/kicad/`).

## Notes
- Generated outputs (`*.qraw` waveforms, `*.cir` netlist, etc.) are gitignored — only the
  `.qsch` schematic is tracked.
- Keep component values consistent with `../DC-DC Converters/load_parameters.m` and the
  targets in `../../docs/project-overview.md`.
