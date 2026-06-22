# PCB workflow — schematic → board → routing → production files

Playbook for (AI-)sessions working on this repo's hardware. This exact flow built
all 7 boards (schematic generation, placement, two-stage autorouting, DXF/Gerber
export) — follow it and you inherit every lesson learned. Commands are PowerShell,
run from `hardware/kicad/` unless noted.

## 0. Environment (verify before starting)

| Tool | Path / check |
|---|---|
| KiCad 9 CLI | `& "C:\Program Files\KiCad\9.0\bin\kicad-cli.exe" version` |
| KiCad python (pcbnew) | `& "C:\Program Files\KiCad\9.0\bin\python.exe" -c "import pcbnew"` |
| System python + sexpdata | `py -3.13 -c "import sexpdata"` |
| Java 21 (NOT 25-only jars) | `java -version` |
| Freerouting **1.9.0** | `%USERPROFILE%\.freerouting\freerouting-1.9.0.jar` (download: github.com/freerouting/freerouting/releases/tag/v1.9.0). **NOT 2.0.1** — its version-check/API NPE can eat the SES save (job "hangs" forever after routing). v2.2+ needs Java 25 and will NOT run here. |
| Component shop CSV | `C:\Users\Mads2\Downloads\Misc\dtu_component_shop.csv` (1464 parts; columns Category, Subcategory, Part_Number, Value, Description) |
| Stock symbol/footprint libs | `C:\Program Files\KiCad\9.0\share\kicad\{symbols,footprints}` |

## 1. Schematics (generated, not drawn)

Schematics are **generated programmatically** with `tools/schbuild.py` (sexpdata).
Each board has a generator in `tools/generators/build_<board>.py` — copy one as a
template for a new board. Pattern:

- Components = list of dicts: `{"lib": "Device:R", "ref": "R1", "val": "10k",
  "fp": "<footprint-id>", "x":.., "y":.., "ang":.., "unit":.., "nets": {pin: net}}`.
- **Connectivity is by net labels** (a stub wire + label per pin) — no wire routing.
  Nets in the `globals_` set become global labels; the rest are local.
- Pin coordinates are read automatically from the installed KiCad libs
  (`schbuild.pins()`), including `extends`-flattening — no hand-typed pin tables.
- **Footprints are assigned at generation time** (the `fp` key). See §1.2.
- Multi-unit parts (LM358 = unit 1/2/3): one dict per unit, same `ref`.
- Add `power:PWR_FLAG` symbols on supply nets fed from connectors, otherwise ERC
  errors `power_pin_not_driven`.
- After generating: ERC + preview, both must be checked:
  ```powershell
  py -3.13 tools\generators\build_<board>.py
  & "C:\Program Files\KiCad\9.0\bin\kicad-cli.exe" sch erc -o "$env:TEMP\x.erc" boards\<b>\<b>.kicad_sch
  & "C:\Program Files\KiCad\9.0\bin\kicad-cli.exe" sch export pdf -o boards\<b>\<b>_preview.pdf boards\<b>\<b>.kicad_sch
  ```
  **Goal: 0 ERC errors.** Benign warnings: `lib_symbol_mismatch` (from extends-
  flattening) and single-pin `global_label_dangling`.

### 1.1 Hand-edited schematics

`boards/{buck,boost,drive_circuit,feedback_circuit}` were GUI-edited —
**the `.kicad_sch` is source of truth, never regenerate them** from old build
scripts. Edit with sexpdata (see `tools/retrofit_pcb.py` for the editing idioms:
`set_footprint`, `remove_symbol`, `add_symbol`, `label_at`) or in the KiCad GUI.

### 1.2 Component & footprint rules (fiber-laser process)

- Pick parts from the **shop CSV** first; course-kit-only parts (IR2110, IL300,
  ILD74, MCP601) get footprints from their datasheets in `docs/datasheets/`.
  Update `bom/footprint_map.csv` for every change (ref → part → footprint → notes,
  substitutions FLAGGED).
- Footprints: THT only. Standard picks:
  R axial → `Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal`;
  100n → `Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm`;
  elko → `Capacitor_THT:CP_Radial_D8.0mm_P3.50mm` (4700µ → `D18.0mm_P7.50mm`);
  diode → `Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal` (zener → DO-35);
  **DIP → `Package_DIP:DIP-x_W7.62mm_LongPads`** (laser guide requirement);
  **TO-220 → `energy_system:TO-220-3_Vertical_LaserPads`** (project lib, pads
  narrowed to 1.7 mm so the pin-to-pin gap meets 0.8 mm — regenerate with
  `lib/make_laserpads.py`);
  power in/out → `TerminalBlock:TerminalBlock_bornier-2_P5.08mm` (or -3);
  signal → `Connector_PinHeader_2.54mm:PinHeader_1xNN_P2.54mm_Vertical`.
- **TO-126 (BD139 etc.) can NEVER meet the 0.8 mm rule** (2.28 mm pitch) — pick a
  TO-220 part instead (e.g. TIP41A, in the shop).
- Op-amps: LM358 if inputs must reach GND (low-side sensing); TL07x can't;
  MCP6002 max 6 V supply.
