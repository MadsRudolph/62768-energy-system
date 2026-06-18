# AUDIT — boost_v2, buck_v2 & mppt_buck IR2110 gate-driver work

**Purpose.** This document lets an independent reviewer (human or AI) validate the
boost_v2, buck_v2 **and mppt_buck** PCB work end-to-end **without trusting the author**. Every claim
below is paired with the exact command that produces the evidence and the pass
criterion. Work against the *current files on disk*; do not assume the author's
summaries are correct.

- **Repo:** `C:\Users\Mads2\DTU\4. Semester\Electrical Energy Systems\team` (own git repo)
- **Tooling:** KiCad 9.0 (`C:\Program Files\KiCad\9.0\bin`), Python 3.13 + `sexpdata`,
  Java 21, Freerouting 1.9.0 (`~/.freerouting/freerouting-1.9.0.jar`)
- **Skill used:** `kicad-laser-pcb` at `C:\Users\Mads2\.claude\skills\kicad-laser-pcb`
  (`<skill>` below). Scripts: `pcb_netlist_json.py`, `pcb_build.py`, `route_board.ps1`,
  `export_production.ps1`.
- **Scope of verification performed by author:** ERC, exported-netlist membership,
  footprint sanity (THT/no-null/no-SMD), placement overlap, and post-route DRC.
  **No bench/SPICE test was performed.** Electrical-behaviour claims (turn-off speed,
  threshold margins) are design-intent, not measured — see §8.

---

## 1. Overview

Both converters previously drove the power MOSFET gate **directly from a phototransistor
optocoupler**. The opto's slow turn-off (~20 µs storage time) stretches PWM duty badly
(measured on the old boost: commanded 20 % → 65 % at 10 kHz), forcing low switching
frequency and large ripple. The fix — already mandated by `docs/system-architecture.md`
§"Gate-drive reminder" — is a dedicated **IR2110** gate-driver IC. The opto now only
carries the logic-level PWM (isolation / level-shift); the IR2110 drives the gate hard
high *and* low in tens of ns.

| Board | Switch topology | IR2110 channel | Bootstrap | Control source |
|---|---|---|---|---|
| boost_v2 | **low-side** (M1 source = GND) | **LO** (pin 1) | none (VS = GND) | external PWM via opto |
| buck_v2 | **high-side** (Q1 source = SW) | **HO** (pin 7) | **required** (VB/VS) | on-board NE555 **or** external PWM (SW1 selects), via opto |

The boost_v2 schematic was generated fresh with `schbuild`. The buck_v2 schematic is a
**GUI-made file (source of truth)** that was edited surgically — the NE555 + trimmer +
DIP-switch front-end and the power stage were left untouched; only the gate-drive stage
(old 4N25 + floating 9 V battery) was replaced.

---

## 2. Reference facts the reviewer should independently confirm

### 2.1 IR2110 pinout (`Driver_FET:IR2110`, DIP-14)

| Pin | Name | Pin | Name |
|----|------|----|------|
| 1 | LO | 8 | NC |
| 2 | COM | 9 | VDD (logic supply) |
| 3 | VCC (gate-drive supply) | 10 | HIN |
| 4 | NC | 11 | SD (shutdown, active high) |
| 5 | VS (high-side return) | 12 | LIN |
| 6 | VB (high-side floating supply) | 13 | VSS (logic gnd) |
| 7 | HO | 14 | NC |

Confirm against the IR2110 datasheet (`docs/datasheets/`). **Critical checks:**
- **SD must be LOW** or the driver is disabled. Both boards tie SD → GND.
- **VIH (logic-high threshold)** scales with VDD. At VDD = 15 V, VIH ≈ 9.5 V. This is
  *why the opto is retained* — it level-shifts the 5 V/PWM up toward 15 V (see §8.1).

### 2.2 Optocoupler pinout (6-pin)

