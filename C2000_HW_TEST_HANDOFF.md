# C2000 Code-Gen Hardware Bring-Up & Test — Handoff

**You are a fresh Claude Code session.** Goal: **get MATLAB/Simulink automatic code
generation actually running on the real TI C2000 F28027 LaunchPad**, and **verify each step
on hardware using a Digilent Analog Discovery 3 (AD3)** as the measurement + stimulus
instrument.

This is hands-on hardware work — you'll guide the user through Simulink deploy + WaveForms,
**and** you can script the AD3 yourself via its SDK to automate the verification. Work
**incrementally**: get the simplest thing blinking before touching the closed loop.

> Read first: the study note `Obsidian/Courses/62768 Electrical Energy Systems/Lecture
> Notes/Code Generation — C2000 Workflow.md` (the full workflow this deploys) and the four
> example models in `simulation/Code Generation/`.

---

## 0. Win condition

By the end you can demonstrate, on the physical board, with AD3 evidence:
1. **GPIO blink** deployed and toggling (LED + AD3 logic capture).
2. **ePWM** out at the right **frequency + duty** (AD3 scope: 5 kHz / 200 µs, duty tracks the slider).
3. **ADC** reading a **known AD3-supplied voltage** correctly (Monitor & Tune live value vs `count ≈ V·4095/3.3`).
4. (stretch) **MotorControl2026** closed loop responding to a reference.

Capture results in a test log → `C2000_HW_TEST_RESULTS.md` (per test: setup, AD3 numbers/screenshots, pass/fail, issues).

---

## 1. Hardware on the bench

| Item | Notes |
|---|---|
| **TI LAUNCHXL-F28027** | C2000 Piccolo F28027 LaunchPad, USB (XDS100v2 onboard debugger). Pinout: `docs/datasheets/Texas_Instruments-LAUNCHXL-F28027-datasheet.pdf` |
| **Digilent Analog Discovery 3** | USB. 2× scope (±25 V diff, 14-bit), 16× DIO (logic analyzer + pattern gen), 2× AWG (W1/W2, ±5 V), supplies. Host app **WaveForms 3**. |
| (optional) NI USB-6008 | also installed on this PC — alternative DAQ, but use the AD3 as asked. |

### ⚠️⚠️ SAFETY — read before wiring anything
- **Every F28027 pin is 3.3 V max.** The ADC inputs are **absolute-max 3.3 V** — overvoltage
  **kills the chip**.
- The **AD3 AWG can output ±5 V** → it *will* exceed 3.3 V if you're careless. When driving an
  ADC pin: set the AWG to **offset 1.65 V, amplitude ≤ 1.65 V** (so it swings 0–3.3 V), or add
  a divider/clamp. **Verify on the scope before connecting to the board.**
- **Common ground:** tie AD3 GND (⊥) to a LaunchPad **GND** pin, always.
- GPIO/ePWM outputs are 3.3 V logic — safe for the AD3 scope/logic inputs.

---

## 2. Software status (already installed — verify, don't reinstall)

| Tool | Where | Status |
|---|---|---|
| Code Composer Studio | `C:\ti\ccs2001` (v20.0.1) | installed. Also `CCS_20.5.1` installer in Downloads if a version bump is needed. |
| C2000Ware | `C:\ti\c2000` | installed |
| controlSUITE | `C:\ti\controlSUITE` | installed |
| WaveForms 3 + **SDK** | `C:\Program Files (x86)\Digilent\WaveForms3` + `…\WaveFormsSDK` | installed (`dwf` DLL present) |
| MATLAB | R2025a (+ R2024b) | Simulink + Embedded Coder present |
| **C2000 Microcontroller Blockset** | MATLAB Add-On | **VERIFY first** (see step 3) |

> Ignore `Downloads/sprc097` — those are **DSP281x** (older F281x) headers, **wrong chip**.
> The F28027 uses **C2000Ware**, already installed.

---

## 3. Bring-up plan (do these in order)

### Step 3.0 — verify the toolchain
- In MATLAB: `>> ver` (or Add-On Manager) → confirm **C2000 Microcontroller Blockset** is
  installed. If missing: Add-Ons → search `C2000` → install (MATLAB restarts). See the study
  note §3.
- Run **`c2000setup`** → it should **auto-detect** CCS `C:\ti\ccs2001`, C2000Ware `C:\ti\c2000`,
  controlSUITE. ⚠️ **Check the version it wants** — if it flags CCS 20.0.1 as untested for
  R2025a, point it at the **CCS 20.5.1** in Downloads (install first) or whichever it asks for.
  Version-mismatch is the #1 codegen failure.
- Plug in the LaunchPad → confirm Windows enumerates the XDS100v2 COM port (Device Manager),
  and `c2000setup`/CCS can see the target.

### Step 3.1 — GPIO blink (`PulseGenerator.slx`)  ← prove the chain end-to-end
- Open the model, Ctrl+E → Hardware board = **TI Piccolo F28027/F28027F LaunchPad**.
- **Build, Deploy & Start**. On-board LED should blink.
- **AD3 check:** probe the driven **GPIO pin** (find it from the model + LaunchPad pinout) with
  the AD3 **Logic analyzer** (or Scope). Confirm the toggle period matches the Pulse
  Generator. → first hardware evidence the codegen path works.

