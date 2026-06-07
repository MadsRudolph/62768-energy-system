# Firmware — 62768 Electrical Energy System

**Bare-metal AVR C** firmware (PlatformIO, no Arduino framework). Builds for
**Arduino Uno** (ATmega328P) and **Mega 2560**. The source files are empty
skeletons — to be written by the team.

## Build & upload

```bash
pio run -e uno            # build for Uno
pio run -e mega           # build for Mega 2560
pio run -e uno -t upload  # upload
pio device monitor        # serial monitor @ 115200
```

(Install PlatformIO: VS Code extension, or `pip install platformio`.)

## Files (skeletons — fill in)
| File | Intended role |
|------|---------------|
| `include/config.h` | Pins, calibration, setpoints, control parameters |
| `pid.h` / `src/pid.c` | PID controller (kept as plain C — can later be swapped for Simulink/Embedded Coder output) |
| `sensors.h` / `src/sensors.c` | ADC reading + scaling to volts/amps |
| `src/main.c` | Init, control loop, PWM, serial monitoring, ISRs |

## What it needs to do (from the spec)
- PID-regulate the motor/generator to hold bus **V1 = 15 V** (Krav 1)
- Use the Arduino's **ADC + timer interrupts + PWM** (Krav 15)
- **PC voltage monitoring**, updated every 1.0 s (Krav 13/14)

> Note: the skeletons are empty, so the project won't link until `main()` and the
> drivers are written.
