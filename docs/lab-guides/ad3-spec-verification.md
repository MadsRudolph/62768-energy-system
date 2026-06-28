# AD3 spec-verification guide — remaining Pri-1 requirements

Measurement protocol for closing the six unverified Priority-1 requirements using the
**Analog Discovery 3 (AD3)** + WaveForms. The AD3 is the *instrument*; the rails are
powered by the actual energy system (generator / solar), not by the AD3 supplies.

Covers reqs **2, 3, 5, 6, 7, 16**. Each test lists the load setup, the WaveForms
instrument settings, the pass criteria (tied to the spec tolerance), and the report
section the capture belongs in.

> Workflow: Mads drives WaveForms and takes the measurements; this guide is the
> reference. Export each capture as PNG (WaveForms: *File → Export*) into the
> matching `report/images/...` folder and reference it in the listed section.

---

## 0. General setup & gotchas

- **Scope inputs are true differential.** Each channel (1+/1−, 2+/2−) measures across
  any two nodes — so you can probe a rail directly or sit across a floating shunt with
  no common-ground tricks.
- **Input range — use a 10× probe on V1 / rectifier.** AD3 single-ended range is ±25 V.
  V1 ≈ 15 V and the rectifier reaches ~26 V, which is at the ceiling. Use a 10× probe on
  those nodes (set *Attenuation = 10×* on that scope channel in WaveForms). V2 (10 V) and
  V3 (5 V) are fine at 1×.
- **Current without a current probe.** Two options:
  - *Known-resistor method (preferred for steady tests):* use a load resistor of known
    value, compute `I = V / R`. No shunt, nothing in the way.
  - *Shunt method (when you want the current waveform):* put a 1 Ω series shunt in the
    rail, measure the drop on a second diff channel, `I = V_shunt / 1 Ω`. Add a Math
    channel `M1 = C2 / 1` to read amps directly.
- **Load resistor power rating:** use ≥ 5 W (10 W safer). Worst case is the V1 50 Ω load
  at `15² / 50 = 4.5 W`.
- **Reuse WaveForms instruments:**
  - *Scope* — transients (reqs 3, 6): single trigger, long time base.
  - *Logger* or *Voltmeter* — steady levels (reqs 2, 5, 7, 16): slow recording over seconds/minutes.
  - *Wavegen (W1)* / *Static IO* — optional, to drive a MOSFET for repeatable load steps.

---

## 1. Load-step rig (used by reqs 3 and 6)

A load step = switch a second resistor in parallel with a base resistor.

```
 Rail (V1 or V2) ──┬── R_base ── GND        (always connected)
                   └── R_step ──[MOSFET D-S]── GND   (switched)
                                   │
                              gate ┘ ← AD3 W1 (0→5 V step)  OR manual switch
```

- Use a **logic-level** N-MOSFET — **IRLZ44N / IRL540N**. Do **not** use the IRF540N here;
  its gate needs ~10 V and the AD3 W1/DIO only swings to 5 V / 3.3 V, so it would stay in
  the linear region.
- **Repeatable step:** Wavegen W1 = single 0→5 V step (or square wave, slow), gate via a
  ~220 Ω gate resistor. Use the same W1 edge as the scope trigger source.
- **Manual fallback:** just flip a switch to add R_step, and let the scope auto-trigger on
  the voltage dip (trigger on the rail channel, falling edge). Simpler, works fine.

Resistor pairs (base ∥ step → total):

| Rail | Low current | High current | Base | Step (∥) | Total at high |
|------|-------------|--------------|------|----------|---------------|
| V1 (15 V) | 100 mA → 150 Ω | 300 mA → 50 Ω | 150 Ω | 75 Ω | 150 ∥ 75 = 50 Ω |
| V2 (10 V) | 50 mA → 200 Ω | 150 mA → 66.7 Ω | 200 Ω | 100 Ω | 200 ∥ 100 = 66.7 Ω |

---

## 2. Req 2 — AC-generator delivers 300 mA to buck

- **Goal:** show the generator → transformer → rectifier chain can supply 300 mA to the
  buck input at V1 ≈ 15 V.
- **Load:** 50 Ω across V1 (= 300 mA at 15 V).
- **WaveForms:** *Voltmeter* (or *Logger*) on Scope Ch1 (10× probe) reading V1. Confirm
  current either by the known resistor (`15 V / 50 Ω = 300 mA`) or a 1 Ω shunt + DMM.
- **Pass:** V1 holds ≈ 15 V while sourcing 300 mA (PID active).
- **Report:** generator-transformer section (add a short "delivered-current" line + value).

## 3. Req 3 — V1 = 15 ±1 V during 100→300 mA step, recover < 1.0 s

