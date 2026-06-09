# PCB & Footprint Handoff — 62768 Energy System

**You are a fresh Claude Code session spawned at the repo root**
`C:\Users\Mads2\DTU\4. Semester\Electrical Energy Systems\team` (the team's KiCad/firmware
repo — a *separate* git repo, GitHub `MadsRudolph/62768-energy-system`, that tracks its
own binaries directly). Your job is the **hardware/PCB** phase. Read this whole file, then
read the linked docs before touching anything.

> **Research hard.** You're encouraged to clone external git repos (KiCad footprint libs,
> Freerouting, etc.), fetch datasheets, and download footprints from SnapEDA or similar
> when it helps. Don't guess a footprint — verify the package against the datasheet.

---

## 0. The mission (three tasks)

1. **Generate the remaining system schematics** (see §5) — the circuits not built yet.
2. **Assign correct footprints** to every real schematic, sourced from the component shop
   CSV + datasheets, into the project footprint library (§3, §4).
3. **Produce a single-layer PCB per board** where feasible (§6).

Quality bar: ERC-clean (or only the known-benign warnings), every component has a *real*
footprint that matches the physical part, a BOM mapping table, and a rendered PCB preview
per board. Flag — don't silently substitute — any part with no shop equivalent.

---

## 1. Orient yourself first (read these, in order)

