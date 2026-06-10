# CLAUDE.md — 62768 energy-system team repo

Team product repo (KiCad hardware + firmware + simulation + report) for DTU 62768.
Tracks binaries (PDF/.slx/.kicad_*) directly in git — commit and push normally.

## Hard rules
- **NEVER add `Co-Authored-By: Claude` or any AI mention in commits/code/docs.**
  Commit messages read like a developer wrote them (Danish or English, match context).
- `.kicad_sch` files are source of truth — never blindly re-run generator scripts
  over GUI-edited schematics (buck, boost, drive_circuit, feedback_circuit).
- PCB design rules are fixed by the fiber-laser process: track 1.0 mm,
  clearance 0.8 mm. Don't lower them.

## PCB work? Read this first
**`hardware/kicad/WORKFLOW.md`** — the complete, battle-tested pipeline:
schematic generation (sexpdata) → placed board (pcbnew API) → two-stage
Freerouting (B.Cu first, locked, leftovers on F.Cu) → DXF/Gerber production
export. Includes every known gotcha (KiCad assert dialog, Freerouting hangs,
pin-letter traps) and the add-a-new-board checklist.

## Map
| Where | What |
|---|---|
| `hardware/kicad/boards/<name>/` | One KiCad project per board — open the `.kicad_pro` |
| `hardware/kicad/production/` | Laser DXFs + Gerbers + operator run-plan (README) |
| `hardware/kicad/tools/` | The pipeline scripts (see WORKFLOW.md) |
| `hardware/kicad/bom/footprint_map.csv` | Ordering list, substitutions flagged |
| `PCB_RESULTS.md` | Current per-board status (sizes, top-layer usage, design notes) |
| `docs/` | Spec synthesis, system architecture (read before wiring blocks together), datasheets |
| `simulation/`, `firmware/`, `report/` | Simulink models, Arduino code, LaTeX report |

## External context
- Component shop CSV (this PC): `C:\Users\Mads2\Downloads\Misc\dtu_component_shop.csv`
- Fiber-laser guide clone: `..\DTU-PCB-prototyping` (SimsesLab/DTU-PCB-prototyping)
- Course material (slides/spec PDFs): umbrella repo,
  `Obsidian\Courses\62768 Electrical Energy Systems\` (drive-synced)
