# Produktions-eksport til XTool fiberlaseren jf. DTU-PCB-prototyping-guiden:
#   production/<board>/<board>.dxf   - laser-filen (B.Cu + Edge.Cuts, drill marks Small, mm)
#   production/<board>/gerbers/      - standard Gerber-saet + Excellon-drill
# Brug: .\pcb_export_production.ps1
$kc = "C:\Program Files\KiCad\9.0\bin\kicad-cli.exe"
$map = @{
    buck             = "converters\design\pcb\buck.kicad_pcb"
    boost            = "converters\design\pcb\boost.kicad_pcb"
    drive_circuit    = "exp3a\pcb\drive_circuit.kicad_pcb"
    feedback_circuit = "exp3a\pcb\feedback_circuit.kicad_pcb"
    rectifier        = "system\pcb\rectifier.kicad_pcb"
    mppt             = "system\pcb\mppt.kicad_pcb"
    current_sense    = "system\pcb\current_sense.kicad_pcb"
}
foreach ($b in $map.Keys | Sort-Object) {
    $pcb = $map[$b]; $out = "production\$b"
    New-Item -ItemType Directory -Force "$out\gerbers" | Out-Null
    Write-Host "=== $b ==="
    # DXF til laseren: B.Cu + Edge.Cuts i EN fil, drill marks = small (1), mm,
    # ingen kontur-plot (guidens eksport-indstillinger)
    & $kc pcb export dxf --mode-single -l "B.Cu,Edge.Cuts" --ou mm --drill-shape-opt 1 `
        -o "$out\$b.dxf" $pcb | Out-Null
    if (Test-Path "$out\$b.dxf") { Write-Host "  dxf ok" } else { Write-Host "  DXF FEJLEDE" }
    # Gerbers (enkeltsidet saet) + drill
    & $kc pcb export gerbers -l "B.Cu,Edge.Cuts,B.Mask,F.Silkscreen,F.Fab" `
        -o "$out\gerbers\" $pcb | Out-Null
    & $kc pcb export drill --format excellon -o "$out\gerbers\" $pcb | Out-Null
    $n = (Get-ChildItem "$out\gerbers" | Measure-Object).Count
    Write-Host "  gerbers: $n filer"
}