boost_v2 uses symbol `Isolator:4N25` with value **CNY17**; buck_v2 uses symbol
`Isolator:Optocoupler_DC_PhotoNPN_AKEC` with value **4N25**. Both expose the same
relevant pins: **1 = LED anode, 2 = LED cathode, 4 = emitter, 5 = collector** (pins
3/6 unused). Confirm both boards wire: anode ← series-R from PWM, cathode → PWM-side
ground, collector → +15 V, emitter → IR2110 input (HIN or LIN) with a pulldown to GND.

### 2.3 Laser-process design rules (non-negotiable)

Board 104×104 mm, copper blank 109×109 mm, **track 1.0 mm, clearance 0.8 mm**, THT only,
no vias (single-sided B.Cu; F.Cu only for unavoidable wire-bridge crossings). TO-220 and
the wound toroid use `energy_system:*_LaserPads`; DIPs use `*_LongPads`.

---

## 3. Files produced / changed

### 3.1 Team repo (the deliverables)

| Path | Status | What |
|---|---|---|
| `hardware/kicad/tools/generators/build_boost_v2.py` | new | schbuild generator for boost_v2 |
| `hardware/kicad/tools/generators/patch_buck_v2_ir2110.py` | new | surgical sexpdata patch for buck_v2 |
| `hardware/kicad/boards/boost/boost_v2/boost_v2.kicad_{sch,pcb,pro}` | new | board project |
| `hardware/kicad/boards/buck/buck_v2/buck_v2.kicad_{sch,pcb}` | modified | sch patched; pcb re-routed |
| `hardware/kicad/production/boost_v2/` | new | DXFs + gerbers + drill + layout svg |
| `hardware/kicad/production/buck_v2/` | modified | DXFs + gerbers + drill + layout svg |
| `hardware/kicad/bom/footprint_map.csv` | modified | +18 boost_v2 rows, +9 buck_v2 rows, −1 (battery) |
| `hardware/kicad/bom/BOM.md` | regenerated | from footprint_map.csv |
| `PCB_RESULTS.md` | modified | boost_v2 + buck_v2 status entries |

### 3.2 Local skill scripts (NOT in team repo — author-side bug fixes)

| Path | Change | Why |
|---|---|---|
| `<skill>/scripts/route_board.ps1` | `"$b:"` → `"${b}:"` (line ~61) | PowerShell parse error blocked all routing |
| `<skill>/scripts/export_production.ps1` | `"$b:"` → `"${b}:"` (line ~27) | same parse error blocked all export |
| `<skill>/scripts/pcb_build.py` | replaced stale `buck_v2` PLACE entry | old entry referenced removed J1 + missing 9 new refs (fails hard) |

**Reviewer note:** the skill fixes are real and reproducible (a `$b:` token is an
unconditional PS parse error). They are outside the team repo by design.

---

## 4. boost_v2 — specification & verification

### 4.1 Components (17)

`J1` screw-term (5 V in), `L1` 470 µ toroid, `M1` IRF530 (TO-220 LaserPads, low-side),
`D1` 1N5819 Schottky, `C1` 47 µ out, `J2` screw-term (V2 out), `J3` header (PWM, isolated),
`J4` screw-term (+15 V), `R1` 200 (LED), `U1` CNY17 opto, `R2` 1k (LIN pulldown),
`U2` IR2110, `R3` 10 (gate-R), `D2` 1N4007 (anti-parallel), `R4` 1k (gate pulldown),
`C2` 22 µ + `C3` 100 n (+15 V decoupling).

### 4.2 Net acceptance table (must match exactly)

| Net | Members |
|---|---|
| VIN_5V | J1.1, L1.1 |
| SW | D1.2, L1.2, M1.D |
| VOUT_V2 | C1.1, D1.1, J2.1 |
| GATE | D2.2, M1.G, R3.2, R4.1 |
| LO | D2.1, R3.1, U2.1 |
| LIN | R2.1, U1.4, U2.12 |
| +15V | C2.1, C3.1, J4.1, U1.5, U2.3, U2.9 |
| OPTO_A | R1.2, U1.1 |
| PWM | J3.1, R1.1 |
| GND_MCU | J3.2, U1.2 |
| GND | C1.2, C2.2, C3.2, J1.2, J2.2, J4.2, M1.S, R2.2, R4.2, U2.2, U2.5, U2.10, U2.11, U2.13 |

