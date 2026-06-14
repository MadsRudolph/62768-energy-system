---
name: kicad-laser-pcb
description: >-
  Playbook for the DTU 62768 KiCad → fiber-laser PCB pipeline: reviewing a board
  schematic for design bugs, assigning through-hole footprints, placing the board
  in the 104×104 mm laser-jig format, two-stage Freerouting, and exporting DXF/Gerber
  production files. Use this whenever the user is working on the energy-system team
  repo's hardware — adding or fixing a board, "redo/rebuild the PCB", "fix the
  footprints", "route this board", "make the laser files / DXF / Gerbers", reviewing
  a teammate's converter schematic, or anything touching hardware/kicad/. Reach for
  it even when the user only names one step ("the cap needs a bigger footprint",
  "the gate drive looks wrong") — the surrounding pipeline and its hard-won gotchas
  almost always apply.
---

# KiCad fiber-laser PCB pipeline (DTU 62768)

This repo turns KiCad schematics into single-sided boards etched on an xTool fiber
laser. The flow is battle-tested but full of traps that cost real time; this skill
is the map. **Read `hardware/kicad/WORKFLOW.md` too** — it's the canonical pipeline
doc and this skill complements it. Everything below assumes you're working from
`hardware/kicad/` (PowerShell, Windows).

