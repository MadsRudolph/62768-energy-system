# HANDOFF — complete double-sided PCB for the whole system

**For:** a fresh Claude Code session.
**Goal the user gave:** *"make a complete double-sided PCB for the whole system."*
**Your job:** figure out *how* we do this and drive it, starting from the decisions below.

> ### ✅ Route DECIDED by the user (2026-06-27): in-house **SRM-20 CNC mill, double-sided**.
> **Not** an external fab. The hard constraints that follow from this:
> - **Clearance 0.9–1.0 mm** — the isolation end mill is **0.8 mm**, so every copper-to-copper
>   gap must be ≥ 0.8 mm for the bit to physically fit; target **0.9–1.0 mm**. Track ≥ **1.0 mm**.
> - **Max board 203.2 × 152.4 mm** (× 60.5 mm Z) — the SRM-20 work area. No more 104×104 laser
>   jig. A whole-system board fits comfortably.
> - **No plated vias** — double-sided on a mill means **hand-stitched vias** (rivets or soldered
>   wire through-holes, soldered top *and* bottom) + a **two-sided registration/flip** scheme.
>   This is the central hard part — see the new "Double-sided on the mill" section.
> - Output = **mill toolpaths (RML/NC via the `srm-cam` / gerber2rml flow)**, not laser DXF, not
>   fab Gerbers.
>
> So Phase 0 below is mostly answered. The **remaining** Phase-0 items (board set, monolithic vs
> modular, MCU target, KiCad version, off-board connectors) still need the user.

---

## TL;DR of the situation

Everything built so far is **single-sided** for the in-house fiber-laser / SRM-20 mill:
copper on **B.Cu** as the main etch, **F.Cu used only for unavoidable crossings** (wire
bridges), design rules **track 1.0 mm / clearance 0.8 mm**, board **fixed at 104×104 mm**
(laser jig), **no plated vias**, output = **DXF/RML**. There are **11 separate boards**
(rectifier, buck/buck_v2, boost/boost_v2, mppt/mppt_buck, drive_circuit/motor_power,
feedback_circuit/motor_feedback/c2000_feedback, current_sense).

The new ask is **one integrated, genuinely double-sided board** (both copper layers carrying
signal, **hand-stitched** through-hole vias, ground pours) — milled in-house on the **SRM-20**
(decided, see the box above). Relative to the single-sided laser flow, what changes is: board
size (up to 203.2×152.4 mm), clearance (0.9–1.0 mm for the 0.8 mm bit), **both layers now route**
(no more F.Cu-as-wire-bridges masking), vias become a manual stitching step, and output is the
mill RML/NC flow. The schematic/footprint/ERC front-end is unchanged.

Read these before doing anything: this file → [`WORKFLOW.md`](WORKFLOW.md) (the single-sided
pipeline + every gotcha) → [`../../PCB_RESULTS.md`](../../PCB_RESULTS.md) (per-board status,
substitutions, electrical notes) → the hierarchical-system design contract
[`../../docs/superpowers/specs/2026-06-21-system-hierarchical-schematic-design.md`](../../docs/superpowers/specs/2026-06-21-system-hierarchical-schematic-design.md)
(the inter-board **net interface contract** — this is your integration map).

---

## Phase 0 — decisions to force with the user FIRST (gating)

These are not yours to assume. Ask, get answers, record them in this file before Phase 1.

1. ~~**Manufacturing route.**~~ **RESOLVED → in-house SRM-20 CNC, double-sided** (see box at
   top). Clearance 0.9–1.0 mm (0.8 mm bit), track ≥1.0 mm, max board 203.2×152.4 mm, hand-
   stitched vias, RML/NC output. Skip to #2.

2. **Board set / which variants.** The repo has older *and* v2 boards. Lock the canonical set.
   The hierarchical spec already locked one (motor_power, motor_feedback, mppt, boost_v2,
   current_sense) but the converter story has since moved to the **IR2110 v2 / switching**
   variants (`buck_v2`, `boost_v2`, `mppt_buck`) — see `PCB_RESULTS.md`. Decide explicitly:
   which buck, which boost, which MPPT (linear `mppt` vs switching `mppt_buck`), motor side
   (`drive_circuit` vs the `motor_power`+`motor_feedback` split), sensing (`current_sense`
   5 V vs `c2000_feedback` 3.3 V), and **MCU target (Arduino vs TI C2000)** — they scale
   feedback differently (5 V vs 3.3 V), so this picks the feedback board.

3. **Topology of the deliverable.** One **monolithic** board with everything, or a
   **motherboard + module headers** (mezzanine/backplane) so the existing modules plug in?
   "Complete double-sided PCB for the whole system" reads as monolithic; confirm.