### Step 3.2 — ePWM (`SliderPWM.slx`)  ← verify the actuator
- Deploy. Probe the **ePWM1A output pin** with the **AD3 Scope**.
- Verify **frequency** (5 kHz → 200 µs period) using the scope's Measurements, and that moving
  the **slider changes the duty cycle** (AD3 duty measurement 0–100 %).
- Cross-check against the note's `TBPRD ≈ 11999 @ 60 MHz` maths.

### Step 3.3 — ADC (`ADC.slx`)  ← verify the sensor  ⚠️ 3.3 V SAFETY
- **AD3 AWG (W1)** → ADC input pin (`ADCINA5`, find the physical pin from the pinout).
  **Set W1 to a DC or slow ramp constrained to 0–3.3 V** (offset 1.65 V, amp ≤ 1.65 V). Verify
  on AD3 scope **before** connecting to the board.
- Run **Monitor & Tune (External Mode)** → read the ADC count live. Confirm
  **`count ≈ V_in · 4095 / 3.3`** (e.g. 1.65 V → ~2048). Sweep W1 and confirm linearity.
- This validates the sensing chain (`g_v,adc`) on real silicon.

### Step 3.4 — closed loop (`MotorControl2026.slx`)  ← stretch
- Needs a plant or an emulated feedback. Options: feed a known AD3 voltage as the "measured
  output" into the ADC and watch the PI drive the ePWM duty to regulate; or wire a simple RC
  as a fake plant. Verify the loop reacts to the reference. Keep it qualitative unless a real
  converter is on the bench.

---

## 4. Driving the Analog Discovery 3

Two ways — use both:

**A) WaveForms 3 GUI** (manual, fast to eyeball): Scope, Logic, Wavegen, Voltmeter tabs.
Good for first looks and screenshots for the log.

**B) Script it via the SDK** (automate verification — *this is the powerful part*):
- The `dwf` library lives in `C:\Program Files (x86)\Digilent\WaveFormsSDK`. Python binding:
  `pip install pydwf` (preferred), or call `dwf.dll` via `ctypes`. The SDK also ships C/Python
  samples under the install dir.
- With it you can, from a script: set **W1** to a precise 0–3.3 V level/ramp, capture **Scope
  CH1/CH2**, measure **frequency/duty** of the ePWM, and **sweep the ADC input while logging**
  — i.e. produce an automated PASS/FAIL for steps 3.2 and 3.3 instead of hand-reading the GUI.
- ⚠️ Enforce the **0–3.3 V clamp in code** before any AWG output reaches an ADC pin.

Close WaveForms 3 (GUI) before scripting — only one app can own the AD3 at a time.

---

## 5. Tooling / workflow notes

- **Builds** can run headless: `matlab -batch "..."` (open_system, set_param, `slbuild`/
  `rtwbuild`). But **Deploy + Monitor&Tune are interactive** — guide the user in the Simulink
  GUI (like prior sessions), and you handle the **AD3 side by script**.
- **Research hard:** the LaunchPad datasheet (pin map: which header pin = ePWM1A, ADCINA5,
  the LED GPIO), MathWorks "Get Started with C2000 Microcontroller Blockset", and the
  Digilent AD3 reference manual / WaveForms SDK docs. Clone repos / fetch examples as useful.
- Shell is **PowerShell on Windows**; quote paths with spaces.
- This is the **team repo** (`MadsRudolph/62768-energy-system`) — commit the results log with
  developer-voice messages, **no AI attribution** (global rule).

---

## 6. Likely gotchas

- **MATLAB↔CCS version mismatch** → build fails cryptically. Trust `c2000setup`'s required
  version; CCS 20.0.1 *and* 20.5.1 are available — use the one it asks for.
- **Wrong COM/driver** → install the XDS100v2 / FTDI driver if the target isn't seen.
- **AD3 + board ground not common** → garbage scope traces.
- **Over-voltage on ADC** → dead chip. Re-read §1 safety every time you touch an ADC pin.
- **Pin identification** — don't guess which physical pin is ePWM1A / ADCINA5; confirm from the
  datasheet pinout before probing/driving.
- `sprc097` in Downloads is the wrong chip's headers — ignore it.

---

## 7. Definition of done

- [ ] C2000 Blockset verified, `c2000setup` happy with CCS/C2000Ware/controlSUITE, target seen.
- [ ] `PulseGenerator` deployed; LED blinks; AD3 logic confirms timing.
- [ ] `SliderPWM` deployed; AD3 scope confirms 5 kHz + duty tracks the slider.
- [ ] `ADC` deployed; AD3 AWG (0–3.3 V) → Monitor&Tune count matches `V·4095/3.3`, linear sweep.
- [ ] (stretch) `MotorControl2026` loop responds to reference.
- [ ] `C2000_HW_TEST_RESULTS.md` written (per-test evidence + issues), committed + pushed.
- [ ] (nice) an AD3 SDK script that automates the PWM/ADC verification, committed.

Go incrementally, keep the 3.3 V rule sacred, and capture evidence at every step.