IR2110 (U2) **low-side** usage: VDD/VCC(9,3)=+15V; VSS/COM(13,2)=GND; **VS(5)=GND**;
**HIN(10)=GND, SD(11)=GND, LIN(12)=control**; **LO(1)=gate drive**; NC = 4,6,7,8,14.

### 4.3 Reproduce the boost_v2 checks

```powershell
$kc = "C:\Program Files\KiCad\9.0\bin\kicad-cli.exe"
$sch = "...\boards\boost\boost_v2\boost_v2.kicad_sch"
# (a) ERC — expect 0 errors
& $kc sch erc -o "$env:TEMP\b.erc" --severity-error --severity-warning $sch
# (b) netlist -> JSON -> membership (compare to §4.2)
& $kc sch export netlist --format kicadsexpr -o "$env:TEMP\b.net" $sch
py -3.13 <skill>\scripts\pcb_netlist_json.py "$env:TEMP\b.net" "$env:TEMP\b.json"
# (c) DRC on the routed board — expect 0 unconnected, only track_dangling
& $kc pcb drc -o "$env:TEMP\b.drc" "...\boards\boost\boost_v2\boost_v2.kicad_pcb"
```

Use `<skill>\scripts\pcb_netlist_json.py` then dump per-net members (script in §7) and
diff against §4.2.

### 4.4 Author's observed results (reproduce to confirm)

- ERC: **0 errors**, 3 warnings (2× `footprint_link_issues` for `energy_system` lib not
  registered in GUI lib-table — benign; 1× `lib_symbol_mismatch` on 1N4007 — benign).
- Netlist: **11 nets, all match §4.2**; 17 components, **no null footprints, no SMD**.
- DRC: **0 unconnected pads, 0 footprint errors, 1 `track_dangling`** (net /LO, 1.52 mm).
- Route: 17 F.Cu segments / 255 mm, **0 vias**.

---

## 5. buck_v2 — specification & verification

### 5.1 What changed vs. the original buck_v2

**Removed:** `J1` (9 V battery floating on SW); the `+9V_SW` net; the direct
opto-emitter→gate wire. **Relabelled:** opto collector net `+9V_SW` → `+15V`.
**Relocated:** `R4` (now gate→SW pulldown, split off the opto emitter).
**Added (10 refs):** `U4` IR2110, `D4` 1N4148 (bootstrap diode), `C7` 1 µ (bootstrap cap),
`R5` 10 (gate-R), `D5` 1N4148 (anti-parallel), `R6` 1k (HIN pulldown), `C8` 22 µ + `C9`
100 n (+15 V decoupling), `J5` screw-term (+15 V in), `#FLG03` PWR_FLAG.
**Untouched:** LM7805 (U1), NE555 (U2) + R1/R2/RV1/D1/D2/C3/C5/C6 timing, SW1 source
select, opto LED side (R3, U3 pins 1/2), power stage (Q1/D3/L1/C4), connectors J2/J3.

### 5.2 Gate-drive net acceptance table (must match exactly)

| Net | Members |
|---|---|
| HIN | R6.1, U3.4, U4.10 |
| HO | D5.1, R5.1, U4.7 |
| GATE | D5.2, Q1.G, R4.1, R5.2 |
| VB | C7.1, D4.1, U4.6 |
| +15V | C8.1, C9.1, D4.2, J5.1, U3.5, U4.3, U4.9 |
| SW | C7.2, D3.1, L1.1, Q1.S, R4.2, U4.5 |
| GND | C1.2, C2.2, C3.2, C4.2, C5.2, C6.2, C8.2, C9.2, D3.2, J2.2, J3.2, J5.2, R6.2, U1.2, U2.1, U3.2, U4.2, U4.11, U4.12, U4.13 |
| Rectifier (V1) | C1.1, Q1.D, U1.1 |

