# Standalone two-stage Freerouting for ONE board, usable on any KiCad 9 project.
# Bundled with the kicad-laser-pcb skill - no team repo required.
#
#   .\route_board.ps1 -Sch path\to\board.kicad_sch -Pcb path\to\board.kicad_pcb
#       Fresh build: netlist -> placed 104x104 board -> two-stage route -> DRC.
#   .\route_board.ps1 -Pcb path\to\board.kicad_pcb -KeepPlacement
#       Re-route an already-placed board (e.g. hand-placed in the GUI), keeping
#       the placement: strips old routing first, then routes.
#
# Requires KiCad 9, Java 21, Python 3.13+sexpdata, and the Freerouting 1.9.0 jar
# (see ../references/setup.md). Run from anywhere; paths can be absolute.
param(
    [string]$Sch,
    [Parameter(Mandatory=$true)][string]$Pcb,
    [switch]$KeepPlacement,
    [string]$Jar      = "$env:USERPROFILE\.freerouting\freerouting-1.9.0.jar",
    [string]$KicadBin = "C:\Program Files\KiCad\9.0\bin",
    [string]$TmpDir   = "$env:TEMP\kicad-laser"
)
$ErrorActionPreference = "Stop"
$here = $PSScriptRoot
$kc  = Join-Path $KicadBin "kicad-cli.exe"
$kpy = Join-Path $KicadBin "python.exe"
foreach ($p in @($kc, $kpy, $Jar)) {
    if (-not (Test-Path $p)) { throw "ikke fundet: $p  (se references/setup.md)" }
}
New-Item -ItemType Directory -Force $TmpDir | Out-Null
$b = [System.IO.Path]::GetFileNameWithoutExtension($Pcb)

if ($KeepPlacement) {
    if (-not (Test-Path $Pcb)) { throw "-KeepPlacement men boardet findes ikke: $Pcb" }
    py -3.13 "$here\strip_routing.py" $Pcb
} else {
    if (-not $Sch) { throw "angiv -Sch for at bygge et nyt board (eller brug -KeepPlacement)" }
    & $kc sch export netlist --format kicadsexpr -o "$TmpDir\$b.net" $Sch
    py -3.13 "$here\pcb_netlist_json.py" "$TmpDir\$b.net" "$TmpDir\$b.json"
    & $kpy "$here\pcb_build.py" "$TmpDir\$b.json" $Pcb
}

# STAGE 1 - everything that can go on B.Cu (mask F.Cu as power so the router skips it).
# Write the DSN BOM-free: PS 5.1's Set-Content -Encoding utf8 adds a BOM that
# Freerouting's parser rejects ("file not found" / non-ansi char at position 0).
& $kpy "$here\pcb_route.py" dsn $Pcb "$TmpDir\$b.dsn"
$masked = (Get-Content "$TmpDir\$b.dsn" -Raw) -replace '\(layer F\.Cu\s*\r?\n\s*\(type signal\)', "(layer F.Cu`n      (type power)"
[System.IO.File]::WriteAllText("$TmpDir\${b}_1l.dsn", $masked)
Remove-Item "$TmpDir\$b.ses" -ErrorAction SilentlyContinue
java -jar $Jar -de "$TmpDir\${b}_1l.dsn" -do "$TmpDir\$b.ses" -mp 100 *> "$TmpDir\fr_${b}_s1.log"
if (-not (Test-Path "$TmpDir\$b.ses")) { throw "trin 1 gav ingen SES - se $TmpDir\fr_${b}_s1.log (typisk: forkert Freerouting-jar, se gotchas.md)" }
& $kpy "$here\pcb_route.py" sesraw $Pcb "$TmpDir\$b.ses"

# STAGE 2 - lock stage 1 (exports type=fix), let the router put leftovers on F.Cu.
& $kpy "$here\pcb_route.py" lockdsn $Pcb "$TmpDir\${b}_2l.dsn"
Remove-Item "$TmpDir\${b}2.ses" -ErrorAction SilentlyContinue
java -jar $Jar -de "$TmpDir\${b}_2l.dsn" -do "$TmpDir\${b}2.ses" -mp 100 *> "$TmpDir\fr_${b}_s2.log"
if (Test-Path "$TmpDir\${b}2.ses") { & $kpy "$here\pcb_route.py" ses $Pcb "$TmpDir\${b}2.ses" }
else { & $kpy "$here\pcb_route.py" ses $Pcb "-" }   # finish (zones+text) with no top import

$drc = [System.IO.Path]::ChangeExtension($Pcb, ".drc.txt")
& $kc pcb drc -o $drc $Pcb | Out-Null
Select-String -Path $drc -Pattern "Found" | ForEach-Object { $_.Line }
Write-Output "${b}: routing faerdig. DRC-rapport: $drc"
