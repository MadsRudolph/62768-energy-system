# tools/

## srm-cam — Roland SRM-20 CAM tool (git submodule)

`tools/srm-cam/` is a **git submodule** pointing at
[`MadsRudolph/gerber2rml`](https://github.com/MadsRudolph/gerber2rml) (private):
a standalone tool that converts our KiCad Gerber/Excellon exports into Roland
SRM-20 **RML** jobs (trace isolation, drilling, board cutout) — the CNC-mill
alternative to the fiber laser.

### First checkout / after pulling this in

```bash
git submodule update --init tools/srm-cam
```

(or clone the team repo with `git clone --recurse-submodules …`). You need read
access to the private `gerber2rml` repo.

### Use it

```bash
cd tools/srm-cam
python -m venv .venv && .venv\Scripts\activate     # Windows
pip install -e ".[dev,gui]"
python -m gerber2rml.cli <gerber-folder> -o out -n <board>   # CLI → 3 .rml + runplan
python -m gerber2rml                                          # GUI (preview + export)
```

Gerbers come from the usual KiCad production export (see
`hardware/kicad/WORKFLOW.md`). Full docs live in the submodule: `tools/srm-cam/README.md`,
`tools/srm-cam/docs/design.md`.

### ⚠️ Not yet hardware-verified

Run `tools/srm-cam/docs/parity-mosfet_test.md` (compare against the mods website on a
real board) before cutting copper. The fiber-laser flow remains the default until then.

### Updating the pin

The submodule is pinned to a specific `gerber2rml` commit. To move the team repo to a
newer version: `cd tools/srm-cam && git pull origin main && cd ../.. && git add tools/srm-cam && git commit`.