IR2110 (U4) **high-side** usage: VDD/VCC(9,3)=+15V; VSS/COM(13,2)=GND; **VS(5)=SW**;
**VB(6)=bootstrap node**; **HO(7)=gate drive**; **HIN(10)=control**; **LIN(12)=GND,
SD(11)=GND**; LO(1)=NC; NC = 1,4,8,14.

**Bootstrap topology (the high-side must-have):** `D4` anode=+15V (VCC), cathode=VB;
`C7` between VB and VS(=SW). Confirm: `VB = {C7.1, D4.1(K), U4.6}` and
`SW ⊇ {C7.2, U4.5(VS)}`.

**Emitter/gate split (the surgical core):** the opto emitter `U3.4` is on **HIN**, *not*
on GATE; the gate is driven from **HO via R5** (with D5 anti-parallel). Confirm `U3.4`
appears in HIN and **not** in GATE.

### 5.3 Front-end preservation (must be byte-for-byte identical to original)

These 12 nets must be unchanged from the pre-patch buck_v2:
`Net-(D1-A)`, `Net-(D1-K)`, `Net-(D2-A)`, `Net-(D2-K)`, `Net-(J2-Pin_1)`,
`Net-(J3-Pin_1)`, `Net-(R3-Pad1)`, `Net-(R3-Pad2)`, `Net-(U1-VO)`, `Net-(U2-CONT)`,
`Net-(U2-OUT)`, `Net-(U2-THRES)`. (Reviewer: `git show <pre-patch>:...buck_v2.kicad_sch`
→ netlist → diff the front-end nets.)

### 5.4 Author's observed results (reproduce to confirm)

- ERC: **0 errors**, warnings are `endpoint_off_grid` (pre-existing in the GUI file) +
  `lib_symbol_mismatch` (benign).
- Netlist: **20 nets, 31 components**, gate-drive nets match §5.2, front-end nets match
  §5.3, **no null footprints, no SMD**.
- Placement: cluster **91.6 × 94.6 mm** (≤ 98), **0 footprint overlaps** (all pairs
  ≥ 0.8 mm). The toroid L1 is **~35 × 35 mm** and was given its own quadrant.
- DRC: **0 unconnected pads, 0 footprint errors, 4 `track_dangling`** (3 micro-stubs +
  one 5.9 mm stub on `Net-(J3-Pin_1)`).
- Route: 21 F.Cu segments / 116 mm, **0 vias**.

### 5.5 Round-trip safety (buck_v2 is a GUI file)

The patch parses the GUI schematic with `sexpdata` and writes it back compact (KiCad
re-pretty-prints on next GUI save). Before editing, a load→dump→ERC round-trip was shown
to preserve the netlist **byte-identical** (17 nets identical) and add only benign
warnings. Reviewer can re-confirm by reverting and round-tripping.

---

## 5b. mppt_buck — specification & verification

A **new** switching buck (PV 17.6 V → 5 V store) replacing the linear MPPT board. Same
high-side IR2110 gate-drive as buck_v2 **but no NE555** — duty comes entirely from the
Arduino's Perturb & Observe PWM; PV sensing is external (INA219). Generated fresh with
`tools/generators/build_mppt_buck.py`. **Key difference: sized for ~2 A** (P_MPP ≈ 10 W /
5 V), not buck_v2's light load.

### 5b.1 Components (20, excl. 3 PWR_FLAG)

`J1` PV-in, `C1` 470 µ/25 V PV bulk, `Q1` IRF530 (high-side), `D1` **1N5822 ≥3 A Schottky**
(DO-201AD), `L1` 150 µ toroid, `C2` 47 µ out, `J2` store-out, `J3` PWM (Arduino), `R1` 200,
`U1` CNY17, `R2` 1k (HIN pulldown), `U2` IR2110, `R3` 10 (gate-R), `D3` 1N4148 (anti-par),
`R4` 1k (gate→SW pulldown), `D2` 1N4148 (boot diode), `C3` 1 µ (boot cap), `C4` 22 µ + `C5`
100 n (+15 V decoupling), `J4` +15 V in.