- Verify any new footprint name exists on disk before using it
  (`Test-Path "<libdir>\<Lib>.pretty\<Name>.kicad_mod"`).

## 2. Board generation (placement)

`tools/pcb_build.py` (run via KiCad's python) turns a netlist-JSON into a placed
`.kicad_pcb` + a `.kicad_pro` next to it (project file carries the 0.8/1.0 mm
netclass — required so GUI routing keeps the rules):

- Components on top, copper routed on **B.Cu** (etch side). Board outline =
  closed RECT on Edge.Cuts (segments trigger a KiCad assert — see §5).
- **Board size is FIXED at 104×104 mm** (`JIG_W/JIG_H` in pcb_build.py): the
  laser positioning jig takes a 109×109 mm copper blank, edge cuts sit 2.5 mm
  inside. Components are packed compactly (5 mm bbox gap); pcb_build fails hard
  if a board's content doesn't fit the square.
- Auto-placement: odd-numbered J + terminal-footprint M1 → left edge, even J →
  right edge, rest row-packed. **For dense boards add an explicit entry to the
  `PLACE` dict** (mppt and current_sense have them) — place along the signal
  flow, channels in rows; this is what cut their jumper counts ~50%.
- Spacing intuition: 4700µ caps need ≥20 mm pitch; TO-220 near big caps needs
  margin; connectors inset 15 mm from the edge; keep top rows ≥4 mm from the
  edge (silkscreen clearance).
- `put()` centers the **bounding box** at the target (footprint anchors are pad 1
  — naive SetPosition makes DIPs overlap their neighbours).
- **Pin-letter trap:** `Device:Q_NMOS` pins are named G/D/S but TO-220 pads are
  1/2/3; `pcb_build.py` maps G/D/S→1/2/3 and FAILS HARD if any component ends up
  with zero netted pads. If you add a symbol with non-numeric pins, extend that map.

## 3. Routing (two-stage Freerouting — this is the secret sauce)

Run the whole thing per board (or all) with:
```powershell
.\tools\pcb_make_all.ps1 [-Jar <path>\freerouting-1.9.0.jar] [-Boards buck,mppt]
```
What it does per board — replicate exactly if scripting by hand:

1. Netlist: `kicad-cli sch export netlist --format kicadsexpr` →
   `tools/pcb_netlist_json.py` → `tools/pcb_build.py`.
2. **Stage 1 (bottom only):** export DSN (`pcb_route.py dsn`), then text-replace
   `(layer F.Cu (type signal))` → `(type power)` — Specctra routers skip power
   layers, so Freerouting routes B.Cu only. Route, import with `pcb_route.py
   sesraw` (no decorations yet).
3. **Stage 2 (top for the leftovers):** `pcb_route.py lockdsn` locks all existing
   tracks → they export as `(type fix)` so Freerouting cannot rip them; route
   again with both layers live. Only the impossible crossings end up on F.Cu.
4. Final import `pcb_route.py ses`: **merge-import** (Freerouting does NOT
   re-emit fixed wires in its SES, so the importer snapshots the tracks and
   re-adds whatever the import dropped), then adds **refdes text on F.SilkS**
   (silkscreen, top/component side, not mirrored — NEVER on copper, a name on F.Cu
   would etch as top copper). The footprint's own reference is hidden so there's
   exactly one clean label per part; placement only avoids pads (silk over copper
   is fine), so nothing is dropped on a normal board. Also adds **no-net solid
   laser zones** on both copper layers (pad connection: none — the guide's
   engraving hack). The step is idempotent (materializes the old text + zone lists
   before any Remove() — a Remove invalidates KiCad's SWIG iterators — and clears
   old F.Cu/B.Cu copper refdes too, so pre-silk boards migrate on a re-run).
5. DRC + renders into `boards/<b>/pcb/`.

**Acceptance bar: 0 unconnected items, 0 DRC errors.** Benign leftovers:
`track_dangling` micro-stubs from the merge, `silk_over_copper`/`silk_overlap`
(silkscreen isn't part of the laser flow), and `zones_intersect` must NOT appear
(if it does, the finish step ran twice on an old board — just re-run the board).

## 4. Production files (DXF for the xTool laser + Gerbers)

```powershell
.\tools\pcb_export_production.ps1
```
Per board into `production/<board>/`:
- `<board>.dxf` — **bottom copper + Edge.Cuts in ONE file**, drill marks *Small*,
  mm, no contour mode (`kicad-cli pcb export dxf --mode-single -l "B.Cu,Edge.Cuts"
  --ou mm --drill-shape-opt 1`). This is the file the xTool gets; it is
  **mirrored in xTool**, not in the export.
- `<board>_top_cu.dxf` — F.Cu + Edge.Cuts. Wire-bridge plan (single-sided build)
  or second etch side (NOT mirrored in xTool).
- `<board>_silk_top.dxf` — optional top-side refdes engraving (NOT mirrored).
- `gerbers/` — `kicad-cli pcb export gerbers -l "F.Cu,B.Cu,Edge.Cuts,B.Mask,F.Mask,
  F.Silkscreen,F.Fab"` + `export drill --format excellon`.

Then update `production/README.md` (cut sizes = board + 2 mm, the top-layer
table) and `PCB_RESULTS.md`. The operator checklist for the machine lives in
`production/README.md`; the upstream guide is the clone at
`..\..\..\DTU-PCB-prototyping` (SimsesLab/DTU-PCB-prototyping).

## 5. Gotchas (every one of these cost real time)

| Symptom | Cause / fix |
|---|---|
| Blocking dialog "wxWidgets Debug Alert … non-closed outline" during DSN export | KiCad-stable debug assert; harmless. Run this dismisser in a background job during batches: `$sh=New-Object -ComObject WScript.Shell; while($true){if($sh.AppActivate("wxWidgets Debug Alert")){Start-Sleep -m 150;$sh.SendKeys("n")};Start-Sleep -m 400}` |
| Freerouting hangs after "Route optimization completed" | Flaky save phase — can take 1–3 min normally; >5 min = hung. Kill java, re-run that board. NEVER launch java with `-WindowStyle Hidden` (kills its GUI event pump → guaranteed hang). Run it in the console. |
| Freerouting "File not found" on a DSN that exists / "Non-ansi character at position 0" / hangs forever burning CPU | **BOM in the DSN.** Windows PowerShell 5.1's `Set-Content -Encoding UTF8` writes a UTF-8 BOM (pwsh 7 doesn't) and Freerouting's parser chokes on it. Write the masked stage-1 DSN with `[System.IO.File]::WriteAllText(...)` (BOM-less) — `pcb_make_all.ps1` does this now. |
| Freerouting 2.0.1 routes (CPU busy) but never writes the SES; `NullPointerException ... gson.JsonObject.get(String) is null` in the log | 2.0.1's VersionChecker/API phone-home NPEs and takes the job-completion chain with it. Use the **1.9.0 jar** (pure local CLI, same DSN/SES formats, runs on Java 21; the NPE is a harmless daemon-thread warning there). |
| Freerouting exits instantly, no SES | Wrong Java (2.2.x jars need Java 25). Use the 1.9.0 jar. |
| SES import wiped the stage-1 routing | Fixed wires aren't in Freerouting's SES — use `pcb_route.py ses` (merge-import), never a raw import after stage 2. |
| MOSFET/transistor pads end up `<no net>` (and DRC stays quiet about it!) | Symbol has letter pin numbers vs numeric pads — §2 pin-letter trap. The fail-hard check in pcb_build catches whole-component cases. |
| `power_pin_not_driven` ERC errors | Add PWR_FLAG symbols on connector-fed supply nets. |
| KiCad GUI routes with 0.2 mm clearance | The board was opened without its `.kicad_pro` (netclass lives there). Open the project file, not the bare .kicad_pcb. |
| "Update PCB from Schematic" unlinks everything | Tick "Re-link footprints to schematic symbols based on their reference designators" — script-built boards have no symbol UUIDs. |
| ZONE.Remove() via pcbnew crashes/corrupts the session (access violation, SWIG iteration breaks) | Never Remove zones in-process on loaded boards. Edit the .kicad_pcb textually with sexpdata instead (see `tools/migrate_refdes_topside.py`) and refill zones in a CLEAN session (`tools/refill_zones.py`). |
| `import json` (or similar) inside a function | Shadows the module-level import → UnboundLocalError at the top of the function. Imports at module level. |
| PowerShell eats inline python with quotes/braces | Write a temp .py file instead of `py -c` for anything non-trivial; `git stash drop 'stash@{0}'` needs quotes. |

## 6. Checklist: adding a brand-new board

1. Write `tools/generators/build_<name>.py` (copy `build_rectifier.py`); pick parts
   from the shop CSV; footprints per §1.2. Output goes to `boards/<name>/`.
2. `New-Item boards\<name>` is created by the generator's output path; copy
   `fp-lib-table` + `sym-lib-table` from another board folder.
3. Generate, ERC (0 errors), export preview PDF.
4. Add rows to `bom/footprint_map.csv`.
5. Add `<name>` to the board list in `tools/pcb_make_all.ps1` AND
   `tools/pcb_export_production.ps1`.
6. Run the pipeline; if >5 airwires after stage 1 or DRC noise, add a `PLACE`
   entry in `tools/pcb_build.py` following the signal flow; re-run.
7. Export production files; update `production/README.md` (cut size = W+2 × H+2,
   top-layer row) and `PCB_RESULTS.md`.
8. Commit (developer voice, Danish or English matching nearby files,
   **never any AI attribution**) and push.

## 7. Repo conventions

- `boards/<name>/` = one self-contained KiCad project (pro+sch+pcb, same basename).
- Schematic `.kicad_sch` is ALWAYS source of truth over generator scripts.
- Design rules: track 1.0 mm, clearance 0.8 mm — never lower them; they come from
  the fiber-laser guide and live in each `.kicad_pro` + `pcb_build.py`.
- Danish in component comments/board docs is fine (matches the repo); this file
  and code comments mix freely.
- Commits: plain developer style. **No Co-Authored-By, no AI mentions.**