**First time on this PC?** This skill is shared across the team — if KiCad,
Freerouting, Java, Python+sexpdata, or the Freerouting jar aren't set up yet, do the
one-time install in `references/setup.md` before running anything. The pipeline is
Windows + PowerShell (matching the repo's scripts); a teammate on Mac/Linux can still
do schematic review and footprint edits but the routing/export scripts are
PowerShell-and-KiCad-9-on-Windows.

## The non-negotiables (these come from the laser process, don't fight them)

- **Board outline is fixed at 104×104 mm.** The positioning jig accepts a 109×109 mm
  copper blank; edge cuts sit 2.5 mm inside it. `JIG_W/JIG_H` in `tools/pcb_build.py`.
- **Track 1.0 mm, clearance 0.8 mm.** From the fiber-laser guide. Lives in each
  board's `.kicad_pro` netclass and in `pcb_build.py`. Never lower them.
- **Through-hole only**, with the laser-specific footprint variants (see
  `references/footprints.md`).
- **`.kicad_sch` is the source of truth.** The buck/boost/drive/feedback boards were
  GUI-edited — never regenerate them from old build scripts. Edit schematics in the
  GUI or textually with sexpdata.
- **No AI attribution in commits/code/docs.** Developer-voice commit messages,
  Danish or English to match nearby files.

## Where things are

| Path | What |
|---|---|
| `hardware/kicad/boards/<name>/` | One KiCad project per board (`.kicad_pro/.sch/.pcb`) |
| `hardware/kicad/tools/` | The pipeline scripts (drive these; don't reinvent them) |
| `hardware/kicad/production/<board>/` | DXF + Gerbers + the operator run-plan README |
| `hardware/kicad/bom/footprint_map.csv` | Ordering list (source of truth) → `bom/BOM.md` via `tools/bom_to_md.py` |
| `hardware/kicad/lib/energy_system.pretty` | Project footprints (`*_LaserPads`, custom toroid) |
| Shop CSV (per-PC, optional) | Wherever you saved `dtu_component_shop.csv` — only needed when picking new parts. Ask the user for the path if a task needs it and you can't find it. |
| Freerouting 1.9.0 jar | `%USERPROFILE%\.freerouting\freerouting-1.9.0.jar` (download once — `references/setup.md`) |
| KiCad 9 CLI | default `C:\Program Files\KiCad\9.0\bin\kicad-cli.exe` (the repo scripts assume this; `references/setup.md` if yours differs) |

## Pick your task

Most requests are one of these. Jump to the right section; read the referenced file
when you get there.

1. **Review/fix a schematic** (new board, or a teammate's draft) → start here, then
   `references/schematic-review.md` for the design-bug checklist.
2. **Assign or fix footprints** → `references/footprints.md`.
3. **Build/route/re-export a board (the PCB itself)** → "Running the pipeline" below
   + `references/routing.md`.
4. **Anything misbehaving** → `references/gotchas.md` first. Most "it hangs / it
   won't parse / it crashed" symptoms are known and have one-line fixes.

## Schematic work (review + footprints)

When a schematic arrives — especially a teammate's — **sanity-check it before
committing it to copper.** Run ERC and dump the netlist; trace the power path by
hand. Converter boards have recurring, expensive bugs (floating regulator grounds,
high-side gate drives that can't pull V_GS positive, output caps 100× too small,
optocouplers whose isolation is quietly defeated). The full checklist with the
*why* behind each one is in `references/schematic-review.md` — read it whenever you
review a power schematic.

```powershell
# ERC (0 errors is the bar; lib_symbol_mismatch + single-pin dangling are benign)
& "C:\Program Files\KiCad\9.0\bin\kicad-cli.exe" sch erc -o "$env:TEMP\b.erc" `
    --severity-error --severity-warning boards\<b>\<b>.kicad_sch

# Dump the netlist so you can read net membership by hand (the real check)
& "C:\Program Files\KiCad\9.0\bin\kicad-cli.exe" sch export netlist `
    --format kicadsexpr -o "$env:TEMP\b.net" boards\<b>\<b>.kicad_sch
py -3.13 tools\pcb_netlist_json.py "$env:TEMP\b.net" "$env:TEMP\b.json"
```

Edit schematics textually with sexpdata when scripting (see `tools/retrofit_pcb.py`
and `tools/migrate_refdes_topside.py` for the idioms). **Pick footprints from the
shop CSV first**; assign them per `references/footprints.md`; update
`bom/footprint_map.csv` for every change, then regenerate the markdown BOM with
`py -3.13 tools/bom_to_md.py`.

## Running the pipeline (placement → routing → production)

For the standard boards (`boards/<name>/<name>.*`), one command does the lot:

```powershell
# from hardware\kicad — routes the named boards (or all 7 if -Boards omitted)
.\tools\pcb_make_all.ps1 [-Boards buck,boost]
.\tools\pcb_export_production.ps1
```

`pcb_make_all.ps1` runs: netlist → `pcb_build.py` (placement + 104×104 outline +
`.kicad_pro`) → stage-1 Freerouting on B.Cu → lock → stage-2 for the leftovers on
F.Cu → merge-import + copper refdes + laser zones → DRC + render. **Before you start
a batch, launch the assert-dialog dismisser** (KiCad pops a harmless debug dialog
during DSN export) — the one-liner is in `references/gotchas.md`.

**Acceptance bar: 0 unconnected pads, 0 real DRC errors.** Benign leftovers:
`track_dangling` micro-stubs and `silk_*` warnings. If you see `shorting_items` or
clearance errors right after a route, **re-run that board once** — the SES
merge-import occasionally leaves a transient short that a fresh route clears (seen
on rectifier and mppt). If it persists, the placement is genuinely too tight — open
up the crowded row.

Boards in a non-standard location (e.g. `boards/buck/buck_v2/`) don't match
`pcb_make_all`'s `<name>/<name>` pattern — drive the steps with an explicit-path
script. There's a worked template in `references/routing.md`.

### Re-routing a hand-placed board

When the user has hand-placed a board in the GUI and wants it routed (or re-routed)
keeping their placement: **strip the old routing first** with
`py -3.13 tools/strip_routing.py <board>.kicad_pcb` (textual, via sexpdata — an
in-process `pcbnew` `ZONE.Remove()` access-violates), then run the two-stage route
without re-placing. Template in `references/routing.md`.

## Production output

`pcb_export_production.ps1` writes per board into `production/<board>/`:
- `<board>.dxf` — **bottom copper + edge cuts, mirrored in xTool** (not in the export)
- `<board>_top_cu.dxf` — the wire-bridge plan (single-sided) or top etch; NOT mirrored
- `gerbers/` — full set + Excellon drill

Then update `production/README.md` (the operator run-plan: cut blanks to 109×109,
the per-board top-track count) and `PCB_RESULTS.md`. Compute top-track stats from the
`.kicad_pcb` rather than guessing — see `references/routing.md`.

## After the work

Verify renders look sane (read the `pcb/<board>_top.png`), then commit by explicit
path (the umbrella repo has a broken nested submodule that aborts `git add -A`).
Developer-voice message, no AI attribution. If a teammate pushed meanwhile,
`git pull --rebase --autostash` then push — board work rarely conflicts with report/
sim commits.
