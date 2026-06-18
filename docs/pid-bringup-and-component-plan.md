# PID bring-up + component plan — what we actually need to close the V1 loop

Working doc for finishing the system. Two goals:

1. **Finish the untested perfboard circuits** (buck, current-sense, MPPT hardware).
2. **Get the V1 motor PID running on the C2000** so we can tune it with Ziegler–Nichols.

Decisions this doc is built on (locked 18 June):
- **PCBs = perfboard ("hulprint") prototypes**, not the KiCad laser boards. The
  `hardware/kicad/` laser pipeline is a parallel/optional track — not on the critical path.
- **Control split:** **C2000 LAUNCHXL-F28027 = V1 motor PID** (3.3 V I/O, Simulink codegen);
  **Arduino Nano = MPPT** (P&O + INA219). The two MCUs are independent.

> ⚠️ Because the PID brain is the **C2000, every signal into it is 0–3.3 V max**, not 5 V.
> The dividers/gains in [`mega-pinmap.md`](mega-pinmap.md) are sized for a 5 V Arduino and
> are **wrong for this target** — see §4 for the 3.3 V versions.

---

## 1. Where we are right now (what's built and tested)

| Block | Physical state | Tested? | Evidence |
|---|---|---|---|
| DC motor (SR555) → A20 generator → Y‑Δ transformer → 3φ rectifier → **V1** | Built | ✅ **Yes** | Full sweep table: 7.5 V motor in → **15.23 V** out; 12.5 V → 26.4 V (`report/sections/generator-transformer.tex`) |
| **Drive circuit** (CNY17 → IR2110 → IRF540N, low-side) | Perfboard | ✅ ran the motor for the rectifier sweep | `report/images/DriveCircuit/DriveCircuit-Hulprint.jpg` |
| **Boost** (store 5 V → load) | Perfboard | ✅ **Yes** | 10.1 V out, 56 mVpp ripple @ 10 kHz / 48 % duty (`report/sections/boost.tex`) |
| **Feedback / IL300 iso-amp** | Perfboard | ⚠️ built, no measurement written up | `report/images/Feedback-circuit/…` |
| **Buck** (V1 → 5 V store) | **Not built** | ❌ **No** | `buck.tex` is design-only, "TODO … måleresultater" |
| **Current sensing** (discrete shunt + op-amp) | **Not built** | ❌ **No** | `stroemmaaling.tex` is a TODO stub |
| **MPPT power stage** (PV → buck → store) | PV characterised only | ❌ hardware not built | PV I–V/P–V measured directly; buck-MPPT only simulated (`test.tex`, `styring.tex`) |
| **C2000 codegen chain** (GPIO/PWM/ADC) | — | ✅ all PASS | `C2000_HW_TEST_RESULTS.md` |
| **C2000 closed loop** (MotorControl2026) | — | ❌ "instructive failure" | bugs found + fixed on paper, see §5 |

**Bottom line:** the *plant for the V1 PID is already finished and measured.* The boost is
done. The pieces that are genuinely missing are the **buck**, the **current-sense**, the
**MPPT power stage**, and — for the PID specifically — a **V1 voltage-sense scaled to 3.3 V**.

---

## 2. Answering the four questions (for the PID, what do we actually need?)

The V1 PID loop is: **C2000 PWM → drive circuit → motor → generator → transformer →
rectifier → V1 → sense → back into C2000 ADC.** Everything else hangs *off* V1 or is a
*separate branch*. So:

| Question | For the V1 PID / Ziegler–Nichols? | Why |
|---|---|---|
| **Do we need the motor?** | ✅ **Yes — non-negotiable** | The motor+generator **is the plant** the PID controls. No motor = no V1 to regulate. |
| **Do we need the buck?** | ❌ **No** | The buck is a *load on V1* (it charges the 5 V store), not part of the V1 loop. For ZN tuning you want a **simple, known load** on V1 (a power resistor), not the buck. Buck is needed for the *full system* (Krav 8/9/12) and to prove the 100→300 mA V1 step — but **not to get the loop running**. |
| **Do we need the boost?** | ❌ **No** | Boost is `store (5 V) → load (V2)`, downstream of the store. Independent of V1. Already tested anyway. |
| **Do we need MPPT?** | ❌ **No** | MPPT is the *parallel PV source*, runs on the **Arduino**, feeds the store. Nothing to do with the V1 loop. |

