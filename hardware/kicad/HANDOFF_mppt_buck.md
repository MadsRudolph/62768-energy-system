# HANDOFF — convert the MPPT into a switching BUCK (PV → 5 V store)

**For:** the Claude Code session that already rebuilt **boost_v2** and **buck_v2** with the
IR2110 gate driver (you have the schbuild/generator + IR2110 context). This task adds a
**third converter**: a proper switching **buck for the MPPT path**, replacing the existing
**linear** MPPT.

**Repo:** `C:\Users\Mads2\DTU\4. Semester\Electrical Energy Systems\team` (own git repo).
**Process:** xTool fiber-laser, single-sided, THT only, **track 1.0 mm / clearance 0.8 mm**,
104×104 mm board / 109×109 mm blank. No AI attribution in commits/code/docs.

> The main buck (`buck_v2`) is being finalized in a parallel session — **don't touch
> `boards/buck/buck_v2/`**. Your job is the **MPPT buck** only.

---

## 0. Read first

- `report/sections/solcelle-mppt.tex` — PV measurements + the stated design: *"the Arduino
  adjusts the duty cycle of the **buck converter** using Perturb and Observe."* The buck is
  the intended MPPT; the linear board is outdated.
- `hardware/kicad/boards/mppt/` — the **current MPPT = LINEAR** (TIP41A pass transistor +
  LM358 servo + 5.1 V zener + 3×4700 µ). This is what the buck replaces. Read it for the
  PV-side bulk caps and connector conventions, but the control stage is being dropped.
- `hardware/kicad/boards/buck/buck_v2/buck_v2.kicad_sch` — the **reference design** you
  reuse: high-side IR2110 buck (HO + bootstrap). The MPPT buck is this minus the NE555.
- `hardware/kicad/tools/schbuild.py` + `tools/generators/` (`buck_build.py`,
  `build_boost_v2.py`, `patch_buck_v2_ir2110.py`) — the generator toolchain. Use it.
- `hardware/kicad/HANDOFF_buck_boost_ir2110.md` + `hardware/kicad/AUDIT_buck_boost_ir2110.md`
  — the IR2110 architecture, pinout, footprint rules, and verification method. All apply.

---

## 1. What to build

A **synchronous-rectifier-free (diode) buck**, high-side switch, driven by the **Arduino's
PWM** through the opto → IR2110, stepping the PV panel down into the 5 V store. **No on-board
control loop and no NE555** — the duty is set entirely by the Arduino running Perturb &
Observe. PV voltage/current sensing is **external** (INA219 module per the report), so the
board is just the power stage + gate driver + PV input cap.

**Make a new board** `hardware/kicad/boards/mppt_buck/mppt_buck.kicad_{sch,pcb,pro}` (keep
the linear `mppt` board as history, same as buck/buck_v2).

### PV panel (measured — from solcelle-mppt.tex)

| Voc | Isc | V_MPP | I_MPP | P_MPP |
|---|---|---|---|---|
| 20.3 V | 0.60 A | **17.6 V** | **0.57 A** | **~10 W** |

### Operating point

- Input: PV, regulated by P&O to **~17.6 V** (ranges to Voc 20.3 V open-circuit).
- Output: **5 V** store (1 F supercap).
- Duty D = Vout/Vin = 5/17.6 ≈ **0.28** (0.25 at Voc).
- **Output current ≈ P/Vout = 10/5 = ~2 A into the store** (this is the key difference from
  buck_v2 — size the power parts for ~2 A, not the lighter main-buck load).

---

## 2. ⚠️ Power sizing — the real design work (do the math, don't copy buck_v2's parts blindly)

1. **Freewheel diode — UPGRADE from 1N5819.** 1N5819 is **1 A**; this buck runs ~2 A. Use a
   **≥3 A Schottky** (e.g. **1N5822** 3 A / 40 V, or SB560). Bigger package → bigger
   footprint (DO-201AD `D_DO-201AD_P15.24mm_Horizontal` or a TO-220 Schottky). Confirm the
   footprint exists on disk before assigning.
2. **MOSFET** — IRF530 (100 V, ~14 A) is fine for 20 V / 2 A. Keep TO-220 LaserPads.
   Add a heatsink note if needed (likely fine at 2 A with low Rds(on)).
