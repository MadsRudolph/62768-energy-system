---
name: kicad-laser-pcb
description: >-
  Self-contained playbook + scripts for turning a KiCad schematic into a single-sided
  PCB etched on an xTool fiber laser (the DTU 62768 process): reviewing a board
  schematic for design bugs, assigning through-hole footprints, placing the board in
  the 104×104 mm laser-jig format, two-stage Freerouting, and exporting DXF/Gerber
  production files. Use this whenever someone is preparing a KiCad board for the fiber
  laser — "redo/rebuild the PCB", "fix the footprints", "route this board", "make the
  laser files / DXF / Gerbers", reviewing a buck/boost/converter schematic, or sizing
  a board to the laser jig. Reach for it even when only one step is named ("the cap
  needs a bigger footprint", "the gate drive looks wrong") — the surrounding pipeline
  and its hard-won gotchas almost always apply. Works on any KiCad 9 project; bundles
  its own scripts and footprint library, no special repo required.
---

# KiCad fiber-laser PCB pipeline (DTU 62768)

This skill turns KiCad schematics into single-sided boards etched on an xTool fiber
laser. The flow is battle-tested but full of traps that cost real time; this is the
map. **It is self-contained** — the scripts and the laser-specific footprint library
travel inside the skill (`scripts/`, `lib/`), so it works on any KiCad 9 project
without a special repo. Commands are PowerShell on Windows.

In the snippets below, `<skill>` is this skill's own directory (the folder containing
this SKILL.md). `<proj>` is the user's KiCad project. Use absolute paths if unsure.

**First time on this PC?** If KiCad 9, Java 21, Python 3.13 + sexpdata, or the
Freerouting jar aren't installed yet, do the one-time setup in `references/setup.md`
first. Schematic review and footprint edits work on any OS; the routing/export scripts
are Windows + PowerShell + KiCad 9.

## The non-negotiables (these come from the laser process, don't fight them)

- **Board outline is fixed at 104×104 mm.** The positioning jig accepts a 109×109 mm
  copper blank; edge cuts sit 2.5 mm inside it. (`JIG_W/JIG_H` in `scripts/pcb_build.py`
  — change there if your jig differs.)
- **Track 1.0 mm, clearance 0.8 mm.** From the fiber-laser guide; `pcb_build.py` bakes
  this into the board's netclass + `.kicad_pro`. Don't lower them.
- **Through-hole only**, with the laser-specific footprint variants (see
  `references/footprints.md`).
- **`.kicad_sch` is the source of truth.** Once a board is hand-edited in the GUI,
  don't regenerate it from a build script — edit the schematic in the GUI or textually
  with sexpdata, and re-route keeping the placement.
- **No AI attribution in commits/code/docs.** Developer-voice commit messages.

## What's bundled here vs. what's yours

| In this skill (`<skill>/…`) | What |
|---|---|
| `scripts/route_board.ps1` | One-shot: build (or re-route) a board + two-stage Freerouting + DRC |
| `scripts/export_production.ps1` | Laser DXFs + Gerbers for a board |
| `scripts/pcb_build.py` | Netlist-JSON → placed 104×104 board (+ `.kicad_pro` with the netclass) |
| `scripts/pcb_route.py` | DSN export / SES import primitives for the two-stage route |
| `scripts/pcb_netlist_json.py`, `strip_routing.py`, `bom_to_md.py`, `fix_text_collisions.py` | Helpers |
| `lib/energy_system.pretty/` | Laser footprints: `*_LaserPads` TO-220/TO-126, the measured toroid |
| `lib/make_laserpads.py` | Regenerates the `*_LaserPads` TO footprints from stock KiCad |

| In the user's project | What |
|---|---|
| `<proj>/…/<board>.kicad_sch` / `.kicad_pcb` / `.kicad_pro` | Their board |
| Shop CSV (`dtu_component_shop.csv`, per-PC, optional) | Only when picking new parts — ask for the path |

## Pick your task

