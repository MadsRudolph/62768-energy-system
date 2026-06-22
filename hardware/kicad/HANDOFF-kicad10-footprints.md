# Handoff: verify KiCad-10 footprints on a fresh PC

**For the Claude Code session on the *other* PC** (KiCad 10 freshly installed). Goal:
confirm we do **not** hit the footprint-not-found problem we fixed on the first PC.

## TL;DR — run this first

```powershell
cd "<repo root>"          # the 62768 team repo
git pull
py -3.13 hardware/kicad/tools/verify_footprints.py
```

Expect the last line to read **`13 boards checked, 0 with problems.`** If so, footprints
are fine on this PC — nothing else to do. The tool is pure Python stdlib (no KiCad/pcbnew
needed), so it runs before you touch the GUI.

If any board prints `[FAIL]`, jump to **"If verify fails"** below.

---

## What went wrong on PC1 (context)

Updating KiCad 9 → 10 broke footprint resolution on the first PC:

1. **KiCad 10 dropped the stock `TerminalBlock` bornier footprints** (the screw
   terminals — `TerminalBlock_bornier-2/3/4_P5.08mm`). Boards referencing
   `TerminalBlock:...` couldn't find them.
2. **TO-220 pad-name split.** `Device:Q_NMOS` MOSFETs have letter pins (G/D/S) while the
   stock TO-220 footprint has numeric pads (1/2/3) — pads ended up with **no net**
   (silent: DRC stays clean!). Regulators (numeric pins) need the plain footprint.
3. The file format also changed (`20260306`) — **KiCad 9's CLI cannot read KiCad-10
   boards**; you must use the 10.0 CLI.

### How it was fixed (all committed to this repo)

- Vendored the missing libs into the repo: `hardware/kicad/lib/`
  - `TerminalBlock.pretty/` — the three bornier footprints
  - `energy_system.pretty/` — laser footprints incl. a `TO-220-3_Vertical_LaserPads_GDS`
    variant (pads renamed G/D/S) for the MOSFETs
- Registered both libs in **every board's own `fp-lib-table`** using **portable**
  `${KIPRJMOD}/.../lib/*.pretty` paths (relative to each project, so they resolve on any
  PC after `git pull` — no dependence on a machine-specific *global* footprint table).

**Because those fixes are committed, a `git pull` on this PC should already make everything
resolve.** The verify script just proves it.

> Why a *project* table matters: on PC1, three boards happened to work only because PC1's
> **global** KiCad table had the libs registered. That is per-machine and does **not**
> travel with git — so they'd fail here. They've now been given their own project
> `fp-lib-table` (boost_v2, c2000_feedback, mppt_buck), committed. The verify script is
> exactly the check that would have caught this.

---

## If verify fails

Run the fixer, then re-verify:

```powershell
py -3.13 hardware/kicad/tools/fix_fplib.py        # creates/patches project fp-lib-tables
py -3.13 hardware/kicad/tools/verify_footprints.py
```

`fix_fplib.py` is idempotent: for every board project that uses `energy_system:` /
`TerminalBlock:` footprints, it ensures the lib is registered in that board's own
`fp-lib-table` with the correct relative depth. It never touches `CompleteMotorCircuit`
(a teammate's project).

If verify still fails after that, the **repo lib itself** is missing a footprint file —
check `hardware/kicad/lib/TerminalBlock.pretty/` and `hardware/kicad/lib/energy_system.pretty/`
exist and contain the named `.kicad_mod`. If they don't, the `git pull` was incomplete.

Then commit the regenerated tables:
```powershell
git add hardware/kicad/boards/**/fp-lib-table
git commit -m "fp-lib-table: register repo footprint libs for <board>"
```

---

## Environment notes for this PC (KiCad 10)

- **Use the KiCad 10 CLI**, not 9: `C:\Program Files\KiCad\10.0\bin\kicad-cli.exe`
  (and `...\10.0\bin\python.exe` for pcbnew scripts). The 9.0 CLI errors on these boards.
- The **kicad-laser-pcb skill defaults to the 9.0 path** — when routing/exporting, pass
  `-KicadBin "C:\Program Files\KiCad\10.0\bin"` to `route_board.ps1` /
  `export_production.ps1`.
- When building/routing via the skill's `pcb_build.py`, set
  `KICAD_LASER_EXTRA_LIBS` to `…\hardware\kicad\lib` so it finds the repo libs
  (`TerminalBlock`, the `_GDS` variant). (This is a skill-side setting; the repo's own
  `tools/pcb_route.py` is already current.)

## The footprint-not-found trap (so you recognise it)

Opening a *routed* `.kicad_pcb` will **not** error even if a lib is missing — the board
stores its footprint geometry inline. The problem only surfaces when KiCad re-reads the
library: **Update PCB from Schematic**, the footprint chooser/editor, or running the build
pipeline (`pcb_build.py`'s `FootprintLoad`). That's why `verify_footprints.py` checks the
schematic's footprint *references* against the libs, rather than just opening the board.

## Other KiCad-10 fixes already in the repo (FYI, no action needed)

- Reference designators now go on **F.SilkS (silkscreen)**, never etched as copper on
  F.Cu. (`tools/pcb_route.py`, `add_refdes_silk`.)
- The finish step's zone cleanup was made KiCad-10-safe (materialise removal lists before
  `board.Remove()` — KiCad's SWIG iterators invalidate on mutation, yielding
  `SwigPyObject` without `GetNetCode`).

---

## One-line summary to give the PC2 session

> "Pull the repo, run `py -3.13 hardware/kicad/tools/verify_footprints.py`; if it says
> `0 with problems` the KiCad-10 footprint migration is fine on this PC. If not, run
> `tools/fix_fplib.py` and re-verify."
