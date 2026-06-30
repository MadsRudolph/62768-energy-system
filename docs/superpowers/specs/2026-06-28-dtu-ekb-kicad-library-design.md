# DTU-EKB KiCad library — contribution + global setup

**Date:** 2026-06-28
**Target repo:** `github.com/DTU-EKB/KiCad-components` (separate from the 62768 team repo)
**Target KiCad version:** 10.0 (the version Mads uses for all projects)

## Goal

Two outcomes:

1. **Setup** — the DTU-EKB component library is available in *every* KiCad 10 project
   on this PC, as a live git checkout (edits are instantly usable and staged for PR).
2. **Contribute** — populate the currently-empty `dtu-ballerup-componentshop.kicad_sym`
   with a curated set of the ~18 named parts the 62768 boards actually use, each carrying
   a verified footprint, datasheet link, and shop-location field.

## Current state (verified)

- The released PCM package (`v0.2`) is an **empty shell**: empty symbol libs, empty
  `.pretty` folders, empty `.3dshapes`. `repository.json` / `packages.json` are valid and
  `v0.2` downloads + checksums correctly; `v0.1`'s download URL is broken (404).
- The library is **not installed/registered** in any KiCad version on this PC (8.0 / 9.0 / 10.0).
- The repo's existing symbol stubs are KiCad-10 format (`version 20251024`, generator 10.0),
  authored by a teammate on KiCad 10.
- Authoritative parts list: `Downloads/Misc/dtu_component_shop.csv` (1464 rows).
- Authoritative footprint mapping (already verified per board):
  `team/hardware/kicad/bom/footprint_map.csv`.

## Part A — Live global setup (KiCad 10)

1. Clone `DTU-EKB/KiCad-components` to `C:\Users\Mads2\KiCad\DTU-EKB-components`
   — deliberately **outside** `C:\Users\Mads2\DTU` (the umbrella git repo) to avoid the
   nested-repo `git add` failures documented in the umbrella CLAUDE.md.
2. Add KiCad path variable `DTU_EKB_DIR` → that path, in
   `%APPDATA%\kicad\10.0\kicad_common.json` (`environment.vars`).
3. Register in the KiCad 10 **global** tables (back up first; KiCad must be closed —
   it rewrites these files on exit):
   - `%APPDATA%\kicad\10.0\sym-lib-table`: `dtu-ballerup-componentshop` and
     `ekb-component-stock` → `${DTU_EKB_DIR}/Components/symbols/*.kicad_sym`
   - `%APPDATA%\kicad\10.0\fp-lib-table`: the two `.pretty` dirs (registered now so they're
     ready even though empty in v1).
4. Verify: open KiCad 10 symbol chooser in any project → the `dtu-ballerup-componentshop`
   library is listed with the new parts.

Because the table points at the live checkout, editing a symbol updates every project and
leaves the change staged in git for commit/PR. No PCM round-trip for the contributor.

## Part B — Curated starter set (~18 named parts)

Populate `Components/symbols/dtu-ballerup-componentshop.kicad_sym`. Each catalog symbol
carries: `Value` = part number, `Footprint` = stock KiCad footprint, `Datasheet` = URL,
custom field `Shop_Location` (CSM / kit), and a description.