3. **Inductor** — size for the chosen switching frequency and a sensible ripple
   (ΔI_L ≈ 30 % of 2 A ≈ 0.6 A):
   `L = Vout·(Vin−Vout) / (ΔI_L · f · Vin)`. At Vin=17.6, Vout=5, ΔI=0.6 A:
   - f = 31 kHz → L ≈ 174 µH; f = 62 kHz → L ≈ 87 µH.
   The hand-wound toroid must be rated for **≥2.5 A peak without saturating** — verify the
   core/wire. Re-use the `energy_system:L_Toroid…LaserPads` footprint only if the physical
   toroid matches (measure: pitch 28.2 mm c-c, drill 2.0 mm — or re-measure the real one).
4. **Input capacitor (PV side)** — needed to supply the switch's pulsed current and hold the
   PV at MPP. **Voltage rating ≥ 25 V** (Voc 20.3 V). The linear MPPT used 3×4700 µ/50 V —
   reuse a substantial bulk (≥470 µ/25 V) plus a small ceramic. **MEASURE the real cap's
   pitch/diameter** (see the C6 lesson in §6).
5. **Output capacitor** — the 1 F store is the bulk; add a small local output cap (e.g.
   47 µ) at the inductor/output node.
6. **Switching frequency** — Arduino-limited. Mega 2560 timers do ~31 kHz (or ~62.5 kHz with
   timer config). **Confirm the actual MCU + PWM frequency with the user/parallel session
   before finalizing L** (the project's PWM source — see `docs/mega-pinmap.md`,
   memory note "Mega codegen state").

---

## 3. Gate driver — identical pattern to buck_v2 (high-side, copy it)

`opto → IR2110 HO + bootstrap`, driven by Arduino PWM. **No 555.** IR2110 pinout (confirmed
in the audit): 1=LO(NC) 2=COM 3=VCC 5=VS 6=VB 7=HO 9=VDD 10=HIN 11=SD 12=LIN 13=VSS.

High-side usage: **VS→SW, VB=bootstrap (D_boot from +15V, C_boot to SW), HO→R_gate→GATE,
HIN=control (from opto), LIN=GND, SD=GND.** Gate pulldown to **SW** (not GND).

Opto: CNY17 on the `Isolator:4N25` symbol (or `Optocoupler_DC_PhotoNPN_AKEC`), pins
1=LED-A, 2=LED-K(→GND_MCU), 5=collector(→+15V), 4=emitter(→HIN, with 1 k pulldown).

---

## 4. Net spec — ready-to-paste schbuild `comps` (high-side buck, Arduino PWM)

