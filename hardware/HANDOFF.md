# Roland SRM-20 PCB Milling — FlatCAM Workflow

## Context

This folder supports PCB milling on the **Roland monoFab SRM-20** at DTU Ballerup Campus,
as an alternative to the xTool F1 Ultra fiber laser workflow documented in the repo root.

The SRM-20 uses **RML-1** motion language, not standard G-code.
The toolchain is: **KiCad → Gerber/Excellon → FlatCAM → G-code → RML-1 → SRM-20**.

PCB design constraints (from repo root README) still apply:
- Single-sided only (B.Cu)
- Minimum trace width: 0.8mm (1.0mm preferred)
- Minimum clearance: 0.8mm
- All traces on B.Cu layer

---

## Folder Structure

```
roland-cnc/
├── CLAUDE.md              ← this file
├── exports/               ← KiCad Gerber + Excellon exports go here
│   ├── *.gbr              ← Gerber files (B.Cu, Edge.Cuts)
│   └── *.drl              ← Excellon drill file
├── flatcam/               ← FlatCAM project files and G-code output
│   ├── *.FlatPrj          ← saved FlatCAM project
│   ├── traces.nc          ← G-code: isolation routing
│   ├── drill.nc           ← G-code: drilling
│   └── cutout.nc          ← G-code: board outline cutout
└── rml/                   ← Final RML-1 files ready for SRM-20 VPanel
    ├── traces.rml
    ├── drill.rml
    └── cutout.rml
```

---

## Step 1 — Export from KiCad

In the KiCad PCB Editor:

`File → Fabrication Outputs → Gerbers (.gbr)`

In the Plot dialog:
- **Format**: Gerber
- **Include Layers**: B.Cu, Edge.Cuts
- **Drill marks**: None (drills come from Excellon separately)
- **Plot graphic items using their contours**: unchecked
- **Export units**: Millimeters
- Click **Plot**

Then click **Generate Drill Files**:
- Format: Excellon
- Units: Millimeters
- Zeros format: Suppress leading zeros
- Click **Generate Drill File**

Place all outputs in `exports/`.

---

## Step 2 — FlatCAM Setup

FlatCAM version: **8.994** (legacy stable, not the beta).
Download: https://bitbucket.org/jpcgt/flatcam/downloads/

Open FlatCAM and import the three files:
- `exports/*-B_Cu.gbr` → copper layer
- `exports/*-Edge_Cuts.gbr` → board outline
- `exports/*.drl` → drill file

### Isolation Routing (traces)

1. Select the B.Cu Gerber object
2. `Selected → Isolation Routing`
3. Parameters:
   - **Tool dia**: 0.1mm (use actual bit diameter — measure with calipers)
   - **Width (passes)**: 2 (one pass often leaves burrs)
   - **Pass overlap**: 0.15
   - **Combine passes**: checked
4. Click **Generate Geometry**
5. Select the resulting geometry → `Selected → Create CNC Job`
   - **Cut Z**: -0.1mm (adjust based on copper thickness — 1oz = ~0.035mm, go slightly deeper)
   - **Travel Z**: 2.0mm
   - **Feed rate**: 100 mm/min (conservative for SRM-20)
   - **Spindle speed**: leave 0 (SRM-20 spindle is always on, speed set on machine)
6. Click **Generate CNC Job** → export as `flatcam/traces.nc`

### Drilling

1. Select the Excellon object
2. `Selected → Create CNC Job`
   - **Cut Z**: -1.8mm (through 1.6mm board + a little into spoilboard)
   - **Travel Z**: 2.0mm
   - **Feed rate**: 60 mm/min
3. Export as `flatcam/drill.nc`

### Board Cutout

1. Select the Edge.Cuts Gerber object
2. `Selected → Isolation Routing`
   - **Tool dia**: 1.0mm (or whatever cutout bit is available)
   - **Width**: 1
3. Generate geometry → Create CNC Job
   - **Cut Z**: -1.8mm
   - **Travel Z**: 2.0mm
   - **Feed rate**: 80 mm/min
   - **Multi-depth**: checked, **Depth/pass**: 0.5mm
4. Export as `flatcam/cutout.nc`

---

## Step 3 — Convert G-code to RML-1

The SRM-20 does not accept standard G-code. Convert using **grbl2rml**
or the Python script below (save as `gcode_to_rml.py` in this folder):