| Part | Type | Footprint (stock KiCad) | Source |
|---|---|---|---|
| 1N4148 | signal diode | Diode_THT:D_DO-35_SOD27_P7.62mm_Horizontal | shop |
| 1N4006 | rectifier diode 800V | Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal | shop |
| 1N5817 | Schottky 1A/20V | Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal | shop |
| 1N5822 | Schottky 3A/40V | Diode_THT:D_DO-201AD_P15.24mm_Horizontal | order |
| BZX55C5V1 | zener 5.1V | Diode_THT:D_DO-35_SOD27_P7.62mm_Horizontal | shop |
| BZX55C3V0 | zener 3.0V | Diode_THT:D_DO-35_SOD27_P7.62mm_Horizontal | shop |
| IRF530 | N-MOSFET 100V | Package_TO_SOT_THT:TO-220-3_Vertical | shop |
| IRF540 | N-MOSFET 100V | Package_TO_SOT_THT:TO-220-3_Vertical | shop |
| TIP41A | NPN 6A | Package_TO_SOT_THT:TO-220-3_Vertical | shop |
| LM358 | dual op-amp | Package_DIP:DIP-8_W7.62mm_LongPads | shop |
| MCP601 | op-amp | Package_DIP:DIP-8_W7.62mm_LongPads | kit |
| NE555 | timer | Package_DIP:DIP-8_W7.62mm_LongPads | shop |
| LM7805 | 5V LDO/regulator | Package_TO_SOT_THT:TO-220-3_Vertical | shop |
| 4N25 | optocoupler | Package_DIP:DIP-6_W7.62mm_LongPads | shop |
| CNY17 | optocoupler | Package_DIP:DIP-6_W7.62mm_LongPads | shop |
| IR2110 | gate driver | Package_DIP:DIP-14_W7.62mm_LongPads | kit |
| ILD74 | dual optocoupler | Package_DIP:DIP-8_W7.62mm_LongPads | kit |
| IL300 | linear optocoupler | Package_DIP:DIP-8_W7.62mm_LongPads | kit |

Decisions:
- **All footprints are stock KiCad libs** (taken from the verified BOM). **No custom
  footprints in v1.** The laser-pad `energy_system` footprints stay in the team repo — this
  shared catalog stays laser-process-agnostic.
- **Authoring method:** copy base symbols (D, D_Zener, D_Schottky, Q_NMOS, Q_NPN) and the
  IC symbols (LM358, NE555, MCP601, regulator, 4N25, IR2110…) from KiCad 10's stock symbol
  libs via `sexpdata`; add part-number variants from a small curated CSV
  (`Components/parts/dtu-shop-parts.csv`) so the build is reproducible and reviewable.
  - Gotcha: derived (`extends`) symbols must live in the *same* `.kicad_sym` file as their
    base, so each needed base symbol is copied in first. Stock IC symbols that are themselves
    derived (e.g. an op-amp that extends another) require copying their parent too.
- **Passives are NOT individual symbols** — 800+ resistor/cap value rows would be noise.
  Instead add `Components/CONVENTION.md`: "use Device:R / Device:C / Device:L; we stock E96
  + these THT footprints." Revisit later if wanted.
- **Full shop inventory CSV** — add the complete `dtu_component_shop.csv` (1464 rows) to the
  repo at `Components/parts/dtu_component_shop.csv` as the authoritative stock list, and link
  it from the README's "components in the component shop" section. This is the source the
  curated symbols are drawn from, and lets future contributors see the whole catalog.
- **Format:** KiCad 10 (matches existing repo stubs + teammate tooling).

## Part C — Deliver to PCM classmates (optional, flagged not auto-done)

PCM-installed classmates won't receive any of this until a new release is cut. Follow-up:
- Fix the broken `v0.1` `download_url` in `packages.json`.
- Cut `v0.3`: rebuild the package zip, compute sha256/sizes via the repo's
  `releases/pcm-info.sh`, update `packages.json`, create the GitHub release with the asset.
- Caveat to record in the release notes: symbols are KiCad-10 format; KiCad-9 classmates may
  need to upgrade. (Pre-existing repo decision.)

## Out of scope for v1

Bulk CSV import of all 1464 parts; the EKB stock library; 3D models; custom footprints.

## Delivery

- Commit the new symbols + curated CSV + CONVENTION.md to a branch on `DTU-EKB/KiCad-components`,
  open a PR. (Commits only when Mads asks — per umbrella CLAUDE.md.)
- Local KiCad 10 config edits (lib tables, `kicad_common.json`) are PC-local, not committed.
