# Routing & production (two-stage Freerouting)

## Why two stages

The boards are built single-sided: the etched side is **B.Cu**, and only the crossings
that are physically impossible single-sided go on **F.Cu** (built as wire bridges, or a
second etch). So stage 1 routes everything it can on the bottom, locks it, then stage 2
lets Freerouting put just the leftovers on top.

## Two hard-won tool facts (these caused hours of "it hangs")

1. **Use Freerouting 1.9.0, not 2.0.1.** 2.0.1's version-check phones home and throws a
   `NullPointerException` (`gson.JsonObject.get` returns null) that takes the
   job-completion chain with it — routing finishes but the SES is never written, so the
   job looks hung forever. 1.9.0 routes purely locally on Java 21, same DSN/SES formats.
   Jar: `%USERPROFILE%\.freerouting\freerouting-1.9.0.jar`.
2. **Write DSN files BOM-free.** Windows PowerShell 5.1's `Set-Content -Encoding utf8`
   prepends a UTF-8 BOM, and Freerouting's DSN parser chokes on it ("file not found" /
   "Non-ansi character at position 0"). Write with `[System.IO.File]::WriteAllText(...)`
   instead. (Same bug bites KiCad lib-tables — see `gotchas.md`.) `pcb_make_all.ps1`
   already does this; replicate it in any hand-written routing script.

## The standard path

For boards matching `boards/<name>/<name>.*`, `pcb_make_all.ps1` does everything. Launch
the assert-dialog dismisser first (`gotchas.md`), then:

```powershell
.\tools\pcb_make_all.ps1 -Boards <name>
```

## Routing a board in a non-standard location, or re-routing a hand-placed board

Boards like `boards/buck/buck_v2/` don't fit the `<name>/<name>` pattern, and sometimes
you want to route a GUI-placed board *without* re-placing it. Drive the steps explicitly.
For a hand-placed board, **strip old routing first** (textually — in-process
`pcbnew` zone removal access-violates):

```powershell
py -3.13 tools\strip_routing.py <board>.kicad_pcb   # removes tracks/vias/zones/copper-text
```

Then the two-stage route (adapt paths; this is the shape of `make_buck_v2.ps1`):

```powershell
$kpy = "C:\Program Files\KiCad\9.0\bin\python.exe"
$kc  = "C:\Program Files\KiCad\9.0\bin\kicad-cli.exe"
$jar = "$env:USERPROFILE\.freerouting\freerouting-1.9.0.jar"
$pcb = "boards\<path>\<b>.kicad_pcb"

# (if building from netlist first:)
# & $kc sch export netlist --format kicadsexpr -o "$env:TEMP\$b.net" $sch
# py -3.13 tools\pcb_netlist_json.py "$env:TEMP\$b.net" "$env:TEMP\$b.json"
# & $kpy tools\pcb_build.py "$env:TEMP\$b.json" $pcb

# STAGE 1: B.Cu only (mask F.Cu as a power layer so the router skips it), BOM-free DSN
& $kpy tools\pcb_route.py dsn $pcb ".routing-tmp\$b.dsn"
$masked = (Get-Content ".routing-tmp\$b.dsn" -Raw) -replace '\(layer F\.Cu\s*\r?\n\s*\(type signal\)', "(layer F.Cu`n      (type power)"
[System.IO.File]::WriteAllText("$env:TEMP\${b}_1l.dsn", $masked)
Remove-Item "$env:TEMP\$b.ses" -ErrorAction SilentlyContinue
java -jar $jar -de "$env:TEMP\${b}_1l.dsn" -do "$env:TEMP\$b.ses" -mp 100 *> ".routing-tmp\fr_$b s1.log"
& $kpy tools\pcb_route.py sesraw $pcb "$env:TEMP\$b.ses"

# STAGE 2: lock stage 1 (exports as type=fix so the router can't rip it), top for leftovers
& $kpy tools\pcb_route.py lockdsn $pcb "$env:TEMP\${b}_2l.dsn"
Remove-Item "$env:TEMP\${b}2.ses" -ErrorAction SilentlyContinue
java -jar $jar -de "$env:TEMP\${b}_2l.dsn" -do "$env:TEMP\${b}2.ses" -mp 100 *> ".routing-tmp\fr_$b s2.log"
if (Test-Path "$env:TEMP\${b}2.ses") { & $kpy tools\pcb_route.py ses $pcb "$env:TEMP\${b}2.ses" }
else { & $kpy tools\pcb_route.py ses $pcb "-" }   # finish (zones+text) with no top import

& $kc pcb drc -o "$out\$b.drc.txt" $pcb
```

`pcb_route.py ses` is a **merge-import**: Freerouting doesn't re-emit the locked stage-1
wires in its SES, so the importer snapshots them and re-adds whatever got dropped, then
lays the no-net laser zones on both copper layers and the copper refdes text on F.Cu.
It's idempotent. Never do a raw SES import after stage 2 — it wipes stage-1 copper.

## Placement notes (pcb_build.py)

- Board is fixed 104×104. Components pack compactly (5 mm gaps) in a cluster that's then
  centered in the outline, so nothing sits against the edge cuts. The builder **fails
  hard** if a cluster won't fit — that's a real signal, not a nuisance; tighten the row
  cap or hand-place.
- Dense or oddly-shaped boards get an explicit entry in the `PLACE` dict (mppt,
  current_sense, buck_v2 have them) following the signal flow left→right. Hand-placing
  cut both the bridge count and the via count dramatically vs. the auto-packer.
- **Pin-letter trap:** `Device:Q_NMOS` pins are G/D/S but TO-220 pads are 1/2/3;
  `pcb_build.py` maps them and fails hard if any component ends up with zero netted pads.

## Reading top-track stats (for the docs, don't guess)

```python
# count F.Cu segments, total length, vias from the .kicad_pcb
import math, re
from pathlib import Path
txt = Path("boards/<b>/<b>.kicad_pcb").read_text(encoding="utf-8")
segs = re.findall(r'\(segment\s*\(start ([-\d.]+) ([-\d.]+)\)\s*\(end ([-\d.]+) ([-\d.]+)\)\s*\(width [\d.]+\)\s*\(layer "F\.Cu"\)', txt)
total = sum(math.hypot(float(x2)-float(x1), float(y2)-float(y1)) for x1,y1,x2,y2 in segs)
print(len(segs), "top segs,", round(total), "mm,", len(re.findall(r'\(via\s', txt)), "vias")
```

## Production export

`pcb_export_production.ps1` handles the standard boards; for a one-off board copy the
export block from it (DXF bottom = `B.Cu,Edge.Cuts`, DXF top = `F.Cu,Edge.Cuts`, gerbers
+ Excellon). Cut blanks to **109×109 mm**. Update `production/README.md` and
`PCB_RESULTS.md` with the per-board top-track numbers.
