# KiCad project — 62768 Electrical Energy System

PCB design for the energy system. **KiCad 9**.

## Open it
Open `energy_system.kicad_pro` in KiCad → it loads the schematic and PCB.
The files are blank starting points; **on first save** KiCad rewrites them to the
exact 9.0 format (if it mentions an older version on open, that's expected — just save).

| File | What |
|------|------|
| `energy_system.kicad_pro` | Project file (open this) |
| `energy_system.kicad_sch` | Schematic (empty) |
| `energy_system.kicad_pcb` | PCB layout (empty, 2-layer to start) |

## Workflow
1. Draw the schematic (Eeschema) → annotate → assign footprints.
2. Update PCB from schematic → place + route (Pcbnew).
3. Export: schematic PDF → `../schematics/`, BOM → `../bom/`, Gerbers/drill for fab.

## Notes
- Backups, autosave, and per-user settings (`*-backups/`, `_autosave-*`, `*.kicad_prl`)
  are gitignored — only the real project/sch/pcb (and any project libraries) are tracked.
- For shared parts, add a project footprint library `energy_system.pretty/` and a custom
  `energy_system.kicad_sym`, then register them in the project's library tables.
- Commit `.kicad_sch` / `.kicad_pcb` after saving so teammates get your changes (KiCad
  files are text/S-expression and diff/merge reasonably, but coordinate big edits to
  avoid conflicts).
