# KiCad — 62768 Electrical Energy System (KiCad 9)

Alle 7 system-boards, produktionsfiler til XTool-fiberlaseren og hele
genererings-pipelinen. **Status og produktionsplan: se `../../PCB_RESULTS.md`
og `production/README.md`.**

## Mappestruktur

| Mappe | Indhold |
|---|---|
| **`boards/<navn>/`** | Ét KiCad-projekt pr. board — **åbn `.kicad_pro`-filen** (skema + PCB linket). `pcb/`-undermappen har DRC-rapport + top/bund-renders. `README-exp3a.md` / `README-system.md` er design-noterne. |
| **`production/<navn>/`** | **Laserfiler**: `<navn>.dxf` (importeres i xTool), `_silk_top.dxf` (valgfri topside-tekst), `gerbers/` (komplet fab-sæt). Køreplan i `production/README.md`. |
| `bom/` | `footprint_map.csv` — ref → indkøbsdel (shop/kit) → footprint → noter. Bestil efter den. |
| `lib/` | Projekt-bibliotek: `energy_system.pretty/` (bl.a. `*_LaserPads`-footprints), `energy_system.kicad_sym`, scaffold-projektet. Hvert board har sin egen `fp-lib-table` der peger herhen. |
| `tools/` | Pipeline: `pcb_make_all.ps1` (netliste → placering → Freerouting → DRC → render), `pcb_export_production.ps1` (DXF + Gerbers), hjælpescripts. `tools/generators/` genskaber skemaerne. `retrofit_pcb.py` er historisk (engangs-rettelser, gamle stier). |
| `simulation/` | ngspice/behavioral-simuleringerne: `converters/` (buck/boost + modeller) og `exp3a/` (drive/feedback). Egne README'er. |

## Boards

`buck` · `boost` · `drive_circuit` · `feedback_circuit` · `rectifier` · `mppt` · `current_sense`

Designregler (fiberlaser-guiden): bane 1.0 mm, clearance 0.8 mm — ligger i hvert
boards `.kicad_pro`, så GUI-routing automatisk overholder dem. Komponentnavne er
graveret som kobber-tekst på B.Cu.

## Genbyg / eksportér (køres fra denne mappe)

```powershell
.\tools\pcb_make_all.ps1 -Jar <sti>\freerouting-2.0.1.jar [-Boards buck,mppt]
.\tools\pcb_export_production.ps1
```

Kræver KiCad 9, `py -3.13` med sexpdata, Java 21 + freerouting-2.0.1.jar
(https://github.com/freerouting/freerouting/releases/tag/v2.0.1).
NB: KiCad-stable popper en harmløs debug-assert-dialog under DSN-eksport — klik **No**.
