# Schematic design-review checklist (power converters)

These bugs recur on the converter boards (buck, boost, drive, the MPPT linear stage)
and on teammates' drafts. ERC will **not** catch most of them — they're electrically
"connected", just wrong. The check that finds them is dumping the netlist and reading
net membership by hand:

```powershell
& "C:\Program Files\KiCad\9.0\bin\kicad-cli.exe" sch export netlist --format kicadsexpr `
    -o "$env:TEMP\b.net" boards\<b>\<b>.kicad_sch
py -3.13 <skill>\scripts\pcb_netlist_json.py "$env:TEMP\b.net" "$env:TEMP\b.json"
# then read the json: which refs/pins share each net?
```

Trace the power path pin by pin. Ask of every net: *what voltage is this relative to
GND, and does every part on it expect that?*

## 1. Floating / islanded grounds

A regulator (LF50, 7805, op-amp) whose GND pin sits on a net that touches nothing
else is an **island** — the part has no return, the rail it makes is undefined. Look
for a GND pin sharing a net only with its own decoupling caps and nothing global.
Fix: tie it to the board GND net. ERC's `power_pin_not_driven` is a hint but fires
for benign missing-PWR_FLAG reasons too, so confirm by reading the net.

## 2. High-side gate drive that can't turn the FET on

The classic. An N-MOSFET used as a **high-side** switch (drain on the high rail,
source on the switch node) needs its gate driven *above its source*, and the source
swings up to the rail when the FET conducts. If the gate driver / opto output and the
gate pull-down are referenced to **GND** instead of the **source**, then the moment
the FET turns on and the source rises, V_GS goes negative and the FET shuts itself
off — it never fully enhances, sits in its linear region, and cooks.

Symptoms in the netlist: gate pull-down resistor's other end on `GND` rather than the
source/switch node; opto collector on a ground-referenced rail.

Fixes, in rough order of preference:
- **Floating bootstrap-style aux supply on the switch node** (what buck v1 does with
  `+12V_SW`): the gate-drive supply rides on SW so it's always ~12 V above the source.
  A battery can float here — but then it can *only* do the gate job; it can't also
  power ground-referenced logic, because anchoring either terminal to GND (even
  through a cap — a cap is a short at switching frequency) destroys the float and
  makes the FET fight to charge that cap every edge. Give the logic its own
  ground-referenced supply (e.g. an LDO from the main rail).
- **IR2110 bootstrap** (what the motor-drive board does): VS→SW, bootstrap diode +
  cap VB→VS.
- **P-channel high-side** with level-shifted drive.

## 3. Output capacitor orders of magnitude too small

A switching converter at a few kHz into a real load needs **tens of µF** of output
cap. A `100n` on the output is ~500× too small — the output is essentially chopped
DC. Sanity-check C_out against ripple (`ΔV = ΔI / (8·f·C)`), and cross-check against
the sibling board (buck v1 uses 47 µ). Same goes for a missing input bulk cap on a
rail fed through long cables from another board.

## 4. Optocoupler isolation quietly defeated

If the point of the opto is to isolate the MCU/control side from the power ground,
then the LED-side return must go to the **isolated** ground (`GND_MCU`), and the
isolated connector's ground pin must actually be wired. If the LED cathode lands on
power `GND`, or the header's ground pin is left dangling, the two domains share ground
and the opto isolates nothing. Check both sides of the opto in the netlist.

## 5. Footprint sanity (SMD on a THT process)

Teammates' schematics often arrive with default SMD footprints (SOIC-8, TSOT-23,
solder-wire pads). These can't be built on the laser THT flow. Re-assign per
`footprints.md`. This isn't an electrical bug but it'll stop the board cold at PCB
stage, so flag it during review.

## 6. Symbol pin numbers vs physical pads

Generic symbols can carry pin numbers that don't match the chosen package. The big
one: a generic optocoupler symbol numbered 1–4 mapped onto a 4N25 DIP-6, where
emitter is pin 4 and collector pin 5 — without renumbering, the netlist puts the
collector on the emitter pad. Also `Device:Q_NMOS` (G/D/S) vs TO-220 pads (1/2/3) —
`pcb_build.py` maps that one, but new symbols with letter pins need the same care.
After any renumber, re-dump the netlist and confirm the pins landed where intended.

## What "done" looks like

ERC 0 errors (benign: `lib_symbol_mismatch` from extends-flattening, single-pin
`global_label_dangling`). Power path traced and every part sees the voltage it
expects. Footprints all THT. Then it's safe to send to the PCB pipeline. When you fix
a non-obvious thing (like the floating gate-drive domain), **leave a short note on
the schematic sheet** so the design intent survives the next editor.