### 5b.2 Net acceptance table (must match exactly)

| Net | Members |
|---|---|
| VPV | C1.1, J1.1, Q1.D |
| SW | C3.2, D1.1, L1.1, Q1.S, R4.2, U2.5 |
| VOUT_5V | C2.1, J2.1, L1.2 |
| GATE | D3.2, Q1.G, R3.2, R4.1 |
| HO | D3.1, R3.1, U2.7 |
| HIN | R2.1, U1.4, U2.10 |
| VB | C3.1, D2.1, U2.6 |
| +15V | C4.1, C5.1, D2.2, J4.1, U1.5, U2.3, U2.9 |
| OPTO_A | R1.2, U1.1 |
| PWM | J3.1, R1.1 |
| GND_MCU | J3.2, U1.2 |
| GND | C1.2, C2.2, C4.2, C5.2, D1.2, J1.2, J2.2, J4.2, R2.2, U2.2, U2.11, U2.12, U2.13 |

IR2110 (U2) **high-side**: VDD/VCC(9,3)=+15V; VSS/COM(13,2)=GND; **VS(5)=SW**; **VB(6)=VB**;
**HO(7)=gate**; **HIN(10)=control**; **LIN(12)=GND, SD(11)=GND**; LO(1)=NC; NC=1,4,8,14.
**Power-stage checks:** D1 K→SW, A→GND (freewheel); L1 SW→VOUT_5V; Q1 D→VPV, S→SW; gate
pulldown R4 → **SW**. Bootstrap: VB={C3.1, D2.1, U2.6}, D2 anode∈+15V, C3 other end∈SW.

### 5b.3 Author's observed results

- ERC **0 errors** (benign `footprint_link_issues` + `lib_symbol_mismatch` only).
- Netlist: **12 nets, 20 components, all match §5b.2; no null/SMD footprints.**
- Placement: hand-placed (toroid = own quadrant), cluster **84.8 × 92.6 mm, 0 overlaps**.
- DRC: **0 unconnected pads, 0 footprint errors, 0 vias, 2 `track_dangling`.**
  Route: 8 F.Cu segments / 65 mm. *(Auto-pack first gave 1 via + 37 bridges/350 mm; the
  hand-place removed the via and cut bridges 4.6×.)*

### 5b.4 Power-sizing claims to check (this board's distinctive risk)

- **~2 A load** (10 W / 5 V) ⇒ freewheel diode upgraded 1N5819 (1 A) → **1N5822 (3 A/40 V
  Schottky)**. **The component shop has NO ≥3 A Schottky** (only 1N5817 1 A); BOM flags
  "order 1N5822/SB540". A *slow* silicon 3 A rectifier (1N5408) would **not** be acceptable
  at 31–62 kHz (reverse-recovery). Reviewer: confirm the chosen part is a fast Schottky with
  V_R ≥ ~30 V (SW swings to V_PV ≈ 20 V) and I ≥ 3 A.
- **Inductor** L = Vout(Vin−Vout)/(ΔI_L·f·Vin); at 17.6→5 V, ΔI_L = 0.6 A: f = 31 kHz →
  ≈174 µH, 62 kHz → ≈87 µH. Author set **150 µ (≈31 kHz)** as a placeholder; it is a
  **hand-wound toroid** (same footprint regardless of value) — value must be re-wound to
  the real Arduino PWM frequency, **which is still undetermined** (mega-pinmap: D5/Timer3
  "if Arduino-side", custom freq possible). Core must not saturate at ≥2.5 A peak.
- **PV input cap** 470 µ/25 V (≥ Voc 20.3 V) + 100 n: adequate for switch ripple; the linear
  MPPT's 3×4700 µ is *not* needed (that was a linear-regulator hold cap). **Cap footprints
  assume CP_Radial_D8 / C_Disc_D5 — measure the real parts** (§6.1 / §8).

