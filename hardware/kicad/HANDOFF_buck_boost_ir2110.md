# HANDOFF — redesign buck & boost with on-board IR2110 gate driver

**For:** a fresh Claude Code session (with the `kicad-laser-pcb` skill) that will design the
schematics and build the laser PCBs for **buck_v2** and **boost_v2**, each with an
integrated `opto → IR2110 → MOSFET` gate driver.

**Repo:** `C:\Users\Mads2\DTU\4. Semester\Electrical Energy Systems\team` (its own git repo).
**Course:** DTU 62768. **Process:** xTool fiber-laser, single-sided, through-hole only.

---

## 0. First actions (do these before anything else)

1. **Invoke the skill:** it carries the whole pipeline + every gotcha. Ask/trigger
   `kicad-laser-pcb` ("build the boost PCB / route this board"). Read its `SKILL.md`,
   `references/footprints.md`, `references/routing.md`, `references/gotchas.md`.
2. **Read these repo files** (they are the design authority — do not contradict them):
   - `docs/system-architecture.md` — **the buck is high-side, the boost is low-side.** This
     changes which IR2110 output you use. Re-read §"Gate-drive reminder" before wiring.
   - `docs/lab-guides/Exp 3A.pdf` — the reference drive circuit (`opto → IR2110 → MOSFET`).
   - `hardware/kicad/WORKFLOW.md` — the full schematic→placed→route→export pipeline.
   - `hardware/kicad/boards/drive_circuit/drive_circuit.kicad_sch` — a **working, GUI-made
     IR2110 + opto gate driver**. This is the block you reuse. (It's the Exp 3A motor drive:
     IR2110 + ILD74 + IRF540N + motor — copy the driver half, drop the motor.)
   - `hardware/kicad/boards/boost/boost.kicad_sch` — the current boost (power stage to keep +
     the **old, inadequate** 4N25 gate drive to replace).
   - `hardware/kicad/boards/buck/buck.kicad_sch` and `boards/buck/buck_v2/buck_v2.kicad_sch`
     — inspect to confirm the buck power topology (high-side switch) before redesigning.
   - `hardware/kicad/tools/schbuild.py` + `tools/generators/` — **the schematic generator
     that built every board.** You generate boost_v2/buck_v2 with this, not by hand (see §5b).