```python
#!/usr/bin/env python3
"""
Minimal G-code to RML-1 converter for Roland SRM-20.
Handles G00/G01 moves and tool up/down (Z).
Usage: python3 gcode_to_rml.py input.nc output.rml
"""
import sys, re

SCALE = 40  # RML-1 units per mm (SRM-20 = 40 units/mm)
Z_UP   =  2.0   # mm — travel height
Z_DOWN = -0.1   # mm — cut depth (override per operation if needed)

def mm_to_rml(val):
    return int(round(float(val) * SCALE))

def convert(infile, outfile):
    lines = open(infile).readlines()
    out = []
    out.append("^IN;!MC0;V15;Z1168,1168,1168;")  # SRM-20 init, spindle on

    x = y = z = 0.0
    for line in lines:
        line = line.strip().upper()
        mx = re.search(r'X([-\d.]+)', line)
        my = re.search(r'Y([-\d.]+)', line)
        mz = re.search(r'Z([-\d.]+)', line)
        if mx: x = float(mx.group(1))
        if my: y = float(my.group(1))
        if mz: z = float(mz.group(1))

        if line.startswith('G00') or line.startswith('G01'):
            rx, ry, rz = mm_to_rml(x), mm_to_rml(y), mm_to_rml(z)
            out.append(f"Z{rx},{ry},{rz};")

    out.append("!MC0;^IN;")  # spindle off, reset
    open(outfile, 'w').write('\n'.join(out) + '\n')
    print(f"Written {len(out)-2} moves to {outfile}")

if __name__ == '__main__':
    convert(sys.argv[1], sys.argv[2])
```

Run for each operation:
```bash
python3 gcode_to_rml.py flatcam/traces.nc rml/traces.rml
python3 gcode_to_rml.py flatcam/drill.nc  rml/drill.rml
python3 gcode_to_rml.py flatcam/cutout.nc rml/cutout.rml
```

---

## Step 4 — SRM-20 VPanel

1. Open **VPanel for SRM-20** on the lab PC
2. Home the machine (X/Y/Z)
3. Set material origin: jog to bottom-left corner of your PCB stock, zero X and Y
4. Set Z origin: jog Z down until bit just touches copper surface, zero Z
5. Load `rml/traces.rml` → **Cut**
6. Load `rml/drill.rml` → **Cut**
7. Load `rml/cutout.rml` → **Cut** (tape down board edges before cutout)

---

## Bit Recommendations

| Operation       | Bit type              | Diameter  | Notes                        |
|-----------------|-----------------------|-----------|------------------------------|
| Isolation rout  | V-bit or flat endmill | 0.1–0.2mm | 30° V-bit gives cleaner walls|
| Drilling        | PCB drill             | Match hole| 0.8mm for most THT pads      |
| Board cutout    | Flat endmill          | 1.0mm     | Climb cut, multi-pass        |

---

## Gotchas

- **Z zeroing is critical** — the SRM-20 has no autofocus. Use a piece of paper between bit and board to feel the contact point.
- **Spoilboard**: always place a sacrificial MDF sheet under the PCB so drill and cutout passes don't damage the machine bed.
- **Board must be taped flat** — use double-sided tape across the full board surface. Any flex ruins trace depth consistency.
- **Mirroring**: B.Cu in KiCad is already the bottom layer. When you place the board copper-side up on the SRM-20, the coordinate system matches — do NOT mirror in FlatCAM.
- **FlatCAM units**: make sure FlatCAM is set to **mm** (Options → Units) before importing. Mixing mm/inch silently corrupts the toolpath scale.

---

## TODO / Open Questions

- [ ] Confirm actual bit sizes available at DTU Ballerup BuildDesign Lab
- [ ] Confirm SRM-20 VPanel version installed on lab PC
- [ ] Test Z cut depth on scrap board — 0.1mm may need tuning for the local copper stock
- [ ] Verify RML-1 converter handles arcs (G02/G03) — current script ignores them (FlatCAM rarely outputs arcs for PCB isolation, but cutouts can)
- [ ] Roland MODELA Player 4 as alternative to manual RML conversion — evaluate

---

*Handoff for Claude Code — place this folder inside the KiCad project repo.*
*Last updated: 2026-06-18*