**So the minimum hardware to start tuning the PID = motor-drive chain (have it) + a V1→3.3 V
sense divider (build it, ~10 min) + the C2000 + a power-resistor load on V1.** That's it.

The buck / current-sense / MPPT are needed to **complete the system and the report**, just
not to *start* closing the loop. Build them in parallel; they don't block the PID.

---

## 3. The concrete wiring plan for the V1 PID (C2000)

```
                         3.3 V logic                       12 V motor rail
   C2000 ePWM1A  ──Rs──▶ CNY17 LED  ══(opto)══▶ IR2110 ──▶ IRF540N ──▶ DC motor
   (GPIO0 / J6-1)        [drive circuit, already built]                  │
                                                                         ▼
                                                          A20 gen → Y‑Δ xfmr → 3φ rect
                                                                         │
                                                                        V1  (≈15 V reg,
                                                                         │   ≤~27 V open-loop)
   C2000 ADC  ◀── 10nF ──┬───[ R_low 1k ]── GND          ┌──────────────┤
   ADCINA1 / J5-5        │                                │   load: 150 Ω power resistor
        ▲          3.0 V zener to GND (clamp)        [ R_high 10k ]      (known load for tuning)
        └── series 1k ───┘                                │
                                                          └── (later: buck taps here)
   GND: tie C2000 J2-1  ──  drive-circuit GND  ──  rectifier/V1 GND  (one common ground)
```

### Pin assignment (from `C2000_HW_TEST_RESULTS.md` — these are verified-present pins)

| Signal | C2000 pin | Note |
|---|---|---|
| **PWM → drive circuit** | **ePWM1A = GPIO0 = J6 pin 1** | the pin used in the PWM PASS test; 3.3 V logic |
| **V1 sense → ADC** | **ADCINA1 = J5 pin 5** | the pin used in the ADC PASS test (A5 is **not** on any header) |
| **GND** | **J2 pin 1** | common with drive circuit + rectifier |
| (optional) heartbeat | GPIO (LED LD2 = GPIO0 is taken by PWM) | use another free GPIO if wanted |

### The three wiring jobs

1. **PWM out → opto in.** C2000 ePWM1A (3.3 V) drives the CNY17 LED through a series
   resistor `Rs`. The drive circuit was previously driven from a 5 V source — at 3.3 V the
   LED current drops, so **re-size `Rs` for ~10 mA**: `Rs ≈ (3.3 − 1.25 V)/10 mA ≈ 220 Ω`.
   **Verify on the scope that the IR2110 HIN input swings rail-to-rail** at the PWM frequency
   before trusting the loop.

2. **V1 → ADC (the missing sense, build this).** See §4 — divider + clamp into ADCINA1.

3. **Common ground.** C2000 GND ↔ drive-circuit GND ↔ rectifier/V1 GND. A floating ground
   gives the ADC a convincing phantom voltage (this exact mistake cost an evening twice —
   `C2000_HW_TEST_RESULTS.md`).

> 💡 **Note the galvanic isolation:** the CNY17 opto is *meant* to isolate the C2000's
> ground from the motor power ground. The V1 sense divider, however, ties the C2000 ground
> to the V1/power ground. That's fine for bench bring-up (single common ground), but be
> deliberate about it — don't accidentally create a ground loop through both paths.

---

## 4. The one piece to build for the PID — the V1 → 3.3 V sense

V1 regulates to ~15 V but can spike toward **~27 V open-loop** (rectifier table at high
motor duty). During ZN tuning the loop *will* briefly slam to full duty, so design the
divider for a safe max of **~33 V → 3.3 V**.

**Recommended divider: R_high = 10 kΩ, R_low = 1 kΩ (÷11), 1 % resistors.**

| V1 | ADC voltage | Fraction of 3.3 V FS |
|---|---|---|
| 15 V (nominal) | 1.36 V | 41 % |
| 27 V (open-loop max seen) | 2.45 V | 74 % |
| 36.3 V | 3.30 V | 100 % (clamp point) |

- **Low source impedance (10k‖1k ≈ 0.9 kΩ)** — good for the C2000 S/H (a 100k/10k divider
  would be too high-impedance and need a buffer; this avoids that).