3. **Hard repo rules (from `CLAUDE.md`):** never add AI attribution to commits/code/docs;
   `.kicad_sch` is source of truth (don't blow it away with generator scripts);
   PCB design rules are fixed at **track 1.0 mm / clearance 0.8 mm** — don't lower them.

---

## 1. Why we're doing this (the discovery)

The boost board was built with a **4N25 optocoupler driving the MOSFET gate directly**
(opto emitter → gate, 10 kΩ pulldown). We bench-tested it (5 V → ~10 V worked), but the
4N25's **~20 µs turn-off (storage time)** stretches the duty badly: a commanded 20 % became
**65 % at 10 kHz**. It's only usable down around **1–2 kHz**, which forces large output
ripple (~1 V pk-pk on 10 V).

Swapping the opto (CNY17, MCT6, etc.) does **not** fix it — they're all phototransistor
optos with the same slow turn-off. The real fix, and what the **system architecture
intends**, is a proper **gate-driver IC (IR2110)**: the opto only passes the logic PWM
(isolation), and the IR2110 slams the gate high *and* low in tens of ns. That allows
20–50 kHz with clean duty and small ripple.

`docs/system-architecture.md` (lines ~83–96) already says each converter has **its own
opto + IR2110 gate driver**. The buck/boost boards just never implemented the IR2110 — that's
the bug we're fixing.

---

## 2. The reference gate-driver block (copy this from `drive_circuit`)

Proven, GUI-made, in `drive_circuit.kicad_sch`. Chain:

```
PWM → R(200Ω) → OPTO(LED) ┊isolation┊ OPTO(transistor) → IR2110 LIN/HIN → IR2110 LO/HO → R_gate(10Ω) → MOSFET gate
                                                                            (+ 1N4007 across R_gate, 1kΩ gate pulldown)
```

**IR2110 pinout (DIP-14, symbol `Driver_FET:IR2110`)** — confirmed from the drive_circuit
netlist:

| Pin | Name | Low-side use (boost) | High-side use (buck) |
|----|------|----------------------|----------------------|
| 1 | LO | → R_gate → gate | unused |
| 2 | COM | GND | GND |
| 3 | VCC | +15 V | +15 V |
| 5 | VS | GND | **→ SW node (MOSFET source)** |
| 6 | VB | unused | **bootstrap cap top (→VS), boot diode cathode** |
| 7 | HO | unused | **→ R_gate → gate** |
| 9 | VDD | +15 V | +15 V |
| 10 | HIN | GND (tie low) | **→ control (from opto)** |
| 11 | SD | GND (must be low = not shutdown) | GND |
| 12 | LIN | **→ control (from opto)** | GND (tie low) |
| 13 | VSS | GND | GND |
| 4, 8, 14 | NC | leave open | leave open |

Decoupling on +15 V (from drive_circuit): **22 µF** (`C_Polarized`) + **100 nF** (`C` disc),
both to GND.

---

## 3. ⚠️ The one thing you must get right: boost = LOW-side, buck = HIGH-side

- **boost_v2:** M1 source = GND → **low-side**. Use IR2110 **LO (pin 1)**. VS (pin 5) = GND.
  **No bootstrap.** Simple. (This is the same as the drive_circuit motor switch.)
- **buck_v2:** the MOSFET source = the switching node (SW), which swings up to V1 (~15 V) →
  **high-side**. You MUST use IR2110 **HO (pin 7)** with **VS (pin 5) → SW** and a
  **bootstrap**: diode VCC(3)→VB(6) + cap VB(6)→VS(5). The control signal goes to **HIN
  (pin 10)**, and **LIN (12) tied low**. Driving a high-side MOSFET from LO makes it a
  source-follower that runs hot and never fully turns on (see architecture doc §gate-drive).

Bootstrap parts (typical): boot diode = **1N4148/1N4007** fast-ish small diode VCC→VB;
boot cap = **0.1–1 µF** ceramic/film VB→VS. Confirm against the IR2110 datasheet
(`docs/datasheets/` — add if missing) and justify in the report (Exp 3A task 3).

---

## 4. boost_v2 — full netlist spec (LOW-side, ready to build)

Make a new board `hardware/kicad/boards/boost/boost_v2/boost_v2.kicad_sch` (mirrors the
`buck/buck_v2/` pattern; keep the original boost intact). Use the **CNY17** opto (the team
standardized on it) — use the **`Isolator:4N25` symbol** with value `CNY17` (identical
6-pin pinout: 1=LED-A, 2=LED-K, 3=NC, 4=emitter, 5=collector, 6=base), footprint
`Package_DIP:DIP-6_W7.62mm_LongPads`.

**Components**

| Ref | Symbol (lib_id) | Value | Footprint |
|---|---|---|---|
| J_IN | `Connector:Screw_Terminal_01x02` | lager ind (5V) | `TerminalBlock:TerminalBlock_bornier-2_P5.08mm` |
| L1 | `Device:L` | 470u | `energy_system:L_Toroid_Vertical_L34.5mm_W15.0mm_P28.20mm_LaserPads` |
| M1 | `Device:Q_NMOS` | IRF530 | `energy_system:TO-220-3_Vertical_LaserPads` |
| D1 | `Device:D_Schottky` | 1N5819 | `Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal` |
| C_OUT | `Device:C_Polarized` | 47u | `Capacitor_THT:CP_Radial_D8.0mm_P3.50mm` |
| J_OUT | `Connector:Screw_Terminal_01x02` | V2 ud (10V) | `TerminalBlock:TerminalBlock_bornier-2_P5.08mm` |
| J_PWM | `Connector_Generic:Conn_01x02` | PWM (isoleret) | `Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical` |
| J_15V | `Connector:Screw_Terminal_01x02` | drive +15V | `TerminalBlock:TerminalBlock_bornier-2_P5.08mm` |
| R_LED | `Device:R` | 200 | `Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal` |
| R_LIN | `Device:R` | 1k | (same axial R) |
| R_G | `Device:R` | 10 | (same axial R) |
| R_GS | `Device:R` | 1k | (same axial R) |
| U_OPTO | `Isolator:4N25` | CNY17 | `Package_DIP:DIP-6_W7.62mm_LongPads` |
| U_DRV | `Driver_FET:IR2110` | IR2110 | `Package_DIP:DIP-14_W7.62mm_LongPads` |
| C_BYP1 | `Device:C_Polarized` | 22u | `Capacitor_THT:CP_Radial_D8.0mm_P3.50mm` |
| C_BYP2 | `Device:C` | 100n | `Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm` |
| D_G | `Diode:1N4007` | 1N4007 | `Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal` |

**Nets** (pin refs: opto pins per 4N25/CNY17 numbering; IR2110 pins per the table in §2)

| Net | Members |
|---|---|
| VIN_5V | J_IN.1, L1.1 |
| SW | L1.2, M1.D, D1.2(A) |
| VOUT_V2 | D1.1(K), C_OUT.1, J_OUT.1 |
| GATE | M1.G, R_G.2, D_G.2(A), R_GS.1 |
| GDRV (LO) | U_DRV.1 (LO), R_G.1, D_G.1(K) |
| LIN | U_DRV.12 (LIN), U_OPTO.4 (emitter), R_LIN.1 |
| +15V | U_DRV.9 (VDD), U_DRV.3 (VCC), U_OPTO.5 (collector), C_BYP1.1, C_BYP2.1, J_15V.1 |
| OPTO_LED_A | R_LED.2, U_OPTO.1 (LED anode) |
| PWM | J_PWM.1, R_LED.1 |
| GND_MCU | J_PWM.2, U_OPTO.2 (LED cathode) |
| GND | J_IN.2, J_OUT.2, J_15V.2, M1.S, C_OUT.2, R_GS.2, R_LIN.2, C_BYP1.2, C_BYP2.2, U_DRV.2 (COM), U_DRV.5 (VS), U_DRV.10 (HIN), U_DRV.11 (SD), U_DRV.13 (VSS) |

**Isolation preserved:** `GND_MCU` (PWM side) is separate from power `GND`. The CNY17
bridges them optically. (On the bench, using one AD3 for both PWM-gen and scope ties them
together through the AD3 — that's fine, just be aware.)

Add a `PWR_FLAG` (`power:PWR_FLAG`) on `+15V`, `VIN_5V`, and `GND` to keep ERC clean.

---

## 5. buck_v2 — spec (HIGH-side, needs verification first)

The existing `buck_v2` has an on-board 555 PWM and (per the summary) was bug-fixed earlier.
The task here is to give the buck the **same IR2110 driver**, but **high-side**:

1. **Inspect** `boards/buck/buck.kicad_sch` + `boards/buck/buck_v2/buck_v2.kicad_sch`.
   Confirm the switch MOSFET source = SW node (high-side). Identify V1-in (~15 V), SW, the
   L-C-D output stage, and the existing control/PWM source.
2. Replace the existing gate drive with the **IR2110 high-side** chain from §2/§3:
   opto → HIN, **HO → R_G → gate**, **VS → SW**, bootstrap diode VCC→VB + cap VB→VS,
   LIN tied low, SD low.
3. Decide the control source: keep the on-board 555, OR feed external PWM through the opto
   like the boost. **Match whatever the team wants** — ask the user. Either way the IR2110
   does the gate driving.
4. Same parts/footprints table as §4 for the driver block (add the bootstrap diode + cap).
5. The buck MOSFET is `IRF530`/`IRF540N` (TO-220 LaserPads). Freewheel/rectifier diode per
   the existing buck design.

**Do not** copy the boost's low-side wiring onto the buck — the high-side bootstrap is
mandatory or the MOSFET overheats.

---

## 5b. Generate the schematics with `schbuild.py` — DO THIS (don't hand-author)

The repo already has the schematic generator that built every other board. **Use it.**

- `hardware/kicad/tools/schbuild.py` — the generic builder. One call:
  `schbuild.build(title, project, comps, ncs, globals_, out)`.
  - It **auto-reads pin coordinates** from the stock KiCad symbol libs (no hand pin tables),
    **sets the Footprint property**, places parts on a 2.54 mm grid, and wires connectivity by
    **net labels** (so the netlist is correct even if the layout looks rough).
  - `comps`: list of dicts `{"lib":lib_id, "ref":..., "val":..., "fp":footprint,
    "x":mm, "y":mm, "ang":0/90/180/270, "nets":{pin:netname}}`.
  - `ncs`: no-connects `[(lib_id, pin, x, y, ang, unit), ...]`.
  - `globals_`: set of net names to emit as global labels.
- **Templates to copy:**
  - `tools/generators/build_drive.py` — the **low-side `opto → IR2110 → MOSFET`** chain.
    This IS the boost_v2 driver (swap ILD74→CNY17, motor→boost power stage). NOTE: build_drive.py
    uses its own inline `build()` and leaves footprints empty — prefer `schbuild.build` which
    sets footprints. Use build_drive.py only as the wiring reference.
  - `tools/generators/buck_build.py` — the **high-side** buck power stage (M1 source = SW).
- **⚠️ Do NOT use `tools/generators/add_optocoupler.py`.** It injects the OLD bare-4N25
  gate drive (the slow design we're replacing). The whole point of v2 is the IR2110.

Write `tools/generators/build_boost_v2.py` (and a buck variant) and run
`py -3.13 build_boost_v2.py`. The verified boost_v2 component/net spec is below — it maps
1:1 onto `schbuild.build`.

### boost_v2 — ready-to-paste `comps` (LOW-side, IR2110 LO, CNY17 opto)

CNY17 uses the `Isolator:4N25` symbol (same 6-pin: 1=LED-A, 2=LED-K, 4=emitter, 5=collector,
6=base). `R_G` (10 Ω) in series LO→GATE with `D_G` (1N4007) anti-parallel (anode=GATE,
cathode=LO) for fast turn-off — this matches the proven `drive_circuit` board.

```python
import schbuild
FP_R   = "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal"
FP_TERM= "TerminalBlock:TerminalBlock_bornier-2_P5.08mm"
FP_HDR = "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical"
FP_DIP6= "Package_DIP:DIP-6_W7.62mm_LongPads"
FP_DIP14="Package_DIP:DIP-14_W7.62mm_LongPads"
FP_TO  = "energy_system:TO-220-3_Vertical_LaserPads"
FP_TOR = "energy_system:L_Toroid_Vertical_L34.5mm_W15.0mm_P28.20mm_LaserPads"
FP_CP  = "Capacitor_THT:CP_Radial_D8.0mm_P3.50mm"
FP_CDISC="Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm"
FP_DO41= "Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal"

comps = [
  # --- power stage ---
  {"lib":"Connector:Screw_Terminal_01x02","ref":"J1","val":"lager ind (5V)","fp":FP_TERM,"x":50,"y":60,"nets":{"1":"VIN_5V","2":"GND"}},
  {"lib":"Device:L","ref":"L1","val":"470u","fp":FP_TOR,"x":75,"y":55,"ang":90,"nets":{"1":"VIN_5V","2":"SW"}},
  {"lib":"Device:Q_NMOS","ref":"M1","val":"IRF530","fp":FP_TO,"x":100,"y":60,"nets":{"G":"GATE","D":"SW","S":"GND"}},
  {"lib":"Device:D_Schottky","ref":"D1","val":"1N5819","fp":FP_DO41,"x":120,"y":50,"ang":180,"nets":{"2":"SW","1":"VOUT_V2"}},  # 1=K,2=A
  {"lib":"Device:C_Polarized","ref":"C1","val":"47u","fp":FP_CP,"x":135,"y":60,"nets":{"1":"VOUT_V2","2":"GND"}},
  {"lib":"Connector:Screw_Terminal_01x02","ref":"J2","val":"V2 ud (10V)","fp":FP_TERM,"x":160,"y":60,"ang":180,"nets":{"1":"VOUT_V2","2":"GND"}},
  # --- gate driver (opto -> IR2110 LO -> gate) ---
  {"lib":"Connector_Generic:Conn_01x02","ref":"J3","val":"PWM (isoleret)","fp":FP_HDR,"x":40,"y":110,"nets":{"1":"PWM","2":"GND_MCU"}},
  {"lib":"Device:R","ref":"R1","val":"200","fp":FP_R,"x":55,"y":110,"nets":{"1":"PWM","2":"OPTO_A"}},
  {"lib":"Isolator:4N25","ref":"U1","val":"CNY17","fp":FP_DIP6,"x":80,"y":110,"nets":{"1":"OPTO_A","2":"GND_MCU","5":"+15V","4":"LIN"}},
  {"lib":"Device:R","ref":"R2","val":"1k","fp":FP_R,"x":100,"y":125,"nets":{"1":"LIN","2":"GND"}},      # LIN pulldown
  {"lib":"Driver_FET:IR2110","ref":"U2","val":"IR2110","fp":FP_DIP14,"x":125,"y":110,"nets":{
       "9":"+15V","3":"+15V","13":"GND","2":"GND","5":"GND","10":"GND","11":"GND","12":"LIN","1":"LO"}},
  {"lib":"Device:R","ref":"R3","val":"10","fp":FP_R,"x":150,"y":110,"nets":{"1":"LO","2":"GATE"}},      # series gate R
  {"lib":"Diode:1N4007","ref":"D2","val":"1N4007","fp":FP_DO41,"x":150,"y":120,"nets":{"1":"LO","2":"GATE"}},  # anti-parallel (1=K=LO,2=A=GATE)
  {"lib":"Device:R","ref":"R4","val":"1k","fp":FP_R,"x":165,"y":125,"nets":{"1":"GATE","2":"GND"}},     # gate pulldown
  {"lib":"Device:C_Polarized","ref":"C2","val":"22u","fp":FP_CP,"x":110,"y":90,"nets":{"1":"+15V","2":"GND"}},
  {"lib":"Device:C","ref":"C3","val":"100n","fp":FP_CDISC,"x":125,"y":90,"nets":{"1":"+15V","2":"GND"}},
  {"lib":"Connector:Screw_Terminal_01x02","ref":"J4","val":"drive +15V","fp":FP_TERM,"x":40,"y":90,"nets":{"1":"+15V","2":"GND"}},
]
ncs = [  # IR2110 unused: HO,VB,NC,NC,NC  +  CNY17 NC/base
  ("Driver_FET:IR2110","7",125,110,0,1), ("Driver_FET:IR2110","6",125,110,0,1),
  ("Driver_FET:IR2110","4",125,110,0,1), ("Driver_FET:IR2110","8",125,110,0,1),
  ("Driver_FET:IR2110","14",125,110,0,1),
  ("Isolator:4N25","3",80,110,0,1), ("Isolator:4N25","6",80,110,0,1),
]
globals_ = {"PWM","+15V","GND","GND_MCU","VIN_5V","VOUT_V2","GATE"}
schbuild.build("Boost v2  5V->10V  (IR2110 gate drive)","energy_system",comps,ncs,globals_,
               "boards/boost/boost_v2/boost_v2.kicad_sch")
```

After generating: **the netlist below is the acceptance test** — export it and confirm every
net matches §4 exactly. Then footprints are already set (schbuild did it), so go straight to
the route/export pipeline. For **buck_v2**, do the same but high-side: copy `buck_build.py`'s
power stage, add the IR2110 with `7`→GATE (HO), `5`→SW (VS), bootstrap diode `+15V`→VB(6) +
cap VB(6)→SW, control on `10` (HIN), `12` (LIN)→GND. See §3/§5.

## 6. Build the PCB (the skill pipeline)

`<skill>` = the `kicad-laser-pcb` skill dir. `<proj>` = repo. KiCad 9 CLI at
`C:\Program Files\KiCad\9.0\bin`. Commands are PowerShell.

1. **Generate the schematic** with `schbuild.py` per §5b. (`.kicad_sch` = source of truth;
   the user can tidy the layout in the GUI afterward, but the generated netlist is already
   correct.)
2. **ERC + netlist verify** (the real correctness check):
   ```powershell
   $kc = "C:\Program Files\KiCad\9.0\bin\kicad-cli.exe"
   & $kc sch erc -o "$env:TEMP\b.erc" --severity-error --severity-warning <proj>\...\boost_v2.kicad_sch
   & $kc sch export netlist --format kicadsexpr -o "$env:TEMP\b.net" <proj>\...\boost_v2.kicad_sch
   py -3.13 <skill>\scripts\pcb_netlist_json.py "$env:TEMP\b.net" "$env:TEMP\b.json"
   ```
   Open `b.json` and confirm every net in §4 has exactly the listed members, no `null`
   footprints, no SMD package names (`SOIC`/`TSOT`). ERC bar: 0 errors (lib_symbol_mismatch
   + single-pin-dangling are benign).
3. **Place + route + export** (per `references/routing.md`):
   ```powershell
   <skill>\scripts\route_board.ps1 -Sch <proj>\...\boost_v2.kicad_sch -Pcb <proj>\...\boost_v2.kicad_pcb
   <skill>\scripts\export_production.ps1 -Pcb <proj>\...\boost_v2.kicad_pcb -OutDir <proj>\hardware\kicad\production\boost_v2
   ```
   If the cluster doesn't fit 104×104, add a `PLACE` entry in `<skill>\scripts\pcb_build.py`
   following the signal flow (examples in the file). Launch the assert-dialog dismisser first
   (gotchas.md). **Acceptance: 0 unconnected pads, 0 real DRC errors, no vias.**
4. **DXF export for the laser** (what we actually run): the etch file is
   `<board>.dxf` (B.Cu + Edge, **mirror in xTool**). For holes, a full-diameter circle file:
   ```powershell
   & $kc pcb export dxf --mode-single -l "Edge.Cuts" --ou mm --drill-shape-opt 2 -o "...\boost_v2_holes.dxf" ...\boost_v2.kicad_pcb
   ```
   (drill-shape-opt 2 = actual-diameter circles). Board outline 104×104; cut copper blank
   to **109×109 mm**.

---

## 7. Laser / board constraints (non-negotiable)

- Outline **104×104 mm**, copper blank **109×109 mm** (2.5 mm rim for the jig).
- **Track 1.0 mm, clearance 0.8 mm.** THT only. `*_LaserPads` footprints for TO-220; DIP
  `_LongPads`. No vias — single-sided B.Cu, F.Cu only for unavoidable wire-bridge crossings.
- Update `hardware/kicad/bom/footprint_map.csv` (board,schematic_ref,value,
  chosen_part_number,source,footprint,notes) with the new parts, then
  `py -3.13 <skill>\scripts\bom_to_md.py <path-to-footprint_map.csv>` to refresh `BOM.md`.

---

## 8. Parts / naming clarifications (we already resolved these)

- **CNY17** (6-pin) is a fine drive-circuit opto and what the team uses. Wire it: pin1=LED
  anode, pin2=LED cathode (→GND_MCU), pin5=collector (→+15V), pin4=emitter (→LIN/HIN). Use
  the `Isolator:4N25` symbol (same pinout).
- **MCT6 / ILD74** = dual phototransistor optos (8-pin) — also valid drive-circuit optos,
  just different pin numbers (transistor on 7/8 not 5/4).
- **IL300 is NOT the same as MCT6.** IL300 is a *linear* opto for the **feedback** circuit
  (with MCP601 op-amps) — do **not** use it in the gate driver.
- Common subs already worked out: `1N5819→1N5817`, `1N4007→1N4006`, `IRF530N→IRF530`,
  `LF50→LM7805`. TO-126 can't meet 0.8 mm → use TO-220.

---

## 9. Bench-test context (boost, the old 4N25 board) — for the report

- 5 V in → ~10.17 V out (V2 target) at ~16.5 % drain duty, 1 kHz, 5 V @ 0.4 A in. Worked,
  but only because of light-load **DCM** inflation; output sags with load.
- Output ripple ~1.1 V (11 %) at 1 kHz — the symptom that drove this redesign.
- Gate confirmed switching 0→~11 V via the 4N25, but duty stretched (20 %→65 % @ 10 kHz).
- Output cap (C1) had to be reflowed once (open joint made the output collapse each cycle).
- AD3 driver: `tools/ad3/boost_test.py` (drives W1 PWM + captures both scope ch in one
  session; probes are **10×**, use att=10). `tools/ad3/ad3_check.py` is the generic one.

After boost_v2 is built, re-test with the IR2110: expect clean duty tracking and far smaller
ripple at 20–50 kHz.

---

## 10. What NOT to do

- Don't lower track/clearance below 1.0/0.8 mm.
- Don't use `add_optocoupler.py` — it's the old bare-4N25 drive; v2 must use the IR2110.
- Don't drive the buck (high-side) from IR2110 LO — bootstrap + HO are mandatory.
- Don't regenerate a GUI-made `.kicad_sch` from a build script.
- Don't put an IL300 in the gate driver (it's for feedback).
- Don't add AI attribution to commits/code/docs; developer-voice commits only.
- Don't trust schematic correctness by eye — verify via the exported netlist JSON.
