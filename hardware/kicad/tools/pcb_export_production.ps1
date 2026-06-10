# Produktions-eksport til XTool fiberlaseren jf. DTU-PCB-prototyping-guiden:
#   production/<board>/<board>.dxf          - BUNDEN (B.Cu + Edge.Cuts) - SKAL spejlvendes i xTool
#   production/<board>/<board>_top_cu.dxf   - TOPPEN (F.Cu + Edge.Cuts) - traadbro-plan ELLER
#                                             side 2 ved dobbeltsidet aetsning. IKKE spejlvendes.
#   production/<board>/<board>_silk_top.dxf - valgfri topside-tekst. IKKE spejlvendes.
#   production/<board>/gerbers/             - komplet Gerber-saet + Excellon-drill
# Koeres fra hardware\kicad: .\tools\pcb_export_production.ps1
$kc = "C:\Program Files\KiCad\9.0\bin\kicad-cli.exe"
foreach ($b in @("buck","boost","current_sense","drive_circuit","feedback_circuit","mppt","rectifier")) {
    $pcb = "boards\$b\$b.kicad_pcb"; $out = "production\$b"
    New-Item -ItemType Directory -Force "$out\gerbers" | Out-Null
    Write-Host "=== $b ==="
    # DXF til laseren: kobberlag + Edge.Cuts i EN fil, drill marks = small (1),
    # mm, ingen kontur-plot (guidens eksport-indstillinger)
    & $kc pcb export dxf --mode-single -l "B.Cu,Edge.Cuts" --ou mm --drill-shape-opt 1 `
        -o "$out\$b.dxf" $pcb | Out-Null
    & $kc pcb export dxf --mode-single -l "F.Cu,Edge.Cuts" --ou mm --drill-shape-opt 1 `
        -o "$out\${b}_top_cu.dxf" $pcb | Out-Null
    if ((Test-Path "$out\$b.dxf") -and (Test-Path "$out\${b}_top_cu.dxf")) { Write-Host "  dxf ok (bund + top)" }
    else { Write-Host "  DXF FEJLEDE" }
    # valgfri topside-tekst (F.Silkscreen): graveres paa OVERSIDEN. IKKE spejlvendes.
    & $kc pcb export dxf --mode-single -l "F.Silkscreen,Edge.Cuts" --ou mm --drill-shape-opt 0 `
        -o "$out\${b}_silk_top.dxf" $pcb | Out-Null
    # Gerbers (begge kobberlag) + drill
    & $kc pcb export gerbers -l "F.Cu,B.Cu,Edge.Cuts,B.Mask,F.Mask,F.Silkscreen,F.Fab" `
        -o "$out\gerbers\" $pcb | Out-Null
    & $kc pcb export drill --format excellon -o "$out\gerbers\" $pcb | Out-Null
    $n = (Get-ChildItem "$out\gerbers" | Measure-Object).Count
    Write-Host "  gerbers: $n filer"
}
