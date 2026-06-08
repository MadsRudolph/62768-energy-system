# PID code generation — MATLAB Coder → C

Generates the controller's C code from a MATLAB function, to drop into the
firmware (`firmware/`) in place of a hand-written `pid.c`. This is the **hybrid**
flow: design/verify the control law in MATLAB, generate portable C, integrate with
the bare-metal AVR drivers.

## Files
| File | Role |
|------|------|
| `pid_step.m` | The controller: one discrete PID step with anti-windup, single precision (→ `float` in C). State lives in a struct the caller owns. |
| `build_pid_codegen.m` | Runs MATLAB Coder → emits `generated/pid_step.c` + `.h` (source only, no compile). |

## ⚠️ Requires the MATLAB Coder add-on
This machine has **Simulink Coder** but **not MATLAB Coder** (the `codegen`
command). The licence is available, so install it once:
**MATLAB → Home → Add-Ons → Get Add-Ons → search "MATLAB Coder" → Install.**

(Without it, `build_pid_codegen` errors with "Incorrect number … for function codegen".)

## Run
```matlab
>> cd simulation/matlab_coder
>> build_pid_codegen        % -> generated/pid_step.c, pid_step.h, rtwtypes.h
```

## Integrate into the firmware
1. Copy `generated/pid_step.c`, `pid_step.h`, `rtwtypes.h` into `firmware/` (e.g. `firmware/src` + `firmware/include`).
2. In `main.c`, hold the state struct and call `pid_step` each control tick:
   ```c
   // st fields: integ, prevMeas, Kp, Ki, Kd, Ts, uMin, uMax  (all float)
   u = pid_step(&st, setpoint, measured);   // generated signature may vary slightly
   ```
3. This replaces the hand-written PID; `sensors.c` + the Timer/PWM/UART drivers stay.

## Alternative (no install): Simulink Coder
If you'd rather not install MATLAB Coder, the build a Simulink PID model and generate
with the installed **Simulink Coder** instead (heavier `grt` output). Ask and we'll
script that path.

> Keep `Ts`, `Kp/Ki/Kd` consistent with `../DC-DC Converters/load_parameters.m` and the
> firmware's `CONTROL_HZ`.
