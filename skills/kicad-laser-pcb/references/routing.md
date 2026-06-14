# Routing & production (two-stage Freerouting)

`<skill>` = this skill's directory; `<proj>` = the user's KiCad project.

## Why two stages

The boards are single-sided: the etched side is **B.Cu**, and only the crossings that
are physically impossible single-sided go on **F.Cu** (built as wire bridges, or a
second etch). Stage 1 routes everything it can on the bottom, locks it, then stage 2
lets Freerouting put just the leftovers on top.

## The easy path: route_board.ps1

`scripts/route_board.ps1` runs the whole thing for one board. Launch the assert-dialog
dismisser first (`gotchas.md`), then:

```powershell
# fresh board from schematic (places at 104x104, then routes):
<skill>\scripts\route_board.ps1 -Sch <proj>\<b>.kicad_sch -Pcb <proj>\<b>.kicad_pcb
# re-route a board you placed by hand in the GUI (keeps placement):
<skill>\scripts\route_board.ps1 -Pcb <proj>\<b>.kicad_pcb -KeepPlacement
```

Override toolchain locations if needed: `-Jar <path-to-freerouting-1.9.0.jar>`,
`-KicadBin "C:\Program Files\KiCad\9.0\bin"`. The script validates that KiCad, the jar,
and Python are present and points you at `setup.md` if not.

## Two hard-won tool facts (baked into the script — don't undo them)

1. **Freerouting 1.9.0, not 2.0.1.** 2.0.1's version-check phones home and throws a
   `NullPointerException` (`gson.JsonObject.get` returns null) that takes the
   job-completion chain with it — routing finishes but the SES is never written, so the
   job looks hung forever. 1.9.0 routes purely locally on Java 21.
2. **DSN files must be BOM-free.** PowerShell 5.1's `Set-Content -Encoding utf8`
   prepends a UTF-8 BOM, and Freerouting's parser chokes on it ("file not found" /
   "Non-ansi character at position 0"). The script writes with
   `[System.IO.File]::WriteAllText`.

## What the script does internally (for debugging / one-off variants)

If you need to drive the steps by hand (custom flow, partial re-run), this is the
sequence `route_board.ps1` runs. `$kpy` = KiCad's bundled python, `$jar` = Freerouting
1.9.0, `$b` = board basename.

```powershell
# fresh build only (skip if re-routing an existing placement):
& $kc sch export netlist --format kicadsexpr -o "$tmp\$b.net" <proj>\$b.kicad_sch
py -3.13 <skill>\scripts\pcb_netlist_json.py "$tmp\$b.net" "$tmp\$b.json"
& $kpy <skill>\scripts\pcb_build.py "$tmp\$b.json" <proj>\$b.kicad_pcb

# re-route an existing placement instead: strip old routing first (textual — an
# in-process pcbnew zone removal access-violates):
py -3.13 <skill>\scripts\strip_routing.py <proj>\$b.kicad_pcb

# STAGE 1 — B.Cu only (mask F.Cu as a power layer so the router skips it), BOM-free DSN
& $kpy <skill>\scripts\pcb_route.py dsn <proj>\$b.kicad_pcb "$tmp\$b.dsn"
$masked = (Get-Content "$tmp\$b.dsn" -Raw) -replace '\(layer F\.Cu\s*\r?\n\s*\(type signal\)', "(layer F.Cu`n      (type power)"
[System.IO.File]::WriteAllText("$tmp\${b}_1l.dsn", $masked)
java -jar $jar -de "$tmp\${b}_1l.dsn" -do "$tmp\$b.ses" -mp 100
& $kpy <skill>\scripts\pcb_route.py sesraw <proj>\$b.kicad_pcb "$tmp\$b.ses"

# STAGE 2 — lock stage 1 (exports type=fix), route leftovers onto F.Cu
& $kpy <skill>\scripts\pcb_route.py lockdsn <proj>\$b.kicad_pcb "$tmp\${b}_2l.dsn"
java -jar $jar -de "$tmp\${b}_2l.dsn" -do "$tmp\${b}2.ses" -mp 100
& $kpy <skill>\scripts\pcb_route.py ses <proj>\$b.kicad_pcb "$tmp\${b}2.ses"  # or "-" if no stage-2 SES
```

`pcb_route.py ses` is a **merge-import**: Freerouting doesn't re-emit the locked
stage-1 wires in its SES, so the importer snapshots them and re-adds whatever got
dropped, then lays the no-net laser zones on both copper layers and the copper refdes
text on F.Cu. Idempotent. Never do a raw SES import after stage 2 — it wipes stage-1
copper.

## Placement notes (pcb_build.py)

- Board is fixed 104×104. Components pack compactly (5 mm gaps) in a cluster that's
  then centered in the outline, so nothing sits against the edge cuts. The builder
  **fails hard** if a cluster won't fit — that's a real signal; tighten or hand-place.
- Dense / oddly-shaped boards get an explicit entry in the `PLACE` dict (there are
  worked examples in the script) following signal flow left→right. Hand-placing cuts
  both bridge and via counts dramatically vs. the auto-packer.
- **Pin-letter trap:** `Device:Q_NMOS` pins are G/D/S but TO-220 pads are 1/2/3;
  `pcb_build.py` maps them and fails hard if a component ends up with zero netted pads.
  A new symbol with letter pins needs the same mapping added.

## Reading top-track stats (don't guess)

```python
import math, re
from pathlib import Path
txt = Path(r"<proj>\<b>.kicad_pcb").read_text(encoding="utf-8")
segs = re.findall(r'\(segment\s*\(start ([-\d.]+) ([-\d.]+)\)\s*\(end ([-\d.]+) ([-\d.]+)\)\s*\(width [\d.]+\)\s*\(layer "F\.Cu"\)', txt)
total = sum(math.hypot(float(x2)-float(x1), float(y2)-float(y1)) for x1,y1,x2,y2 in segs)
print(len(segs), "top segs,", round(total), "mm,", len(re.findall(r'\(via\s', txt)), "vias")
```

## Production export

`scripts/export_production.ps1 -Pcb <proj>\<b>.kicad_pcb -OutDir <proj>\production\<b>`
writes the bottom DXF (mirror in xTool), top DXF (bridge plan), optional silk, and
gerbers + drill. Cut blanks to **109×109 mm**.