- **Protect the pin** (C2000 ADC absolute-max = 3.3 V; overvoltage kills the chip):
  add a **series 1 kΩ + a 3.0 V zener to GND** at the ADC pin, and a **10 nF** cap to GND to
  settle the S/H.
- **Firmware scale:** `V1 = count · (3.3/4095) · (R_high+R_low)/R_low = count · (3.3/4095) · 11`.
  **Calibrate the ×11 against a multimeter** once wired (resistor tolerance + clamp leakage).

> Optional but cleaner (Krav 10 allows op-amps): buffer the divider with an **MCP601** unity
> follower before the ADC. Not required with the low-impedance divider above.

This same 3.3 V rescaling applies to V2, V3 and the current channels — the **full C2000
sensing map (all 6 channels + pins + scaled dividers/gains) is in
[`c2000-pinmap.md`](c2000-pinmap.md)**. Use that, not `mega-pinmap.md` (which is 5 V).

---

## 5. Getting the loop to actually close (fixing the documented C2000 failure)

The C2000 closed loop failed once (`MotorControl2026.slx`). The post-mortem found three
causes — **apply all three** before re-trying:

1. **PID saturation must match the actuator.** Set the Discrete PID **output limits AND
   integrator limits to [0, 1]**, clamping anti-windup. The old model let the integrator wind
   to ~100, so `CMPA = gain·output` saturated int16 past TBPRD and the ePWM **froze**. After
   the PID, scale [0,1] → TBPRD (`×TBPRD`, cast to the CMPA type) — confirm the product never
   exceeds TBPRD.
2. **Don't reuse the lecture's gains.** P=20 / I·Ts=2 / D=0.6 are for the lecturer's rig.
   Start near the verified Mega values (**P≈0.1, I≈10, D=0**) and re-tune (see §6). **No
   unfiltered D term** on the ripply rectifier ADC signal — if you use D, low-pass it.
3. **Verify the plant open-loop FIRST.** Deploy a **fixed duty** and confirm V1 reads the
   expected level on a meter *and* on the ADC (Monitor & Tune) before closing the loop. The
   famous failure was a floating ADC reading a phantom voltage.

Also from the bring-up log:
- Boot switch **S1 all-UP**, serial switch **S4 UP** (External-Mode/Monitor & Tune over the
  XDS100 UART). Flash standalone with the device-specific **`f28027.ccxml`**.
- **Monitor & Tune is on COM16** on the bench PC (set it in Ctrl+E → External mode if it
  complains about a saved COM9).
- ePWM1 in up-down at TBPRD=10000 → **3 kHz** (not 5 kHz). Pick the PWM frequency
  deliberately for the motor drive.

---

## 6. Ziegler–Nichols, in steps, for this plant

Once the open-loop check passes and the loop is stable at low P:

1. Set **I = 0, D = 0** (pure proportional).
2. Set a sensible **V1 reference** (e.g. 1.36 V at the ADC = 15 V) with a **fixed power-
   resistor load** on V1 (the 150 Ω used in the rectifier test is a good start).
3. **Raise P** until the V1 output shows a **sustained, constant-amplitude oscillation**.
   That P = **K_u** (ultimate gain); measure its period **T_u** (scope on V1, or log the ADC).
4. Apply the classic ZN table:

   | Controller | K_p | K_i = K_p/T_i | K_d = K_p·T_d |
   |---|---|---|---|
   | P | 0.5·K_u | — | — |
   | PI | 0.45·K_u | T_i = T_u/1.2 | — |
   | **PID** | 0.6·K_u | T_i = T_u/2 | T_d = T_u/8 |

5. Convert to the Simulink Discrete-PID form (its I and D are in `1/s` and `s` terms — match
   I = K_p/T_i, D = K_p·T_d, and remember the integrator/output **[0,1] clamp**).
6. Verify against the spec: **V1 = 15 V ±1 V**, and **hold through a 100→300 mA load step in
   ≤1 s** (Krav 1–3). Demonstrate the step by switching a second resistor onto V1.

