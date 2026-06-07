# Firmware — 62768 Electrical Energy System

**Bare-metal AVR C** firmware (PlatformIO, no Arduino framework) for the system's
controller: PID regulation of the DC-motor / AC-generator to hold the rectifier
bus **V1 = 15 V**, plus PC voltage monitoring. Builds for **Arduino Uno**
(ATmega328P) and **Mega 2560**.

## Build & upload

```bash
pio run -e uno            # build for Uno
pio run -e mega           # build for Mega 2560
pio run -e uno -t upload  # upload
pio device monitor        # serial monitor @ 115200
```

(Install PlatformIO: VS Code extension, or `pip install platformio`.)

## How it works
- **Timer1** CTC interrupt @ `CONTROL_HZ` (200 Hz) → runs the control loop (Krav 15).
- Register-level **ADC** reads **V1** → **PID** (`pid.c`) → **Timer2 PWM** duty on OC2B (Krav 15).
- **UART** sends a CSV line `t_ms,V1,V2,V3,Iload,duty,run` once per second (Krav 13/14).
- Starts **stopped** for safety. Serial commands: `r` = run, `s` = stop.

## Files
| File | Role |
|------|------|
| `include/config.h` | **ADC channels, calibration, setpoint, PID gains** — tune here |
| `pid.h` / `src/pid.c` | Reusable PID, anti-windup (pure C — swappable for Simulink-generated code) |
| `sensors.h` / `src/sensors.c` | Register-level ADC → volts/amps scaling |
| `src/main.c` | UART, Timer1 ISR, Timer2 PWM, control loop, monitoring, commands |

## Pin map (motor PWM = Timer2 OC2B)
| Signal | Uno (328P) | Mega (2560) |
|--------|-----------|-------------|
| Motor PWM (OC2B) | **D3** (PD3) | **D9** (PH6) |
| Status LED (D13) | PB5 | PB7 |
| V1 / V2 / V3 / Iload | A0 / A1 / A2 / A3 | A0 / A1 / A2 / A3 |

> Timer1 is reserved for the control-loop interrupt — don't use OC1A/OC1B (Uno D9/D10) for PWM.

## ⚠️ Before running on hardware — set in `config.h`
- **Voltage-divider ratios** `DIV_V1/V2/V3` to your actual resistors.
- **Current-sensor** `ISENS_VPERA` / `ISENS_OFFSET` from the datasheet.
- **PID gains** `PID_KP/KI/KD` — start low; verify the **direction** (more PWM must raise V1; else invert).

## Simulink hand-off (planned)
`pid.c` is plain, hardware-independent C. When the controller is designed in Simulink,
Embedded Coder can generate an equivalent `controller_step()` to drop in place of `pid.c`;
`main.c` + `sensors.c` remain the bare-metal driver/scheduler layer that calls it.