4. **What stays off-board** (connectors): DC motor, 3-phase generator, transformer, PV panel,
   pulsing load, Arduino/C2000, bench/drive supplies. List them — they become the board's edge
   connectors.

5. **KiCad version.** Pick ONE. Per the repo memory, the **v2 boards are KiCad 10 format** and
   the older boards are KiCad 9. Mixing versions when merging sheets will bite you. (See
   `project-freerouting-java-kicad` memory: GUI Freerouting needs Java 25; CLI jar 1.9.0 needs
   Java 17+; route v2/KiCad-10 boards via the KiCad 10 python.)

---

## Why the existing toolchain only half-applies

`WORKFLOW.md` is gold for schematic generation, footprint rules, placement, and the gotchas —
**reuse all of that**. But several steps are **single-sided-laser-specific and must be DROPPED
or changed** for a fabricated double-sided board:

| Single-sided laser step (drop/change) | Double-sided **CNC** equivalent |
|---|---|
| 104×104 mm jig clamp (`JIG_W/JIG_H` in `pcb_build.py`) | Size to content, **up to 203.2 × 152.4 mm** (SRM-20 work area). Leave clamp margin. |
| Rules 1.0 mm track / **0.8 mm** clearance | Track **≥1.0 mm**, clearance **0.9–1.0 mm** (0.8 mm bit must fit the gap — do **not** go below 0.8) |
| Two-stage Freerouting (mask F.Cu as `power` to force B.Cu-only) | **Both layers live + vias enabled** — route normally (KiCad router or Freerouting with vias). The masking trick exists *only* to avoid the top layer; you now *want* both. |
| `energy_system:*_LaserPads` / DIP `LongPads` (1.7 mm pads for 0.8 mm air) | Pads must still respect the **0.9–1.0 mm** copper gap — the laser pad shrink logic mostly carries over; **re-check every footprint's pad-to-pad gap at the new clearance**. THT only. |
| Solid no-net **laser zones** + **refdes-as-copper** | Real **GND/PWR pours** (netted) on both layers; refdes engraving optional (mill can engrave silk, or skip) |
| `<board>.dxf` for xTool | **Mill toolpaths** via the `srm-cam` / gerber2rml flow → `.rml`/`.nc` for VPanel |

So: **front-end (schematic + footprints + ERC) reuses the pipeline unchanged; back-end (rules,
routing, vias, production export) is the double-sided mill flow below.** The `kicad-laser-pcb`
skill is laser-specific — lean on it for footprints/placement intuition, not routing/output.

---

## Double-sided ON THE MILL — the central hard part

A milled double-sided board has **no plated through-holes**, so top↔bottom connections and
two-sided registration are manual. This is where the real risk lives — design for it from the start.

- **Vias = hand-stitched.** Every via is a physical thing you make: drill the hole, insert a
  **via rivet** (preferred) or a snug wire, and **solder both sides**. Give each one a **pad on
  BOTH layers** large enough to solder — a real THT via footprint / annular ring, not a bare drill.
- **GND vias are ALLOWED** (user, 2026-06-27) — so the cheap, robust strategy is a **ground pour
  on both layers stitched together with GND vias** as freely as you like. That gives a solid
  return path and turns most layer-changes into ground stitching rather than signal vias.
- **Minimise *signal* vias specifically.** Ground is free; a *signal* crossing between layers is
  the expensive case (a deliberate hand-stitched joint). Route so signals stay mostly on one
  layer, ground fills both, and signal layer-changes are few and intentional.
  - **Component leads double as vias:** a THT part's leads are soldered both sides anyway, so
    routing a signal to the *same pad* on both layers is a "free" layer change. Exploit this.
- **Two-sided registration (flip).** The mill must cut the top side aligned to the bottom side.
  Standard approach: **two tooling/alignment holes** drilled through the blank; flip about a
  fixed edge/axis and re-locate on those holes. Decide the flip axis and mirror the top toolpath
  accordingly (gerber2rml / VPanel origin handling). **Mirror exactly one side** — getting the
  flip/mirror wrong is the classic double-sided failure (top traces land mirrored).
- **Output flow:** Gerbers (F.Cu, B.Cu, Edge.Cuts, drill) → `srm-cam` / gerber2rml → `.rml`/`.nc`
  → VPanel. The repo already has a **single double-sided-ish mill board to copy from**
  (`boards/boost/boost_v2_mill/`, production in `production/boost_v2_mill/{nc,rml}`) and the
  `drive_circuit` mill outputs (`production/drive_circuit/{nc,rml}`). The `tools/srm-cam`
  submodule is the CAM tool. The **upstream double-sided milling/alignment procedure** is the
  clone at `..\DTU-PCB-prototyping` — read its double-sided section before designing the flip.