1. **Review/fix a schematic** → "Schematic work" below, then `references/schematic-review.md`.
2. **Assign or fix footprints** → `references/footprints.md`.
3. **Build/route/re-export a board** → "Running the pipeline" + `references/routing.md`.
4. **Anything misbehaving** → `references/gotchas.md` first. Most "it hangs / won't
   parse / crashed" symptoms are known and have one-line fixes.

## Schematic work (review + footprints)

When a schematic arrives — especially someone else's — **sanity-check it before
committing it to copper.** Run ERC and dump the netlist; trace the power path by hand.
Converter boards have recurring, expensive bugs (floating regulator grounds, high-side
gate drives that can't pull V_GS positive, output caps 100× too small, optocouplers
whose isolation is quietly defeated). The checklist with the *why* behind each is in
`references/schematic-review.md` — read it whenever you review a power schematic.

```powershell
$kc = "C:\Program Files\KiCad\9.0\bin\kicad-cli.exe"   # adjust if yours differs
# ERC (0 errors is the bar; lib_symbol_mismatch + single-pin dangling are benign)
& $kc sch erc -o "$env:TEMP\b.erc" --severity-error --severity-warning <proj>\<board>.kicad_sch
# Dump the netlist so you can read net membership by hand (the real check)
& $kc sch export netlist --format kicadsexpr -o "$env:TEMP\b.net" <proj>\<board>.kicad_sch
py -3.13 <skill>\scripts\pcb_netlist_json.py "$env:TEMP\b.net" "$env:TEMP\b.json"
```

Pick footprints from the shop CSV first (ask the user for its path), assign per
`references/footprints.md`, and keep a BOM CSV if you like
(`py -3.13 <skill>\scripts\bom_to_md.py` renders it to markdown — it expects a
`footprint_map.csv` next to it; see the script header).

## Running the pipeline (build → route → production)

`route_board.ps1` does netlist → placement → two-stage route → DRC for one board.
**Launch the assert-dialog dismisser first** (KiCad pops a harmless debug dialog
during DSN export — one-liner in `references/gotchas.md`), then:

```powershell
# fresh board from a schematic:
<skill>\scripts\route_board.ps1 -Sch <proj>\<board>.kicad_sch -Pcb <proj>\<board>.kicad_pcb
# export laser files:
<skill>\scripts\export_production.ps1 -Pcb <proj>\<board>.kicad_pcb -OutDir <proj>\production\<board>
```

`-Jar` and `-KicadBin` parameters override the Freerouting jar / KiCad path if yours
aren't at the defaults. The route does: place at 104×104 → stage-1 Freerouting on
B.Cu → lock → stage-2 for the leftovers on F.Cu → merge-import + copper refdes + laser
zones → DRC. How and why, plus the manual step-by-step, is in `references/routing.md`.

**Acceptance bar: 0 unconnected pads, 0 real DRC errors.** Benign leftovers:
`track_dangling` micro-stubs and `silk_*` warnings. If you see `shorting_items` or
clearance errors right after a route, **re-run that board once** — the SES
merge-import occasionally leaves a transient short a fresh route clears. If it
persists, the placement is genuinely too tight; for a dense board add a `PLACE` entry
in `pcb_build.py` (examples are in it) that follows the signal flow, or hand-place in
the GUI and re-route (next section).

### Re-routing a hand-placed board

To route (or re-route) a board you've placed in the GUI, keeping that placement, pass
`-KeepPlacement` — it strips the old routing first (textually, because an in-process
`pcbnew` zone removal access-violates) then routes:

```powershell
<skill>\scripts\route_board.ps1 -Pcb <proj>\<board>.kicad_pcb -KeepPlacement
```

## Production output

`export_production.ps1` writes `<board>.dxf` (**bottom copper + edge cuts — mirror in
xTool**), `<board>_top_cu.dxf` (wire-bridge plan / 2nd etch, not mirrored), an optional
silk DXF, and `gerbers/` (full set + Excellon drill). **Cut blanks to 109×109 mm.**
Read top-track stats from the `.kicad_pcb` rather than guessing — snippet in
`references/routing.md`.

## After the work

Verify the render looks sane (the route writes `<board>_top.png`/`_bottom.png` next to
the board if you render — or open it in KiCad). Commit in the user's own repo with a
developer-voice message, no AI attribution.
