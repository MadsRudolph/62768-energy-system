# First-time setup on a new PC

This skill drives the team repo's `hardware/kicad/tools/` scripts, which assume a
specific toolchain. The scripts and board files travel with the git repo; the tools
below are per-machine and need installing once. The pipeline is **Windows + PowerShell**
(that's what the repo scripts are written in). Schematic review and footprint edits work
anywhere KiCad runs, but routing/export is Windows-only as written.

Verify each before running a routing batch:

| Tool | Check | Get it |
|---|---|---|
| KiCad 9 | `& "C:\Program Files\KiCad\9.0\bin\kicad-cli.exe" version` | kicad.org — install v9.x to the default location |
| KiCad's bundled Python (pcbnew) | `& "C:\Program Files\KiCad\9.0\bin\python.exe" -c "import pcbnew"` | comes with KiCad |
| System Python 3.13 + sexpdata | `py -3.13 -c "import sexpdata"` | python.org, then `py -3.13 -m pip install sexpdata` |
| Java 21 | `java -version` | Adoptium Temurin 21 (Freerouting 1.9 needs Java 21; do NOT use a 2.2+ jar, it needs Java 25) |
| Freerouting 1.9.0 jar | `Test-Path "$env:USERPROFILE\.freerouting\freerouting-1.9.0.jar"` | see below |

## Download the Freerouting jar (once)

```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.freerouting" | Out-Null
Invoke-WebRequest `
  -Uri "https://github.com/freerouting/freerouting/releases/download/v1.9.0/freerouting-1.9.0.jar" `
  -OutFile "$env:USERPROFILE\.freerouting\freerouting-1.9.0.jar"
```

**1.9.0 specifically** — 2.0.1's version-check NPEs and never saves the SES (see
`gotchas.md`), and 2.2+ needs Java 25. `pcb_make_all.ps1` defaults to
`$env:USERPROFILE\.freerouting\freerouting-1.9.0.jar`; pass `-Jar <path>` if yours lives
elsewhere.

## If your KiCad isn't at the default path

The repo scripts (`pcb_make_all.ps1`, `pcb_export_production.ps1`, and the `kicad-cli` /
`python.exe` calls in this skill) hardcode `C:\Program Files\KiCad\9.0\bin`. If you
installed a different 9.x point-release or a custom location, either install to the
default or edit the `$kc`/`$kpy` variables at the top of those scripts. Keep it on
KiCad **9** — the board files use the v9 s-expression format.

## Shop CSV

The component-shop CSV (`dtu_component_shop.csv`) is a per-person download, not in the
repo. You only need it when picking parts for a *new* schematic. Save it anywhere and
tell Claude the path when a task needs it.

## Sanity check

From `hardware/kicad/`, route one small board end to end:

```powershell
.\tools\pcb_make_all.ps1 -Boards rectifier
```

If it produces `boards/rectifier/pcb/rectifier.drc.txt` with 0 errors, the toolchain is
good. If Freerouting hangs or the DSN won't parse, go straight to `gotchas.md` — those
two failure modes are the usual first-run snags.
