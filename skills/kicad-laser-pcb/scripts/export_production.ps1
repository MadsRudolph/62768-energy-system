# Production export for ONE board: laser DXFs + Gerbers. Standalone (no team repo).
#   .\export_production.ps1 -Pcb path\to\board.kicad_pcb -OutDir path\to\out
# Produces in OutDir:
#   <board>.dxf         bottom copper + edge cuts  (MIRROR this in xTool)
#   <board>_top_cu.dxf  top copper + edge cuts     (wire-bridge plan / 2nd etch; NOT mirrored)
#   <board>_silk_top.dxf  optional top silkscreen  (NOT mirrored)
#   gerbers\            full Gerber set + Excellon drill
param(
    [Parameter(Mandatory=$true)][string]$Pcb,
    [string]$OutDir,
    [string]$KicadBin = "C:\Program Files\KiCad\9.0\bin"
)
$ErrorActionPreference = "Stop"
$kc = Join-Path $KicadBin "kicad-cli.exe"
if (-not (Test-Path $kc))  { throw "kicad-cli ikke fundet: $kc (se references/setup.md)" }
if (-not (Test-Path $Pcb)) { throw "board ikke fundet: $Pcb" }
$b = [System.IO.Path]::GetFileNameWithoutExtension($Pcb)
if (-not $OutDir) { $OutDir = Join-Path (Split-Path $Pcb) "production" }
New-Item -ItemType Directory -Force "$OutDir\gerbers" | Out-Null

# DXF: copper layer + Edge.Cuts in ONE file, drill marks small, mm, no contour
& $kc pcb export dxf --mode-single -l "B.Cu,Edge.Cuts"        --ou mm --drill-shape-opt 1 -o "$OutDir\$b.dxf" $Pcb | Out-Null
& $kc pcb export dxf --mode-single -l "F.Cu,Edge.Cuts"        --ou mm --drill-shape-opt 1 -o "$OutDir\${b}_top_cu.dxf" $Pcb | Out-Null
& $kc pcb export dxf --mode-single -l "F.Silkscreen,Edge.Cuts" --ou mm --drill-shape-opt 0 -o "$OutDir\${b}_silk_top.dxf" $Pcb | Out-Null
& $kc pcb export gerbers -l "F.Cu,B.Cu,Edge.Cuts,B.Mask,F.Mask,F.Silkscreen,F.Fab" -o "$OutDir\gerbers\" $Pcb | Out-Null
& $kc pcb export drill --format excellon -o "$OutDir\gerbers\" $Pcb | Out-Null
Write-Output "${b}: DXF + Gerbers i $OutDir (skaer emnet 109x109; spejlvend KUN $b.dxf i xTool)"
