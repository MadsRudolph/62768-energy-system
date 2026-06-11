# C2000 hardware bring-up — test results

Board: LAUNCHXL-F28027 (XDS100v2, COM16). Instrument: Digilent Analog Discovery 3,
scope probe **10x** (pass `--attenuation 10` to `tools/ad3/ad3_check.py`).
Toolchain: MATLAB R2025a + C2000 Microcontroller Blockset 25.1, TI cgt 22.6.0.LTS,
CCS 20.0.1 (DSS scripting), controlSUITE f2802x v230. Date: 2026-06-11.

## Toolchain fixes needed before anything built (step 3.0)

- **Simulink Coder + Embedded Coder were missing** from R2025a — only MATLAB Coder
  was installed. Installed both (25.1) headlessly with MathWorks Package Manager:
  `mpm install --release=R2025a --destination="C:\Program Files\MATLAB\R2025a"
  --products Simulink_Coder Embedded_Coder` (needs elevation). The Add-On GUI
  errors if you try to install them there afterwards — they're already present.
- `c2000setup` had already been run (third-party registry populated: TI cgt under
  `C:\ProgramData\MATLAB\tic2000\3P.instrset\...`, DSS from `C:\ti\ccs2001`).
- Verified end-to-end by building `PulseGenerator.slx` headlessly: codegen + cl2000
  compile + link OK (`PulseGenerator.out`).

## Test 3.1 — GPIO blink (`PulseGenerator.slx`) — **PASS**

- Model: Pulse Generator (period 1 ms, 50 %) → GPIO Digital Output, **GPIO0**
  (= LED LD2 = J6 pin 1). Board target was already `TI Piccolo F28027/F28027F LaunchPad`.
- Flashed via DSS:
  `dss.bat .../tic2000/CCS_Config/runProgram.js .../CCS_Config/f28027.ccxml PulseGenerator.out`
- AD3 scope on J6-1 (GND on J2-1), `ad3_check.py measure --attenuation 10
  --expect-freq 1000 --expect-duty 50`:

  | Measured | Expected | Verdict |
  |---|---|---|
  | 1000.61 Hz | 1000 Hz ±2 % | PASS |
  | 50.2 % duty | 50 % ±3 | PASS |
  | 0.04–3.23 V swing | 3.3 V logic | PASS |

- LED LD2 glows at half brightness (1 kHz is too fast to see blinking).

### Gotchas found (read before repeating)

1. **Boot switch S1 must be all-UP** (switch 3 = TRSTn up) or JTAG fails with
   `Error -1015: Device is not responding`. Demo position (UP-UP-DOWN) blocks the
   debugger. Power-cycle after changing.
2. **Flash with the device-specific `f28027.ccxml`**, not `f28x_generic.ccxml` —
   the generic config has no flash programmer ("flash is not available on this
   device", verify fails at 0x3F001F).
3. **10x probe**: AD3 reads 0–0.33 V unless attenuation is configured — looks like
   a floating-pin ghost signal. Set 10x in software (or flip probe to 1x).
4. Measured base frequency is +0.06 % off nominal — internal 10 MHz oscillator
   (no crystal fitted), well within tolerance.
5. (For step 3.3) **ADCINA5 is not on any LaunchPad header** — J1/J5/J2 carry
   A0–A4/A6/A7 and B1–B4/B6/B7 only. The lecture's `ADC.slx` channel must be
   remapped to e.g. ADCINA0 (J5-6) or ADCINA4 (J1-6).

## Test 3.2 — ePWM (`SliderPWM.slx`) — **PASS**

- Model: Slider → Constant → ePWM1 `WA` input (CMPA in %, source = input port).
  ePWM1: TBPRD = 10000 clock cycles, counting mode **Up-Down** → f = 60 MHz / (2·10000)
  = **3 kHz** (not the 5 kHz the handoff guessed). ePWM1A = GPIO0 = J6-1, same probe
  point as test 3.1.
- Static check (flashed binary, slider snapshot 15.28 %), AD3 `measure --attenuation 10`:

  | Measured | Expected | Verdict |
  |---|---|---|
  | 3014.32 Hz | 3000 Hz ±2 % | PASS |
  | 15.2 % duty | 15.28 % ±3 | PASS |

- Live check: deployed from the Simulink GUI with **Monitor & Tune**, duty tracked the
  slider in real time on the WaveForms scope (frequency constant at 3 kHz). Works as
  intended.

### Gotchas found

1. **External mode serial port is saved inside the model** — the lecture model shipped
   with COM9 and connect fails with `XCP serial port error ... cannot find the file
   specified`. Set Ctrl+E → Hardware Implementation → Target hardware resources →
   External mode → Serial port = **COM16** (this PC's XDS100 UART), then just
   Monitor & Tune → Connect (no rebuild needed — the binary is already running).
2. **S4 (serial switch) must be UP** for External mode — it routes the Piccolo SCI to
   the XDS100 USB-UART.
3. Monitor & Tune builds with `EXT_MODE=1` (XCP-on-serial, 3.75 Mbaud) baked into the
   binary — the standalone DSS-flash path and the Monitor & Tune path produce different
   executables from the same model.

## Test 3.3 — ADC (`ADC.slx`) — **PASS**

- Model samples **ADCINA1** (not ADCINA5 as the lecture quick-start suggested — and
  conveniently A1 *is* broken out: **J5 pin 5**). SOC0, acquisition window 7, trigger =
  CPU Timer0 (`CPU0_TINT0n`), Ts = 1 ms, uint16 out → gain 3.3/4095 → volts on
  Display/Gauge blocks.
- Stimulus: AD3 Wavegen W1 DC level (verified on the scope **before** wiring to the
  pin, never above 3.3 V) → J5-5. GND common on J2-1.
- Deployed via Monitor & Tune (COM16); count and reconstructed voltage tracked the
  applied DC level across a 0.5–3.0 V sweep, matching `count ≈ V·4095/3.3`
  (1.65 V → ~2048). Linearity good, works as intended.

## Test 3.4 — closed loop (`MotorControl2026.slx`) — stretch, pending