---

## 6. Design decisions & rationale (judge these)

1. **boost = LO, buck = HO + bootstrap.** boost M1 source = GND (low-side) → LO is
   correct, VS = GND, no bootstrap. buck Q1 source = SW (high-side) → driving from LO
   would make a source-follower that never fully enhances and overheats; HO + VS→SW +
   bootstrap is mandatory. (`docs/system-architecture.md` §gate-drive.)
2. **Opto retained.** Provides isolation on the boost (separate `GND_MCU`) and, on both
   boards, level-shifts the ≤5 V PWM toward the IR2110's ~9.5 V VIH at VDD = 15 V. See
   §8.1 — this is the main point to scrutinise.
3. **Anti-parallel diode across the gate resistor** (D2 boost / D5 buck): turn-on through
   R (10 Ω, controlled dv/dt); turn-off bypasses R via the diode (fast). Note: the
   reference `drive_circuit` board actually wired this diode **in series**, not
   anti-parallel — the v2 boards use the *correct* anti-parallel arrangement, so they
   intentionally differ from `drive_circuit` here.
4. **Gate pulldown** holds the gate off before the driver is powered: boost R4 = gate→GND
   (low-side ref); buck R4 = gate→SW (high-side ref).
5. **Bootstrap parts (buck):** D4 = 1N4148 (fast), C7 = 1 µF. Reviewer should sanity-check
   C7 against the IR2110 datasheet for the intended 20–50 kHz and the IRF530 gate charge;
   1 µF is conservative for this Qg/frequency but **the footprint assumes a 5 mm-pitch
   disc — verify a real 1 µF film/ceramic fits** (flagged in BOM).
6. **Sourcing:** CNY17 is in the component shop; IR2110 is kit-only. Substitutions carried
   over: 1N5819→1N5817, 1N4007→1N4006 (flagged in `footprint_map.csv`).

---

## 7. Helper to dump net membership (for §4.2 / §5.2 / §5.3 diffs)

```python
# usage: py -3.13 dump_nets.py <board.json>
import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
nets = {}
for c in d["components"]:
    for pin, net in c.get("pads", {}).items():
        nets.setdefault(net, []).append(f"{c['ref']}.{pin}")
for n in sorted(nets):
    print(f"{n:16}: " + ", ".join(sorted(nets[n])))
missing = [c["ref"] for c in d["components"] if not c["footprint"]]
print("components:", len(d["components"]), " no-footprint:", missing or "none")
```

(`<board.json>` is produced by `<skill>\scripts\pcb_netlist_json.py` from the exported
`.net`.) A leading `/` on a net name is KiCad's local-label prefix and is cosmetic.

---

## 8. Open risks / assumptions the reviewer should specifically attack

1. **IR2110 input threshold margin (highest priority).** The opto runs as an
   emitter-follower (collector → +15 V, emitter → HIN/LIN, 1 k pulldown). Its output-high
   level must exceed VIH (~9.5 V at VDD = 15 V) with margin across CTR spread, temperature
   and the chosen LED current (R = 200 Ω). This worked on the bench-proven `drive_circuit`
   (same topology) but was **not re-measured here**. Validate: opto CTR at the LED current,
   resulting emitter VOH into 1 kΩ, vs IR2110 VIH(min). If marginal, lower the pulldown or
   raise LED drive.
2. **Bootstrap refresh (buck).** VB charges through D4 while the low-side is "on" (here:
   while SW is pulled low through the load/freewheel each cycle). Confirm the duty/freq
   range keeps C7 topped up; consider min off-time. Not analysed quantitatively here.
3. **No isolation on the buck.** `U3.2` (LED cathode) ties to power GND — the buck opto
   does **not** provide galvanic isolation (the 555 shares ground). This is intended
   (level-shift only), but confirm it matches the team's intent for the external-PWM path.