> ⚠️ **Plant caveat — you may not get a clean sustained oscillation.** V1 is buffered by a
> **~14 mF** bus capacitor; with a 150 Ω load that's τ ≈ R·C ≈ 2 s, a very slow dominant
> pole. A slow first-order-dominated plant with little loop delay can be hard to push into
> pure-P oscillation. If P-only just gets sluggish/clips instead of ringing:
> - reduce the bus capacitor for the tuning run, or add load to speed the pole, **or**
> - use the **relay (Åström–Hägglund) method**: replace P with a relay (bang-bang on the
>   error), read the limit-cycle amplitude `a` and period `T_u`; then `K_u = 4d/(π·a)`
>   (d = relay half-amplitude) and use the same table. This is more reliable on slow plants.
> - Or just **tune from the Lec 1 model** `H(s)=22.83/((s+7.4)(s+37.17))` and fine-tune live.

---

## 7. Finishing the untested perfboard circuits (parallel track)

These don't block the PID, but they're needed for the full system + report. Build + bench-
test each (they mirror blocks we already proved, so reuse the known-good patterns):

| Circuit | Build notes | Test = "done" when |
|---|---|---|
| **Buck (V1 → 5 V store)** | IRF530/540 **high-side** switch → its own gate drive. **High-side needs the IR2110 high-side channel + bootstrap** (gate←HO, VS→SW node) — see `system-architecture.md §gate-drive`. Don't drive it from the motor's IR2110. Fixed ~33 % duty (own 555 or NE555) or an MCU PWM. | Vout = 5 V ±0.5 V into the 1 F store for I > 20 mA (Krav 7), ripple within spec |
| **Current sensing** | Low-side 1 Ω shunt + op-amp (MCP601), discrete (Krav 10). **I3/store is bidirectional → bias the amp to mid-scale** (1.65 V for 3.3 V FS, *not* 2.5 V — the C2000 rescaling again). | Output tracks a known current linearly; scale calibrated |
| **MPPT power stage** | PV → buck → store, **duty from the Arduino** (P&O, INA219 already coded in `firmware/MPPT/`). Linear-reg fallback exists but burns ~7 W → buck preferred. | P&O converges; store charges; PV prioritised over generator (Krav 11, 16, 17) |

Reference for the gate-drive details: the boost was rebuilt as `boost_v2` precisely because a
bare 4N25 opto was too slow → `opto → IR2110 → gate` is the proven pattern (`PCB_RESULTS.md`).

---

## 8. Shopping / build list (only what's not already on the bench)

For the **PID bring-up** (tiny):
- 1× **10 kΩ** + 1× **1 kΩ** 1 % resistor (V1 divider)
- 1× **3.0 V zener** (e.g. BZX55C3V0) + 1× **1 kΩ** series + 1× **10 nF** (ADC clamp/filter)
- 1× **~220 Ω** resistor (re-size the CNY17 series R for 3.3 V drive) — *check the existing
  value on the board first*
- 1× **150 Ω power resistor** (≥10 W) as the V1 tuning load — **already used** in the
  rectifier test, reuse it
- Dupont wires; common-ground jumper
- (have) C2000 LAUNCHXL-F28027 + XDS100 USB cable, AD3 for verification

For the **rest of the system** (already in the kit or `bom/footprint_map.csv`): IRF530/540N,
IR2110, CNY17/ILD74 optos, MCP601 op-amps, 1N5817/1N4006 diodes, inductors/caps per the
Lec 5 L/C sizing, 1 F super-cap (store), Arduino Nano + INA219 (MPPT). Nothing new needed
beyond the converter passives you size per the ripple equations.

---

## 9. Open items to confirm with the supervisor / team

1. **V2 nominal** — spec says ±1 V but no nominal; boost was tested to 10.1 V. Pin it down.
2. **Store** — 1 F super-cap vs 6 V gel battery (affects V3 headroom). Assume super-cap.
3. **V1 nominal vs rectifier "20–30 V" text** — `generator-transformer.tex` still describes a
   20–30 V bus with a buck down to 15 V, which **conflicts** with the spec/architecture
   (V1 = 15 V, buck → 5 V store). Reconcile the report narrative with the actual target
   (regulate V1 to **15 V** at the motor PWM; the buck makes **5 V**, not 15 V).
4. **3.3 V rescaling** — ✅ done: the full C2000 sense table (V1/V2/V3 + I1/I2/I3, pins +
   scaled dividers/gains) is in [`c2000-pinmap.md`](c2000-pinmap.md). `mega-pinmap.md` stays
   as the 5 V Arduino reference (now only relevant if the V1 PID ever falls back to the Mega).