CNY17 on the 4N25 symbol. Freewheel diode shown as `1N5822` on a ≥3 A footprint — **verify
the footprint name on disk and swap if needed.** Bootstrap cap value/footprint: **measure
the real part** (don't repeat the C6 mistake — see §6).

```python
import schbuild
FP_R   = "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal"
FP_TERM= "TerminalBlock:TerminalBlock_bornier-2_P5.08mm"
FP_HDR = "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical"
FP_DIP6= "Package_DIP:DIP-6_W7.62mm_LongPads"
FP_DIP14="Package_DIP:DIP-14_W7.62mm_LongPads"
FP_TO  = "energy_system:TO-220-3_Vertical_LaserPads"
FP_TOR = "energy_system:L_Toroid_Vertical_L34.5mm_W15.0mm_P28.20mm_LaserPads"
FP_CP  = "Capacitor_THT:CP_Radial_D8.0mm_P3.50mm"   # verify against real caps (measure!)
FP_CDISC="Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm"
FP_DO41= "Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal"
FP_DO201="Diode_THT:D_DO-201AD_P15.24mm_Horizontal"  # for the ~3A Schottky — verify on disk
FP_DO35= "Diode_THT:D_DO-35_SOD27_P7.62mm_Horizontal" # 1N4148 boot/gate diodes

comps = [
  # --- power stage (high-side buck: PV -> SW -> L -> 5V store) ---
  {"lib":"Connector:Screw_Terminal_01x02","ref":"J1","val":"PV ind","fp":FP_TERM,"x":45,"y":60,"nets":{"1":"VPV","2":"GND"}},
  {"lib":"Device:C_Polarized","ref":"C1","val":"470u/25V","fp":FP_CP,"x":60,"y":60,"nets":{"1":"VPV","2":"GND"}},   # PV bulk; >=25V, MEASURE
  {"lib":"Device:Q_NMOS","ref":"Q1","val":"IRF530","fp":FP_TO,"x":80,"y":58,"nets":{"D":"VPV","G":"GATE","S":"SW"}}, # high-side
  {"lib":"Device:D_Schottky","ref":"D1","val":"1N5822","fp":FP_DO201,"x":95,"y":68,"ang":270,"nets":{"1":"SW","2":"GND"}}, # freewheel: K=SW,A=GND; >=3A
  {"lib":"Device:L","ref":"L1","val":"150u","fp":FP_TOR,"x":110,"y":58,"ang":90,"nets":{"1":"SW","2":"VOUT_5V"}},   # size per f (sec.2)
  {"lib":"Device:C_Polarized","ref":"C2","val":"47u","fp":FP_CP,"x":125,"y":60,"nets":{"1":"VOUT_5V","2":"GND"}},
  {"lib":"Connector:Screw_Terminal_01x02","ref":"J2","val":"lager ud (5V)","fp":FP_TERM,"x":145,"y":60,"ang":180,"nets":{"1":"VOUT_5V","2":"GND"}},
  # --- gate driver (opto -> IR2110 HO + bootstrap), PWM from Arduino ---
  {"lib":"Connector_Generic:Conn_01x02","ref":"J3","val":"PWM (Arduino)","fp":FP_HDR,"x":40,"y":110,"nets":{"1":"PWM","2":"GND_MCU"}},
  {"lib":"Device:R","ref":"R1","val":"200","fp":FP_R,"x":55,"y":110,"nets":{"1":"PWM","2":"OPTO_A"}},
  {"lib":"Isolator:4N25","ref":"U1","val":"CNY17","fp":FP_DIP6,"x":80,"y":110,"nets":{"1":"OPTO_A","2":"GND_MCU","5":"+15V","4":"HIN"}},
  {"lib":"Device:R","ref":"R2","val":"1k","fp":FP_R,"x":100,"y":125,"nets":{"1":"HIN","2":"GND"}},        # HIN pulldown
  {"lib":"Driver_FET:IR2110","ref":"U2","val":"IR2110","fp":FP_DIP14,"x":125,"y":108,"nets":{
       "9":"+15V","3":"+15V","13":"GND","2":"GND","12":"GND","11":"GND","10":"HIN","7":"HO","6":"VB","5":"SW"}},
  {"lib":"Device:R","ref":"R3","val":"10","fp":FP_R,"x":150,"y":108,"nets":{"1":"HO","2":"GATE"}},        # series gate R
  {"lib":"Diode:1N4148","ref":"D3","val":"1N4148","fp":FP_DO35,"x":150,"y":118,"nets":{"1":"HO","2":"GATE"}}, # anti-parallel
  {"lib":"Device:R","ref":"R4","val":"1k","fp":FP_R,"x":165,"y":118,"nets":{"1":"GATE","2":"SW"}},        # gate pulldown -> SW (high-side ref)
  {"lib":"Diode:1N4148","ref":"D2","val":"1N4148","fp":FP_DO35,"x":138,"y":92,"nets":{"1":"VB","2":"+15V"}}, # boot diode: K=VB, A=+15V
  {"lib":"Device:C","ref":"C3","val":"1u","fp":FP_CDISC,"x":150,"y":95,"nets":{"1":"VB","2":"SW"}},        # boot cap VB->SW; MEASURE/verify value+fp
  {"lib":"Device:C_Polarized","ref":"C4","val":"22u","fp":FP_CP,"x":110,"y":92,"nets":{"1":"+15V","2":"GND"}},
  {"lib":"Device:C","ref":"C5","val":"100n","fp":FP_CDISC,"x":122,"y":92,"nets":{"1":"+15V","2":"GND"}},
  {"lib":"Connector:Screw_Terminal_01x02","ref":"J4","val":"drive +15V","fp":FP_TERM,"x":40,"y":92,"nets":{"1":"+15V","2":"GND"}},
]
ncs = [  # IR2110 unused: LO(1), NC 4/8/14  +  CNY17 NC/base 3/6
  ("Driver_FET:IR2110","1",125,108,0,1), ("Driver_FET:IR2110","4",125,108,0,1),
  ("Driver_FET:IR2110","8",125,108,0,1), ("Driver_FET:IR2110","14",125,108,0,1),
  ("Isolator:4N25","3",80,110,0,1), ("Isolator:4N25","6",80,110,0,1),
]
globals_ = {"PWM","+15V","GND","GND_MCU","VPV","VOUT_5V","SW"}
schbuild.build("MPPT buck  PV 17.6V -> 5V store  (Arduino P&O, IR2110 high-side)",
               "energy_system",comps,ncs,globals_,
               "boards/mppt_buck/mppt_buck.kicad_sch")
```

**Acceptance net checks (must hold):**
- High-side: `VS(U2.5) ∈ SW`, `VB = {D2.K, C3(VB), U2.6}`, `D2 anode ∈ +15V`, `HO → R3 → GATE`.
- Opto emitter on **HIN** (`U1.4 ∈ HIN, ∉ GATE`), LIN(12) & SD(11) → GND.
- Buck freewheel: `D1` cathode→SW, anode→GND. Inductor SW→VOUT_5V. Q1 drain→VPV, source→SW.
- Gate pulldown R4 → **SW** (not GND).

---

## 5. Pipeline (same as boost_v2/buck_v2)

1. Write `tools/generators/build_mppt_buck.py` from §4, run `py -3.13 build_mppt_buck.py`.
2. **Verify by netlist** (the real check):
   ```powershell
   $kc="C:\Program Files\KiCad\9.0\bin\kicad-cli.exe"
   & $kc sch erc -o "$env:TEMP\m.erc" --severity-error --exit-code-violations ...\mppt_buck.kicad_sch   # expect 0
   & $kc sch export netlist --format kicadsexpr -o "$env:TEMP\m.net" ...\mppt_buck.kicad_sch
   py -3.13 <skill>\scripts\pcb_netlist_json.py "$env:TEMP\m.net" "$env:TEMP\m.json"
   ```
   Confirm §4 net membership, no null/SMD footprints, then DRC after routing.
3. Route + export:
   ```powershell
   <skill>\scripts\route_board.ps1 -Sch ...\mppt_buck.kicad_sch -Pcb ...\mppt_buck.kicad_pcb
   <skill>\scripts\export_production.ps1 -Pcb ...\mppt_buck.kicad_pcb -OutDir ...\production\mppt_buck
   ```
   If it won't fit 104×104, add a `PLACE` entry in `pcb_build.py` (the ~3 A diode + toroid +
   bulk cap are the big parts).