4. **`track_dangling` DRC items are benign but unverified by the author beyond
   "0 unconnected pads".** Reviewer should confirm each dangling stub is a stray segment,
   not a missing connection (0 unconnected pads is strong evidence). The 5.9 mm stub on
   buck `Net-(J3-Pin_1)` is cosmetically removable.
5. **Placement is auto/heuristic, not optimised.** boost auto-packed (17 bridges); buck
   hand-placed (21 bridges). Bridges = top-side wire jumpers to solder. Fewer is better;
   a reviewer may suggest a tighter hand-place (then re-route with `-KeepPlacement`).
6. **Design-rule enforcement lives in `.kicad_pro`.** Confirm the netclass in each
   `*.kicad_pro` is clearance 0.8 / track 1.0; opening the bare `.kicad_pcb` in the GUI
   would use wrong defaults.
7. **No bench or SPICE validation.** All checks are static (ERC/netlist/DRC/placement).
   The boards should be bench-tested (boost expects clean duty + small ripple at
   20–50 kHz vs. the old ~1 kHz limit).

---

## 9. Pass/fail checklist for the reviewer

- [ ] boost_v2 / buck_v2 / mppt_buck ERC each = 0 errors.
- [ ] boost_v2 netlist == §4.2 (all 11 nets, exact membership).
- [ ] buck_v2 gate-drive nets == §5.2; **U3.4 ∈ HIN and U3.4 ∉ GATE**.
- [ ] buck_v2 bootstrap present: VB = {C7.1, D4.1, U4.6}; VS(U4.5) ∈ SW; D4 anode on +15V.
- [ ] buck_v2 front-end nets (§5.3) identical to pre-patch.
- [ ] mppt_buck netlist == §5b.2; bootstrap VB = {C3.1, D2.1, U2.6}; VS(U2.5) ∈ SW; U1.4 ∈ HIN ∉ GATE.
- [ ] mppt_buck freewheel D1 is a **fast Schottky ≥3 A / ≥30 V** (shop lacks it — must be ordered); L re-wound to the real Arduino PWM frequency.
- [ ] IR2110 SD tied low on both boards; correct LO(boost)/HO(buck) channel used.
- [ ] All footprints THT; none null; none SMD (`SOIC`/`TSOT`/`SolderWire`).
- [ ] Both boards: 0 unconnected pads, 0 vias, no DRC errors except `track_dangling`/`silk_*`.
- [ ] `.kicad_pro` netclass = 0.8 mm clearance / 1.0 mm track.
- [ ] Production folders contain `<board>.dxf` (B.Cu+Edge, mirror in xTool),
      `<board>_top_cu.dxf`, gerbers, and `.drl`.
- [ ] (Judgement) §8.1 threshold margin and §8.2 bootstrap refresh are acceptable.

---

## 10. One-command reproduction from scratch (optional)

```powershell
# boost_v2: regenerate schematic, route, export
py -3.13 <repo>\hardware\kicad\tools\generators\build_boost_v2.py
<skill>\scripts\route_board.ps1 -Sch <repo>\...\boost_v2.kicad_sch -Pcb <repo>\...\boost_v2.kicad_pcb
<skill>\scripts\export_production.ps1 -Pcb <repo>\...\boost_v2.kicad_pcb -OutDir <repo>\hardware\kicad\production\boost_v2

# buck_v2: the patch is idempotent ONLY on a pristine pre-patch schematic; to re-derive,
# git-checkout the original buck_v2.kicad_sch first, then:
py -3.13 <repo>\hardware\kicad\tools\generators\patch_buck_v2_ir2110.py
<skill>\scripts\route_board.ps1 -Pcb <repo>\...\buck_v2.kicad_pcb -KeepPlacement
<skill>\scripts\export_production.ps1 -Pcb <repo>\...\buck_v2.kicad_pcb -OutDir <repo>\hardware\kicad\production\buck_v2
```

> **Caution for re-runs:** `patch_buck_v2_ir2110.py` deletes/relabels specific
> coordinates and must run on the *original* GUI schematic, not on an already-patched one.
> Always run it against a clean `git checkout` of `buck_v2.kicad_sch`.