- **Goal:** under a 100→300 mA load step, V1 stays in band and the PID restores it < 1 s.
- **Load:** step rig, 150 Ω base ∥ 75 Ω step (§1).
- **WaveForms — Scope:**
  - Ch1 (10× probe) on V1; vertical ~2 V/div centred on 15 V.
  - Time base **200 ms/div** (≈ 2 s window).
  - Trigger: **Normal, single**; source = W1 edge (or Ch1 **falling edge ~14.8 V** if manual).
  - Add cursors to measure the dip minimum and the recovery time back into 14–16 V.
- **Pass:** V1 never leaves **14–16 V**, and returns inside the band **< 1.0 s** after the step.
- **Prereq:** the **TI-MCU PID loop must be running** (this recovery is the PID's job).
- **Report:** generator-transformer (new transient figure) + req 3 row in kravsporing.

## 4. Req 5 — V2 delivers ≥ 150 mA

- **Goal:** boost output sources ≥ 150 mA while staying in band.
- **Load:** 68 Ω across V2 (≈ 147 mA at 10 V).
- **WaveForms:** *Voltmeter/Logger* on Ch1 (1×) reading V2; current from known R or shunt.
- **Pass:** V2 in **9–11 V** while sourcing ~150 mA.
- **Report:** boost section (add delivered-current line) + req 5 row.

## 5. Req 6 — V2 = 10 ±1 V during 50→150 mA step, < 1.0 s

- **Goal:** under a 50→150 mA load step, V2 stays in band and recovers < 1 s.
- **Load:** step rig, 200 Ω base ∥ 100 Ω step (§1).
- **WaveForms — Scope:** Ch1 (1×) on V2; ~2 V/div centred on 10 V; **200 ms/div**; single
  trigger on the step edge; cursors for dip + recovery.
- **Pass:** V2 stays **9–11 V**, settles **< 1.0 s**.
- **⚠ Design check first:** the boost runs at **fixed 48 % duty (open-loop)** in the current
  design. An open-loop boost's output **sags under load and will not return to 10 V on its
  own** — this test likely fails unless V2 has a closed feedback loop. Confirm whether the
  boost is regulated before running; if not, this is a design gap to note in the discussion,
  not just a measurement.
- **Report:** boost section (transient figure) + req 6 row.

## 6. Req 7 — V3 = 5 ±0.5 V at currents > 20 mA

- **Goal:** energy-store / regulator output holds 5 V for I > 20 mA.
- **Load:** 250 Ω (≈ 20 mA) and 100 Ω (≈ 50 mA) across V3 — test at least two points above 20 mA.
- **WaveForms:** *Voltmeter/Logger* on Ch1 (1×) reading V3.
- **Pass:** V3 in **4.5–5.5 V** at every tested current > 20 mA.
- **Report:** solar/MPPT section (add V3 regulation table) + req 7 row.

## 7. Req 16 — System test with 100 W LED @ 0.5 m from solar panel

- **Goal:** demonstrate the full system running with the solar panel illuminated by a
  100 W LED lamp at 0.5 m.
- **Setup:** lamp at exactly 0.5 m facing the panel; system in normal operation
  (generator + solar, pulsing load on V2).
- **WaveForms — Logger:** record V1, V2, V3 (and motor current if shunted) over a window
  long enough to capture steady operation; take **lamp-off vs lamp-on** like the existing
  "complete system measurements," but with this specific lamp/distance as the PV source.
- **Pass:** system stays operational on solar; rails hold their target bands; motor current
  drops with the lamp on (solar contributing — consistent with the 33 % reduction already
  measured).
- **Report:** fill `test.tex` (once wired into `main.tex`) or fold into the integration
  section.

---

## 8. Results checklist

Tick when captured + dropped into the report. Update `kravsporing.tex` status as each lands.

| Req | Measured value(s) | Within spec? | Capture file | Done |
|-----|-------------------|--------------|--------------|------|
| 2  | V1 @ 300 mA = ___ V | 15 ±1 V | | ☐ |
| 3  | V1 dip = ___ V, recover = ___ s | 14–16 V, < 1 s | | ☐ |
| 5  | V2 @ 150 mA = ___ V | 9–11 V | | ☐ |
| 6  | V2 dip = ___ V, recover = ___ s | 9–11 V, < 1 s | | ☐ |
| 7  | V3 @ 20 mA = ___ V, @ 50 mA = ___ V | 4.5–5.5 V | | ☐ |
| 16 | rails lamp-on vs off | operational | | ☐ |

## 9. AD3 quick-reference

- **Scope:** 2 ch, true differential, 14-bit, ±25 V single-ended (use 10× on V1/rectifier).
- **Wavegen:** W1/W2, ±5 V — enough to drive a logic-level MOSFET gate, not a load directly.
- **Supplies:** V+ 0..+5 V, V− 0..−5 V, ~0.7 A total — *not* used to power the rails here.
- **Logger/Voltmeter:** slow recording — use for steady levels (reqs 2, 5, 7, 16).
- **Grounding:** AD3 ground = USB ground. With differential inputs you can float across a
  shunt; just don't tie a probe − to a node that fights the system's own isolation.
