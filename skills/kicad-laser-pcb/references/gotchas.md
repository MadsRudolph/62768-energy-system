# Gotchas — symptom → cause → fix

Every one of these cost real time. When something misbehaves, scan here first.

| Symptom | Cause / fix |
|---|---|
| Freerouting "routes" (CPU busy) but never writes the SES; log shows `NullPointerException ... gson.JsonObject.get` | 2.0.1's version-check phones home and NPEs, killing the save. **Use the 1.9.0 jar.** |
| Freerouting "file not found" on a DSN that exists, or "Non-ansi character at position 0" | UTF-8 **BOM** in the DSN, from PowerShell 5.1's `Set-Content -Encoding utf8`. Write with `[System.IO.File]::WriteAllText(...)`. |
| KiCad lib-table won't parse: "Expecting '(' ... line 1, offset 1" | Same BOM bug — a `sym-lib-table`/`fp-lib-table` written with `Set-Content -Encoding utf8`. Rewrite BOM-free with `WriteAllText`. |
| Blocking dialog "wxWidgets Debug Alert … non-closed outline" during DSN export | Harmless KiCad-stable assert. Run this dismisser in the background during batches: `$sh=New-Object -ComObject WScript.Shell; while($true){if($sh.AppActivate("wxWidgets Debug Alert")){Start-Sleep -m 150;$sh.SendKeys("n")};Start-Sleep -m 400}` |
| Freerouting genuinely hangs after "Route optimization completed" | Flaky save phase — 1–3 min is normal, >5 min is hung. Kill java, re-run that board. **Never** launch java with `-WindowStyle Hidden` (kills its GUI event pump → guaranteed hang). |
| Freerouting exits instantly, no SES | Wrong Java for the jar (2.2.x needs Java 25). Use 1.9.0 on Java 21. |
| SES import wiped the stage-1 routing | Raw import after stage 2. Use `pcb_route.py ses` (merge-import), which re-adds the locked wires. |
| `pcbnew` `ZONE.Remove()` / track removal access-violates (exit code -1073741819) in-process | KiCad 9.0.6 SWIG bug. Don't remove zones/tracks in a loaded board via python — strip textually with sexpdata (`scripts/strip_routing.py`, or `route_board.ps1 -KeepPlacement`). |
| `shorting_items` / clearance errors right after a route | Often a transient SES merge artifact. **Re-run the board once** — it usually clears (seen on rectifier, mppt). If it persists, the placement is too tight; open the crowded row. |
| MOSFET/transistor pads end up `<no net>` (and DRC stays silent!) | Letter pin numbers (G/D/S) vs numeric pads (1/2/3). `pcb_build.py` maps Q_NMOS and fails hard if a whole component gets no nets; new letter-pin symbols need the same mapping. |
| `power_pin_not_driven` ERC errors | Add `power:PWR_FLAG` symbols on connector-fed supply nets. (Copy the lib-symbol from a board that has one — e.g. mppt — and write fresh instances.) |
| KiCad GUI routes with 0.2 mm clearance | Board opened without its `.kicad_pro` (netclass lives there). Open the project file, not the bare `.kicad_pcb`. |
| "Update PCB from Schematic" unlinks everything | Tick "Re-link footprints to schematic symbols based on their reference designators" — script-built boards have no symbol UUIDs the first time. |
| `git add -A` aborts in the umbrella repo | A broken nested submodule. Stage by explicit path. (The team repo itself is fine; this only bites the outer umbrella.) |
| PowerShell mangles inline python/`java -D...` flags (quotes, braces, `-D` parsed as path) | Write a temp `.py`/`.ps1` file instead of `py -c` / inline for anything non-trivial; quote `-D` flags as `"-Dfoo=bar"`. |
| Shop CSV "not found" | Per-PC download, not in the repo, and people move it around. Ask the user for the path (often their Downloads folder). |
| Python UnicodeEncodeError printing Ω etc. on Windows | `$env:PYTHONIOENCODING = "utf-8"` before the call, or read the CSV with `errors="replace"`. |

## Background-job hygiene

Routing batches take minutes. Run the dismisser and the pipeline in the background, and
keep the dismisser's lifetime longer than the batch (re-launch if it expires mid-run).
Stop leftover dismissers when the work is done.
