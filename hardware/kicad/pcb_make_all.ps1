# Bygger alle 7 boards: netliste -> placeret PCB -> Freerouting (kun B.Cu) -> DRC + render.
# Kraever: KiCad 9, py -3.13 med sexpdata, java 21+ og freerouting-2.0.1.jar
# (https://github.com/freerouting/freerouting/releases/tag/v2.0.1).
# Brug: .\pcb_make_all.ps1 -Jar C:\sti\til\freerouting-2.0.1.jar [-Boards buck,boost,...]
param(
    [string]$Jar = "$env:TEMP\freerouting\freerouting-2.0.1.jar",
    [string[]]$Boards = @("buck","boost","drive_circuit","feedback_circuit","rectifier","mppt","current_sense")
)
$kc  = "C:\Program Files\KiCad\9.0\bin\kicad-cli.exe"
$kpy = "C:\Program Files\KiCad\9.0\bin\python.exe"
$map = @{
    buck             = @{ sch = "converters\design\buck.kicad_sch";          out = "converters\design\pcb" }
    boost            = @{ sch = "converters\design\boost.kicad_sch";         out = "converters\design\pcb" }
    drive_circuit    = @{ sch = "exp3a\drive_circuit.kicad_sch";             out = "exp3a\pcb" }
    feedback_circuit = @{ sch = "exp3a\feedback_circuit.kicad_sch";          out = "exp3a\pcb" }
    rectifier        = @{ sch = "system\rectifier.kicad_sch";                out = "system\pcb" }
    mppt             = @{ sch = "system\mppt.kicad_sch";                     out = "system\pcb" }
    current_sense    = @{ sch = "system\current_sense.kicad_sch";            out = "system\pcb" }
}
foreach ($b in $Boards) {
    $m = $map[$b]; $out = $m.out; $pcb = "$out\$b.kicad_pcb"
    New-Item -ItemType Directory -Force $out | Out-Null
    Write-Host "=== $b ==="
    & $kc sch export netlist --format kicadsexpr -o "$env:TEMP\$b.net" $m.sch | Out-Null
    py -3.13 pcb_netlist_json.py "$env:TEMP\$b.net" "$env:TEMP\$b.json"
    & $kpy pcb_build.py "$env:TEMP\$b.json" $pcb
    & $kpy pcb_route.py dsn $pcb "$env:TEMP\$b.dsn"
    # F.Cu saettes til 'power' saa Freerouting kun bruger bagsiden (enkeltsidet)
    (Get-Content "$env:TEMP\$b.dsn" -Raw) -replace '\(layer F\.Cu\s*\r?\n\s*\(type signal\)', "(layer F.Cu`n      (type power)" |
        Set-Content "$env:TEMP\${b}_1l.dsn" -Encoding UTF8
    Remove-Item "$env:TEMP\$b.ses" -ErrorAction SilentlyContinue
    java -jar $Jar -de "$env:TEMP\${b}_1l.dsn" -do "$env:TEMP\$b.ses" -mp 50 -mt 1 2>&1 |
        Select-String "completed|Saving" | ForEach-Object { "  $_" }
    if (Test-Path "$env:TEMP\$b.ses") { & $kpy pcb_route.py ses $pcb "$env:TEMP\$b.ses" }
    else { Write-Host "  INGEN SES - board forbliver uroutet" }
    & $kc pcb drc -o "$out\$b.drc.txt" $pcb | Out-Null
    Select-String -Path "$out\$b.drc.txt" -Pattern "Found" | ForEach-Object { "  $($_.Line)" }
    & $kc pcb render --side bottom --background opaque -o "$out\${b}_bottom.png" $pcb 2>&1 | Out-Null
    & $kc pcb render --side top    --background opaque -o "$out\${b}_top.png"    $pcb 2>&1 | Out-Null
}