4. **Acceptance:** ERC 0, netlist == §4, high-side bootstrap present, 0 unconnected pads,
   0 vias, DRC only `track_dangling`/`silk_*`, `.kicad_pro` netclass 0.8/1.0, all THT.
5. Update `bom/footprint_map.csv` (+ `bom_to_md.py`) and `PCB_RESULTS.md`. Commit
   developer-voice, no AI attribution. **Stage by explicit path** (don't sweep unrelated WIP;
   don't touch `boards/buck/buck_v2/` or `boards/boost/`).

---

## 6. Gotchas carried over (these already bit us — heed them)

1. **MEASURE the real caps before trusting footprints.** On buck_v2 the 8n2 was a 9.3 mm box
   film, not a 5 mm disc, and the 47 µF was 4 mm pitch not 3.5 mm. **Have the user caliper
   the MPPT input bulk cap, the boot cap, and any film caps**, then set footprints to match
   (custom `energy_system` footprints if needed). Don't assume.
2. **High-side bootstrap is mandatory** — VS→SW, VB cap, boot diode. Driving the gate from
   LO/ground-ref makes a source-follower that overheats. (Audit §6.1, §8.2.)
3. **Don't use `tools/generators/add_optocoupler.py`** — it's the old bare-4N25 drive.
4. **Script-built boards aren't UUID-linked to the GUI.** If the user opens it in KiCad and
   runs "Update PCB from Schematic", it must use **"Re-link footprints by reference"** or it
   **duplicates every part**. For a single footprint change, use pcbnew **Change Footprint**
   directly, not F8. (This corrupted buck_v2 once — schematic lost the IR2110 on a GUI
   re-save; recover from git, re-verify U-refs present.)
5. **Bootstrap refresh:** the high-side bootstrap cap recharges while SW is low (diode
   conducting). At D≈0.28 there's plenty of low-time, but confirm min off-time at the chosen
   frequency keeps C_boot topped up.
6. **Sensing is external** (INA219 inline on PV+). The board only needs PV-in / store-out /
   PWM-in / +15 V. No on-board feedback — duty comes from the Arduino's P&O.

---

## 7. Open questions to resolve with the user before finalizing

- **Switching frequency / MCU** — what PWM frequency will the Arduino actually output? Sets L.
- **Caliper measurements** of the PV bulk cap, boot cap, freewheel-diode package.
- **Toroid current rating** — does the available hand-wound core handle ~2.5 A peak?
- Reuse the linear MPPT's 3×4700 µ bulk on the PV side, or a smaller dedicated input cap?
