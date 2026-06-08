# PID code-gen — rough / experimental

**Optional, not finalised.** An experiment in generating the PID controller's C code
from a MATLAB function (MATLAB Coder), instead of writing it by hand. The firmware PID
can just as well be **hand-written in C** — that's simpler and probably what we'll do.

Keep this only as a reference / proof-of-concept.

## Files
- `pid_step.m` — the PID written as a plain MATLAB function (one discrete step, anti-windup).
- `build_pid_codegen.m` — run it in MATLAB (needs the **MATLAB Coder** add-on) to emit C
  into `generated/` (gitignored).

## In short
- Run `build_pid_codegen` → get `pid_step.c` (clean `float` C).
- It generates **only the controller** — the hardware drivers stay hand-written.
- If we go hand-written instead, this folder can be ignored or deleted.
