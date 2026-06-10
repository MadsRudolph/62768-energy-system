# Bygger alle 7 boards: netliste -> placeret PCB -> Freerouting -> DRC + render.
# Routing: B.Cu foretraekkes (etch-siden); F.Cu er tilladt til de kryds der ikke
# kan klares enkeltsidet (topbaner = designede traadbroer ELLER side 2 ved
# dobbeltsidet aetsning). Maal: 0 uroutede net.
# Kraever: KiCad 9, py -3.13 med sexpdata, java 21+ og freerouting-2.0.1.jar
# (https://github.com/freerouting/freerouting/releases/tag/v2.0.1).
# Koeres fra hardware\kicad: .\tools\pcb_make_all.ps1 -Jar <sti>\freerouting-2.0.1.jar [-Boards buck,...]
param(
    [string]$Jar = "$env:TEMP\freerouting\freerouting-2.0.1.jar",
    [string[]]$Boards = @("buck","boost","drive_circuit","feedback_circuit","rectifier","mppt","current_sense")
)
$kc  = "C:\Program Files\KiCad\9.0\bin\kicad-cli.exe"
$kpy = "C:\Program Files\KiCad\9.0\bin\python.exe"
foreach ($b in $Boards) {
    # projektet ligger i boards\<navn>\ (samme basenavn .kicad_pro/sch/pcb saa
    # KiCad linker skema <-> PCB); rapporter/renders ryger i pcb\-undermappen
    $sch = "boards\$b\$b.kicad_sch"; $pcb = "boards\$b\$b.kicad_pcb"; $out = "boards\$b\pcb"
    New-Item -ItemType Directory -Force $out | Out-Null
    Write-Host "=== $b ==="
    & $kc sch export netlist --format kicadsexpr -o "$env:TEMP\$b.net" $sch | Out-Null
    py -3.13 tools\pcb_netlist_json.py "$env:TEMP\$b.net" "$env:TEMP\$b.json"
    & $kpy tools\pcb_build.py "$env:TEMP\$b.json" $pcb

    # TRIN 1: route alt der KAN ligge paa bagsiden (F.Cu maskeret som power-lag)
    & $kpy tools\pcb_route.py dsn $pcb "$env:TEMP\$b.dsn"
    (Get-Content "$env:TEMP\$b.dsn" -Raw) -replace '\(layer F\.Cu\s*\r?\n\s*\(type signal\)', "(layer F.Cu`n      (type power)" |
        Set-Content "$env:TEMP\${b}_1l.dsn" -Encoding UTF8
    Remove-Item "$env:TEMP\$b.ses" -ErrorAction SilentlyContinue
    java -jar $Jar -de "$env:TEMP\${b}_1l.dsn" -do "$env:TEMP\$b.ses" -mp 100 -mt 1 2>&1 |
        Select-String "completed in|Saving" | ForEach-Object { "  1: $_" }
    if (Test-Path "$env:TEMP\$b.ses") { & $kpy tools\pcb_route.py sesraw $pcb "$env:TEMP\$b.ses" }
    else { Write-Host "  trin 1: INGEN SES"; continue }

    # TRIN 2: laas bagside-kobberet (type fix) og lad Freerouting tage RESTEN
    # med toppen tilladt - topbaner = designede traadbroer / side 2
    & $kpy tools\pcb_route.py lockdsn $pcb "$env:TEMP\${b}_2l.dsn"
    Remove-Item "$env:TEMP\$b.ses" -ErrorAction SilentlyContinue
    java -jar $Jar -de "$env:TEMP\${b}_2l.dsn" -do "$env:TEMP\$b.ses" -mp 100 -mt 1 2>&1 |
        Select-String "completed in|Saving" | ForEach-Object { "  2: $_" }
    if (Test-Path "$env:TEMP\$b.ses") { & $kpy tools\pcb_route.py ses $pcb "$env:TEMP\$b.ses" }
    else { Write-Host "  trin 2: INGEN SES - kun bagside-routing"; & $kpy tools\pcb_route.py ses $pcb "-" }
    & $kc pcb drc -o "$out\$b.drc.txt" $pcb | Out-Null
    Select-String -Path "$out\$b.drc.txt" -Pattern "Found" | ForEach-Object { "  $($_.Line)" }
    & $kc pcb render --side bottom --background opaque -o "$out\${b}_bottom.png" $pcb 2>&1 | Out-Null
    & $kc pcb render --side top    --background opaque -o "$out\${b}_top.png"    $pcb 2>&1 | Out-Null
}
