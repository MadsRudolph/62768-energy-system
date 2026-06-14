# Team skills

Claude Code/Claude.ai skills for this project. A "skill" is a playbook Claude loads
automatically when it's relevant — install once and Claude knows our workflow.

## kicad-laser-pcb

The full KiCad → xTool fiber-laser PCB pipeline: schematic design-bug review
(gate drive, grounding, output caps, opto isolation), through-hole footprint
assignment, the 104×104 mm jig format, two-stage Freerouting, and DXF/Gerber export.
Encodes every gotcha we hit (Freerouting 1.9-not-2.0.1, the PowerShell BOM bug,
the `pcbnew` zone-removal crash, the pin-letter trap, …).

**Self-contained.** It bundles its own scripts (`scripts/`) and the laser footprint
library (`lib/`), so it works on *anyone's* KiCad 9 project — you do **not** need
access to our team repo to use it. Share the single `.skill` file with the whole class
and it just works (after the one-time toolchain install below).

### Install (each person, once)

**Option A — the packaged file (easiest to share).** Hand someone
`kicad-laser-pcb.skill` and they install it via the skills UI in Claude Code / the
Claude desktop app. Nothing else needed.

**Option B — copy the source folder** into your personal skills directory:

```powershell
# Windows
Copy-Item -Recurse "skills\kicad-laser-pcb" "$env:USERPROFILE\.claude\skills\"
```
```bash
# macOS / Linux
cp -r skills/kicad-laser-pcb ~/.claude/skills/
```

Restart Claude Code (or reload skills) and it'll show up. Ask something like
"route this buck board" or "review this boost schematic" and it triggers — pointed at
*your own* KiCad project.

### First-time toolchain setup

The skill drives the scripts in `hardware/kicad/tools/`, which need KiCad 9, Java 21,
Python 3.13 + sexpdata, and the Freerouting **1.9.0** jar. The one-time install steps
are in the skill's `references/setup.md` (Claude will walk you through them, or read it
directly). The pipeline is Windows + PowerShell; schematic review and footprint work
are fine on any OS, but routing/export need Windows + KiCad 9.

### Updating the skill

Edit the source under `skills/kicad-laser-pcb/`, then anyone can re-copy it. (The
`.skill` package is a convenience snapshot — regenerate it with the skill-creator's
`package_skill.py` if you change the source and want to redistribute the one-file
version.)
