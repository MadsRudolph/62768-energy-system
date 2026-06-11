# Arduino Mega 2560 — pin map & sensing plan

The contract between firmware and hardware. The Mega does three jobs (see
[system-architecture.md](system-architecture.md)): **motor PID** (regulate V1 via the
motor-drive PWM), **MPPT**, and **1 s PC monitoring**. The buck/boost run their own
discrete loops — no Mega pins involved.

Codegen workflow + verified loop template: `simulation/Code Generation/MEGA/MegaPI.slx`,
gotchas in `C2000_HW_TEST_RESULTS.md`.

## Pin assignments

| Pin | Function | Notes |
|---|---|---|
| **D11** (Timer1) | PWM → motor drive (ILD74 opto → IR2110 → IRF540N) | Timer1 allows custom PWM frequency without breaking timekeeping; verified pin in `MegaPI` |
| **D5** (Timer3) | PWM → MPPT converter (only if MPPT ends up on the Arduino — see open questions) | |
| **D13** | Heartbeat LED (plain digital, 1 Hz toggle) | never re-clock Timer0 (D4/D13 PWM) — Arduino timekeeping |
| **A0** | V1 sense (rectifier bus, 15 V nom) | divider 30k/10k |
| **A1** | V2 sense (load) | divider 30k/10k |
| **A2** | V3 sense (store, 5 V nom) | divider 10k/10k |
| **A3** | I1 — generator current (300 mA max) | shunt + MCP601, unidirectional |
| **A4** | I2 — load current (150 mA min spec) | shunt + MCP601, unidirectional |
| **A5** | I3 — store current (**bidirectional!**) | shunt + MCP601 biased to 2.5 V mid-scale |
| **A6** | V_PV (panel voltage, for MPPT) | divider 40k/10k |
| **A7** | I_PV (panel current, for MPPT) | shunt + MCP601 |
| **Serial 0** (USB) | 1 s monitoring stream to PC | free — External Mode unusable on the CH340 anyway |
| AREF | default (AVCC = 5 V) | all scalings below assume 5.00 V ref |

## Voltage dividers (hardware to build — not on any board yet)

`count → volts` in firmware: `V = count · (5/1023) · (R_high + R_low)/R_low`

| Rail | Nominal | Design max | R_high / R_low | At max → ADC | Gain constant (V/count) | Resolution |
|---|---|---|---|---|---|---|
| V1 | 15 V | 20 V | **30k / 10k** (÷4) | 5.00 V | 0.019550 | 19.6 mV |
| V2 | ~10 V (TBC) | 20 V | **30k / 10k** (÷4) | 5.00 V | 0.019550 | 19.6 mV |
| V3 | 5 V | 10 V | **10k / 10k** (÷2) | 5.00 V | 0.009775 | 9.8 mV |
| V_PV | ~17 V (Vmp) | 25 V | **40k / 10k** (÷5) | 5.00 V | 0.024438 | 24.4 mV |

- Divider Thévenin impedance ≤ 8 kΩ in all cases — fine for the AVR ADC (wants ≤ 10 kΩ).
- Use 1 % resistors, or calibrate the gain constant per channel against a multimeter once.
- Optional insurance per ADC pin: 5.1 V zener to GND (clamps divider failure).

## Current sensing (Krav: discrete, op-amps OK)

Shunt low-side + MCP601 non-inverting amp, gain sized so design-max current ≈ 4.5 V:

| Channel | I max | Shunt | Amp gain | V/A at the pin |
|---|---|---|---|---|
| I1 (gen) | 400 mA | 1 Ω | 11× (10k/1k) | 11.0 |
| I2 (load) | 300 mA | 1 Ω | 15× (e.g. 15k/1.07k → use 11× and accept 3.3 V FS) | 11.0 |
| I3 (store) | ±300 mA | 1 Ω | 7.5× **+ 2.5 V bias** | 7.5, mid = 2.5 V |

I3 is the special one: the store charges *and* discharges, so the amp output must idle at
mid-scale (2.5 V from a 10k/10k reference divider into the non-inverting summing point).
Firmware: `I3 = (count·5/1023 − 2.5)/7.5`.

## Monitoring protocol (Serial 0, 115200 baud, 1 Hz)

CSV line, newline-terminated, units volts/amps with 3 decimals:

```
V1=14.98,V2=10.02,V3=5.01,I1=0.142,I2=0.098,I3=-0.021,VPV=16.8,IPV=0.31
```

Trivially parsed by the PC side (Python/serial monitor) and human-readable in any
terminal. Implement with a Serial Transmit block at a 1 s subrate (Rate Transition from
the 1 ms control rate).

## Control loops on the Mega

| Loop | In | Out | Rate | Notes |
|---|---|---|---|---|
| Motor PID (V1) | A0 | D11 duty | 1 kHz | the verified `MegaPI` structure; plant ≈ `22.83/((s+7.4)(s+37.17))` per Lec 1 Modeling — tune on hardware, Ziegler-Nichols start |
| MPPT P&O | A6, A7 | D5 duty (if Arduino-side) | 1–10 Hz | perturb duty, observe ΔP, classic P&O |
| Heartbeat | — | D13 | 1 Hz | proves the scheduler is alive |

PID hygiene (hard-won 11 June, both targets): saturation limits **[0, 1] on output AND
integrator** matching the ×255 → uint8 actuator scaling, clamping anti-windup, no
unfiltered D term on a ripply ADC signal.

## Open questions (supervisor / team decisions)

1. **V2 nominal** — spec says ±1 V but no nominal (diagram hints 10 V). Ask.
2. **MPPT: discrete or Arduino?** Project overview says "discrete MPPT (P&O)" under the
   PV branch but lists MPPT under the Arduino's role. If discrete, D5/A6/A7 free up.
3. **Store: 1 F super-cap vs 6 V gel battery** — affects the V3 divider headroom (both
   covered by ÷2 above).
4. Divider bank + current-sense channels need a home: extend `feedback_circuit` (today it
   only carries the Exp 3A IL300 iso-amp) or a new `sensing` board.
