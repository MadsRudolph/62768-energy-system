# Firmware — 62768 Electrical Energy System

Arduino firmware (PlatformIO) for the system's controller: PID regulation of the
DC-motor / AC-generator to hold the rectifier bus **V1 = 15 V**, plus PC voltage
monitoring. Builds for **Arduino Uno** (ATmega328P) and **Mega 2560**.

## Build & upload

```bash
pio run -e uno            # build for Uno
pio run -e mega           # build for Mega 2560
pio run -e uno -t upload  # upload
pio device monitor        # serial monitor @ 115200
```

(Install PlatformIO: VS Code extension, or `pip install platformio`.)

## How it works
- **Timer1** fires a CTC interrupt at `CONTROL_HZ` (200 Hz) → runs the control loop (Krav 15).
- Reads **V1** via ADC, runs a **PID** (`pid.cpp`) → motor PWM duty on `PIN_MOTOR_PWM` (D3).
- Sends a CSV line `t_ms,V1,V2,V3,Iload,duty,run` once per second (Krav 13/14) — log/plot it on the PC.
- Starts **stopped** for safety. Serial commands: `r` = run, `s` = stop.

## Files
| File | Role |
|------|------|
| `include/config.h` | **Pins, calibration, setpoint, PID gains** — tune here |
| `include/pid.h`, `src/pid.cpp` | Reusable PID with anti-windup |
| `include/sensors.h`, `src/sensors.cpp` | ADC → volts/amps scaling |
| `src/main.cpp` | Timer1 ISR, control loop, monitoring, serial commands |

## ⚠️ Before running on hardware — set these in `config.h`
- **Voltage-divider ratios** `DIV_V1/V2/V3` to your actual resistors (so readings are correct).
- **Current-sensor** `ISENS_VPERA` / `ISENS_OFFSET` from the datasheet.
- **PID gains** `PID_KP/KI/KD` — start low and tune; verify the **sign/direction** matches the
  wiring (more PWM must raise V1; otherwise invert).
- Motor PWM is on **D3** on purpose — don't move it to D9/D10 (those use Timer1, reserved for the
  control-loop interrupt).