- **Operating the mill:** see the `project-srm20-vpanel-bringup` memory — USB001, the VPanel
  garbage-coords/dead-buttons = no-handshake fix (power-cycle then relaunch), and the
  gerber2rml launch paths. Mads drives VPanel; you prep the toolpaths.

## The integration map you already have

The hierarchical-system spec defines the **net interface contract** between boards — i.e.
exactly which nets must tie together when you merge them onto one PCB (V1, GND, +5V_PWR,
STORE, +15V_GATE, PWM_MOTOR, PWM_BOOST, PV_V/PV_I, MCU_V1, I_SENSE1..3, etc.). The cleanest
build path:

1. Each chosen board's `.kicad_sch` becomes a **hierarchical sheet** in
   `hardware/kicad/system/system.kicad_sch` (currently an empty stub).
   [`system/HIERARCHICAL_LABELS_HOWTO.md`](system/HIERARCHICAL_LABELS_HOWTO.md) is the
   hand-procedure (Phase-1 label placement is a human-in-KiCad job); Phases 2–3 (top sheet +
   ERC) are scriptable.
2. **"Update PCB from Schematic" on the top sheet pulls every sheet's components into ONE
   `.kicad_pcb`** — that is your single integrated double-sided board. (KiCad multi-sheet → one
   board is exactly this; the hierarchical schematic isn't just for docs.)
3. Place by subsystem/signal-flow, pour grounds both layers, route 2-layer with vias, DRC,
   export fab package.

Alternative if hierarchy fights you: a **flat merge** of all subsystem netlists into one board
via the existing `pcb_build.py` JSON path (strip the jig/laser-zone/refdes-copper bits first).
Hierarchical is cleaner and reuses the contract; flat is more familiar to the existing tooling.

---

## Carry-over gotchas (still true on a double-sided board)

- **Schematic `.kicad_sch` is source of truth** — never regenerate GUI-edited boards
  (buck, boost, drive_circuit, feedback_circuit) from old build scripts.
- **Pin-letter trap:** `Device:Q_NMOS` G/D/S vs TO-220 pads 1/2/3 — no-net pads don't show as
  "unconnected" in DRC. `pcb_build.py` maps and fail-hard checks this; preserve it.
- **Open the `.kicad_pro`, not the bare `.kicad_pcb`**, or the GUI routes with default clearance
  (netclass lives in the project file). Put the **new fab netclass** in the project file.
- **PWR_FLAG** on connector-fed supply nets or ERC throws `power_pin_not_driven`.
- **Power/thermal for a real board:** motor branch ~1.5 A, generator/rectifier currents, MOSFET
  dissipation (MPPT linear pass ~7 W if that variant is kept — prefer the switching `mppt_buck`),
  higher-voltage rails (rectifier ~26 V) need adequate trace width + creepage. Double-sided lets
  you use ground pours and wide power traces — use them.
- **Electrical notes in `PCB_RESULTS.md`** (high-side gate drive references, feedback isolation,
  substitutions in `bom/footprint_map.csv`) all still apply — read them before merging.

---

## Suggested phase plan (after Phase 0 is answered)

1. **Phase 1 — rules + board set.** Create the **CNC netclass** in the project file: track
   ≥1.0 mm, **clearance 0.9–1.0 mm**, via pad sized for hand-stitching. Set max board envelope
   203.2 × 152.4 mm. Lock the canonical board set + KiCad version from Phase 0.
2. **Phase 2 — integrated schematic.** Build the connected hierarchy in `system/` (or flat
   merge). ERC 0 errors across sheets. Confirm the interface contract nets all tie up.
3. **Phase 3 — one PCB.** Update-PCB-from-schematic → single board. Place by signal flow,
   isolate the noisy power stage from the analog sensing. **GND pour on BOTH layers, stitched
   with GND vias (allowed) freely;** keep signals mostly on one layer so *signal* vias stay few
   and deliberate. Route 2-layer, add the two tooling/alignment holes for the flip. DRC 0 errors
   / 0 unrouted at the 0.9–1.0 mm clearance.
4. **Phase 4 — mill toolpaths.** Gerbers (F.Cu, B.Cu, Edge.Cuts) + drill → `srm-cam`/gerber2rml
   → `.rml`/`.nc`, **top side mirrored about the chosen flip axis**, via/drill file included.
   Copy the `boost_v2_mill` production layout. Drop into `production/system/{nc,rml}`. Update
   `PCB_RESULTS.md` + `production/README.md` (cut size, flip procedure, via-stitch list).

## Key files & pointers

| What | Where |
|---|---|
| Single-sided pipeline + gotchas | [`WORKFLOW.md`](WORKFLOW.md) |
| Per-board status, subs, el-notes | [`../../PCB_RESULTS.md`](../../PCB_RESULTS.md) |
| Net interface contract (integration map) | [`../../docs/superpowers/specs/2026-06-21-system-hierarchical-schematic-design.md`](../../docs/superpowers/specs/2026-06-21-system-hierarchical-schematic-design.md) |
| Hand-procedure for hierarchical labels | [`system/HIERARCHICAL_LABELS_HOWTO.md`](system/HIERARCHICAL_LABELS_HOWTO.md) |
| System top-sheet stub (empty) | `system/system.kicad_sch` |
| Board projects | `boards/<name>/<name>.kicad_pro` |
| BOM / footprints / substitutions | `bom/footprint_map.csv` |
| System architecture (read before wiring blocks) | `../../docs/system-architecture.md` |
| Generators / placement / routing scripts | `tools/` (see WORKFLOW §1–4) |
| Component shop CSV | `C:\Users\Mads2\Downloads\Documents\dtu_component_shop.csv` |
| Laser process clone (in-house route only) | `..\DTU-PCB-prototyping` |

## Decisions log

- Manufacturing route: **DECIDED 2026-06-27 — in-house SRM-20 CNC, double-sided.**
- Design rules: **DECIDED — track ≥1.0 mm, clearance 0.9–1.0 mm (0.8 mm end mill), hand-stitched vias.**
- Board envelope: **DECIDED — max 203.2 × 152.4 × 60.5 mm (SRM-20 work area).**
- Canonical board set + converter variants: **DECIDED 2026-06-27 — 6 sheets:**
  `motor_power` (rect + V1 buck + motor drive), `motor_feedback` (V1 sense, 5 V→Arduino),
  `boost_v2`, `mppt_buck` (switching MPPT), `current_sense` (3× low-side, 5 V→Arduino),
  `c2000_feedback` (V1/V2/V3 dividers + PWM, 3.3 V→C2000). Old `buck`/`boost`/`mppt`(linear)/
  `drive_circuit`/`feedback_circuit`/`rectifier` standalone boards are NOT used (motor_power
  integrates rect+buck+drive per the 2026-06-21 hierarchical spec).
- Monolithic vs motherboard+modules: **DECIDED — monolithic single double-sided board.**
- MCU target → feedback board: **DECIDED — SPLIT MCU.**
  - **Arduino Nano (5 V), on-board socketed:** current sensing only (`current_sense`, 3× shunt
    ×10) + V1 monitoring (`motor_feedback` MCU_V1, IL300-isolated). + PV_V/PV_I.
  - **TI C2000 LaunchPad (3.3 V), off-board headers:** ALL PID. Reads V1/V2/V3 via
    `c2000_feedback` dividers; emits **3× PWM** (motor buck + boost + mppt_buck) through
    level-shifted opto passes.
  - **Implied reworks (Phase 2, both script-generated → editable):** `c2000_feedback` must
    expand its single PWM pass to **three** and **remove** its I1/I2/I3 current channels
    (currents come from `current_sense`→Arduino only).
  - **Interface contract update:** the 2026-06-21 contract's single "Arduino hub" is superseded
    — top sheet needs a **second MCU connector** (C2000 hub: V1/V2/V3 sense + 3× PWM out).
- KiCad version: **DECIDED — KiCad 10.** `motor_power`/`buck_v2` are already `20260206` (KiCad 10)
  format which KiCad 9 can't open; KiCad 10 reads the `20241229` boards fine.
- Off-board connectors: **DECIDED — screw terminals on board edge:** 3-phase AC in (transformer
  secondary U/V/W → rectifier), DC motor (MOTOR_A/B), PV panel (PV_PLUS/PV_RET), 1 F supercap
  store (STORE/GND), pulsing load (LOAD), +15 V gate-drive bench supply, +5 V logic supply.
  MCUs: **Arduino Nano on-board socket; C2000 LaunchPad off-board via header.**
- Diagnostic probe points: **DECIDED 2026-06-27 — add labelled 1-pin header test points** on
  key nets, grouped into labelled rows near the edge (reachable with Arduino socketed + C2000
  off-board). Coverage: rails (V1/STORE/LOAD/+5V/+3V3/+15V_GATE + per-domain GND), switch nodes
  (motor-buck/boost/mppt SW), PWM chain probed **both** MCU-side and post-opto gate
  (PWM_MOTOR/BOOST/MPPT), feedback (V1/V2/V3 sense, I_SENSE1/2/3, PV_V, PV_I, MCU_V1). One GND
  TP per ground domain (power GND vs GND_MCU) for correct single-ended scope reference.