- `README.md` (repo root) — team repo layout.
- `docs/system-architecture.md` — **the 4 circuits and how they connect** (motor drive,
  feedback, buck, boost are *separate* stages — don't cross-wire). Read this before
  designing any new schematic.
- `docs/project-overview.md` — the spec synthesis: the 18-requirement table, V1/V2/V3
  targets, which lecture drives each subsystem.
- `hardware/kicad/exp3a/README.md` and `hardware/kicad/sim/README.md` *(under exp3a/sim)* —
  what the drive/feedback circuits are + the verify-against-slide caveats + sim results.
- `../../../CLAUDE.md` (umbrella repo) — project handoff notes (the team-repo is gitignored
  from the umbrella; work inside `team/` with its own git).

**Course material** (lectures, datasheets, the official spec) lives at
`C:\Users\Mads2\DTU\Obsidian\Courses\62768 Electrical Energy Systems\`:
- `Literature\Project Specifications.pdf` — **the Kravspecifikation** (authoritative
  requirements; drives what schematics are needed).
- `Literature\Datasheets\` and `team/docs/datasheets/` — datasheets for the Exp 3A parts
  (IR2110, IRF540, MCP601, IL300, ILD74). **Use these to confirm pinouts + packages.**
- `Slides\` — Lec 2 (buck/boost), Lec 3 (PMSM), Lec 4 (3φ rectifier), Lec 5 (choppers),
  Lecture 1 Modeling (motor/gen + MPPT).
- ⚠️ Those PDFs are **gitignored/Drive-synced** in the umbrella; if missing, run
  `python C:\Users\Mads2\DTU\Obsidian\scripts\drive-sync\download.py`.

---

## 2. Current state — what exists

### Real schematics (these get footprints + PCBs)
| File | Circuit | Key parts |
|---|---|---|
| `hardware/kicad/converters/design/buck.kicad_sch` | Buck converter | M1 IRF530N, D1 1N5819, L1, C1 470u/47u, R1/R2, U1 4N25 opto |
| `hardware/kicad/converters/design/boost.kicad_sch` | Boost converter | M1 IRF530, D1 1N5819, L1, C 470u/47u, R, U1 4N25 opto |
| `hardware/kicad/exp3a/drive_circuit.kicad_sch` | Motor PWM drive | Q1 IRF540N (+ BUZ11), U1 IR2110, U2 ILD74, D 1N4007/1N4001, M1 Motor_DC, R/C, PWR_FLAGs |
| `hardware/kicad/exp3a/feedback_circuit.kicad_sch` | Isolated feedback | U1 IL300, U3/U4 MCP601, R1–R5 |

> ⚠️ **The `.kicad_sch` files are the source of truth — NOT the `build_*.py` scripts.**
> The schematics have hand-edits in KiCad beyond what the generators produce (e.g.
> `drive_circuit` now has BUZ11, PWR_FLAGs, a 1N4001 that aren't in `build_drive.py`).
> **Do not blindly re-run the build scripts — you'll lose edits.** Edit the `.kicad_sch`
> directly (sexpdata, the established pattern) or in the KiCad GUI.

### NOT for PCB
- `hardware/kicad/converters/sim/*.kicad_sch` — **simulation-only** (ngspice). Skip them.
- `hardware/kicad/exp3a/sim/*` — behavioral SPICE sims (PySpice/ngspice). Skip.

### Library scaffold (already wired up)
- `hardware/kicad/energy_system.kicad_sym` — project **symbol** lib (currently empty).
- `hardware/kicad/energy_system.pretty/` — project **footprint** lib (currently just
  `.gitkeep`). **This is your "footprints folder."**
- `hardware/kicad/fp-lib-table` + `sym-lib-table` — already register the above as lib
  `energy_system` via `${KIPRJMOD}`. Drop new `.kicad_mod` footprints into the `.pretty`
  folder and they're immediately available as `energy_system:<name>`.

### How schematics are generated (the pattern)
`build_drive.py` / `build_feedback.py` / `converters/design/generate_kicad.py` use
**`sexpdata`** to emit `.kicad_sch` directly. Key conventions (see `exp3a/build_drive.py`):
- Stock symbols pulled from `C:\Program Files\KiCad\9.0\share\kicad\symbols`.
- Inherited symbols (`extends`) must be **flattened** (copy base graphics renamed).
- Component origins on the **2.54 mm grid**; net-label connectivity (no wire routing).
- `_prop("Footprint","",...)` is where the footprint string goes — **currently empty**.

---

## 3. Component sourcing — TWO sources

### A) The component shop CSV (passives + generics)
`C:\Users\mads2\Downloads\Documents\dtu_component_shop.csv` — 1464 parts the team can buy.
Columns: `Category, Subcategory, Part_Number, Value, Description`. **Everything is
through-hole (THT)** — good for a single-layer board. Categories: Resistor (673, E96 1/4W
THT), IC (357), Capacitor (138, ceramic/film/electrolytic), Transistor (93), Diode (91),
Inductor (38), Optocoupler (5), Connector, LED, Photodiode, …

Use this to pick the **real orderable part** for each schematic component, then map that
to a footprint (§4).

### B) Course-kit ICs (the Exp 3A specialised parts)
Several schematic ICs are **NOT in the shop CSV** — they come from the course kit (the
team physically has them; datasheets are in `docs/datasheets/`). These still need
footprints, just sourced by package from the datasheet.

### ⚠️ Substitution flags — resolve these explicitly (don't guess)
| Schematic part | In shop? | Action |
|---|---|---|
| **IRF540N / IRF530N** | ✅ `IRF540`, `IRF530` (N-MOSFET) | Use directly. TO-220-3. |
| **BUZ11** | check CSV | N-MOSFET TO-220; confirm or swap to IRF540. |
| **4N25** | ✅ `4N25` (Optocoupler THT) | DIP-6. |
| **1N5819** (Schottky) | ⚠️ closest `1N5817` (Schottky 1A) | Use 1N5817, DO-41. Flag the swap. |
| **1N4007 / 1N4001** | ⚠️ `1N4006`/`1N4003` (rectifier) | Use closest voltage rating, DO-41. |
| **MCP601** (op-amp) | ⚠️ `MCP6002` (dual RRIO) or `TL072` | Substitute; note single-vs-dual. DIP-8. |
| **IR2110** (gate driver) | ❌ NOT in shop | Course kit. DIP-14. Confirm pinout from datasheet. |
| **IL300** (linear opto) | ❌ NOT in shop, **no equivalent** | Course kit. DIP-8. Critical — the feedback servo needs *this* part. |
| **ILD74** (dual opto) | ❌ NOT in shop | Course kit, DIP-8. (4N25 is single-channel — not a drop-in.) |
| **Motor (Motraxx SR555)** | connector only | Use a 2-pin header / screw terminal footprint. |

Produce a **BOM mapping table** as an artifact (e.g. `hardware/kicad/bom/footprint_map.csv`
with columns: schematic_ref, value, chosen_part_number, source[shop/kit], footprint,
notes). This is a required deliverable — the team orders from it.

---

## 4. Footprints — assign them

### Prefer KiCad **stock** footprints (they cover almost everything here)
All these parts are standard THT packages that KiCad ships footprints for — you usually do
**not** need SnapEDA:
| Part type | KiCad stock footprint |
|---|---|
| Resistor 1/4 W axial | `Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal` |
| Ceramic cap (100n) | `Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm` |
| Electrolytic (22u/47u/470u) | `Capacitor_THT:CP_Radial_D6.3mm_P2.50mm` (size up for 470u) |
| Diode DO-41 (1N400x, 1N5817) | `Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal` |
| MOSFET TO-220 (IRF530/540, BUZ11) | `Package_TO_SOT_THT:TO-220-3_Vertical` |
| Op-amp DIP-8 (MCP601/6002) | `Package_DIP:DIP-8_W7.62mm` |
| Opto DIP-6 (4N25) | `Package_DIP:DIP-6_W7.62mm` |
| Opto/driver DIP-8 / DIP-14 (ILD74, IL300 / IR2110) | `Package_DIP:DIP-8_W7.62mm` / `Package_DIP:DIP-14_W7.62mm` |
| LED 5 mm | `LED_THT:LED_D5.0mm` |
| Motor / power in/out | `Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical` or a `TerminalBlock_*` |
| `PWR_FLAG`, power symbols (+15V/+5V/GND) | **no footprint** — schematic-only, exclude from board |

KiCad's stock footprint libs are under
`C:\Program Files\KiCad\9.0\share\kicad\footprints\*.pretty`. Browse them to pick exact
names; verify pad count/pitch against the datasheet.

### When to use SnapEDA / custom footprints → the `.pretty` folder
Use SnapEDA (https://www.snapeda.com) **only** for parts whose package is non-standard or
where you want an exact, vendor-verified footprint + 3D model — e.g. the **Motraxx motor
connector**, an unusual inductor, or if a datasheet shows a package KiCad doesn't ship.
- Download the **KiCad** footprint format (`.kicad_mod`) from SnapEDA.
- Drop it into `hardware/kicad/energy_system.pretty/` — it's already registered as lib
  `energy_system`, so it appears as `energy_system:<FootprintName>`.
- SnapEDA needs a free account/login to download; if you can't authenticate headlessly,
  **fetch what you can, and for anything blocked, list the exact part + SnapEDA URL** so
  the user can download it and drop it in. Alternative free sources: Ultra Librarian,
  ComponentSearchEngine, or cloning a community KiCad lib from GitLab/GitHub.
- A note tool `mcp__…__download_assets` may be available for asset fetching — check.

### How to write the footprint into the schematic
The `Footprint` property on each symbol carries the assignment. Three ways:
1. **Programmatic (preferred, matches the repo pattern):** edit the `.kicad_sch` with
   sexpdata — set the `(property "Footprint" "Lib:Name" …)` value per symbol. Mind that
   the schematic is the source of truth (don't regen from `build_*.py`).
2. **KiCad GUI:** Tools → *Assign Footprints* (CvPcb).
3. After assignment, run ERC and confirm no `footprint` errors.

---

## 5. The remaining schematics to generate

The system (per `docs/system-architecture.md` + the Kravspecifikation) needs more than the
4 built circuits. **Confirm exact scope against `Project Specifications.pdf`**, but the
remaining blocks are:

1. **3-phase rectifier → V1 bus** — generator (3φ) → **6-diode bridge** → filter cap →
   **V1 = 15 V** (Krav 1). Theory: Lec 4 (`V_dc = 1.654·V_m`). A Simscape model exists at
   `simulation/Three Phase Transformer/three_phase_rectifier.slx` for reference values.
2. **PV + MPPT front-end** — Sun Plus 10 panel → discrete **Perturb & Observe** MPPT →
   into the store (Krav: PV consumed first). Theory: Lecture 1 Modeling.
3. **Current sensing** — discrete, **op-amps allowed, no other ICs** (Krav) — for the
   control loops + monitoring. Likely shunt + op-amp difference amp per branch.
4. **(maybe) transformer interface + Arduino I/O / monitoring connector.**

Build these with the same sexpdata pattern (or KiCad GUI), real symbols, net-label
connectivity, 2.54 mm grid, then footprint them like the rest. **If scope is unclear, do a
deep read of the spec PDF and the architecture doc, list what you'll build, and proceed —
note assumptions.**

---

## 6. PCB layout — single-layer per board

**Be realistic about what's automatable** (set expectations honestly in your final report):

- **Footprint assignment:** fully automatable. ✅
- **Board creation + placement:** scriptable via KiCad's **`pcbnew` Python API** (use
  KiCad's bundled Python: `C:\Program Files\KiCad\9.0\bin\python.exe`). You can create the
  `.kicad_pcb`, import the netlist (`kicad-cli sch export netlist`), add footprints, place
  them, and set the board to **1 copper layer** (B.Cu) in board setup.
- **Routing:** KiCad 9 has **no built-in autorouter.** Single-layer THT routing is doable
  for these small circuits but often needs a few **jumper wires**. Options:
  - **Freerouting** (external Java app) via Specctra **DSN export → SES import**. It can
    target a single layer. Clone/download it if you want to attempt auto-routing.
  - **Manual** routing in the GUI (hand off a placed, ratsnest-ready board to the user).
- Per board: run **DRC**, then render with
  `kicad-cli pcb render` / `kicad-cli pcb export svg` for a preview.

**Recommended deliverable per board:** a `.kicad_pcb` with all footprints placed sensibly,
the board set to single (bottom) copper layer, ratsnest shown, an attempted route (Freerouting
if you get it working), DRC report, and a rendered image. If single-layer can't be fully
routed without jumpers, **say so per board** and show how far you got.

Make a tidy folder structure, e.g. `hardware/kicad/<board>/pcb/` per board, mirroring how
sim and design are already split.

---

## 7. Tooling & environment

- **KiCad 9.0.4** CLI: `C:\Program Files\KiCad\9.0\bin\kicad-cli.exe` (ERC, netlist, render,
  export). `pcbnew` Python module via the bundled `python.exe`. `ngspice.dll` bundled (no
  standalone exe).
- **Python:** `py -3.13` has `sexpdata` (+ PySpice if needed). Use sexpdata for `.kicad_sch`
  edits (the repo pattern).
- **Render a schematic:** `kicad-cli sch export pdf -o out.pdf file.kicad_sch`.
- **ERC:** `kicad-cli sch erc --output x.erc.txt file.kicad_sch`.
- You may **clone external repos** (KiCad libs, Freerouting) and **download footprints**.
- Shell is **PowerShell on Windows** (paths with spaces → quote them). Git Bash also works.

---

## 8. Rules & gotchas (do not violate)

- **NO AI attribution in commits.** No `Co-Authored-By`, no "Claude", no AI mention
  anywhere in commits/code/files. Commit messages read as if the developer wrote them.
  (Global rule — non-negotiable.)
- **This is the team repo** (`MadsRudolph/62768-energy-system`) — it tracks binaries
  (PDF/.slx/.kicad_*) directly, unlike the umbrella. Commit + push normally from inside
  `team/`. It is **gitignored from the umbrella** repo, so don't try to stage it there.
- **`.kicad_sch` = source of truth.** Build scripts have diverged — edit schematics directly.
- **Benign ERC warnings** you can ignore: `lib_symbol_mismatch` (from flattening `extends`
  symbols — clears with *Tools → Update Symbols from Library*), `power_pin_not_driven`
  (add `PWR_FLAG`s), single-pin external `global_label_dangling`.
- **Danish** is fine for component comments / lib descriptions (matches the repo); English
  fine for docs. Keep it consistent with surrounding files.
- Verify every footprint's pad count + pitch against the **datasheet** — a DIP-8 vs DIP-14
  mistake or a TO-220 pinout swap ruins the board.

---

## 9. Definition of done

- [ ] Remaining system schematics generated (rectifier, MPPT, current sense — scope
      confirmed against the spec), ERC-clean, net-label connectivity, real symbols.
- [ ] Every component in **every real schematic** has a valid footprint (stock or
      `energy_system:*`), ERC shows no footprint errors.
- [ ] `hardware/kicad/bom/footprint_map.csv` — schematic ref → chosen part (shop/kit) →
      footprint → notes, with all substitutions flagged.
- [ ] Custom footprints (if any) downloaded into `energy_system.pretty/`; anything that
      needed SnapEDA-login-but-couldn't-fetch is listed with its URL for the user.
- [ ] A `.kicad_pcb` per board: footprints placed, single (bottom) copper layer, DRC run,
      rendered preview. Routing attempted; per-board honesty about what's fully routed
      single-layer vs. needs jumpers/manual finish.
- [ ] A short `PCB_RESULTS.md` summarising per board: parts, substitutions, footprint
      sources, routing status, and what the user must still do.
- [ ] Committed + pushed to the team repo (clean, developer-style messages).

Work methodically, board by board. Research deeply, verify against datasheets, and flag
every assumption. Good luck.
