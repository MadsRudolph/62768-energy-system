# Code Generation example models

The worked Simulink models from the **Code Generation** lecture series (Ashraf/Sam).
They demonstrate the MATLAB → C automatic-code-generation workflow, peripheral by
peripheral, building up to a closed-loop controller.

| Model | Demonstrates | Lecture |
|---|---|---|
| `PulseGenerator.slx` | GPIO digital output (the LED-blink smoke test) | Deck 1–2 (Install) |
| `SliderPWM.slx` | ePWM — set frequency + vary duty live with a slider | Deck 3 (PWM) |
| `ADC.slx` | ADC peripheral — SOC trigger, channel, the sensing chain | Deck 4 (ADC) |
| `MotorControl2026.slx` | **closed-loop PI(z) control** — ref → PI → PWM → plant → ADC → back | Deck 5 (PID) |

`MotorControl2026.slx` is effectively the **template for our own motor/converter control**.

## ⚠️ Target board
These examples target the **TI C2000 F28027 LaunchPad** (the lecture's board). Our project
uses an **Arduino Mega 2560** — to run them on it, change *Configuration Parameters
(Ctrl+E) → Hardware board* and swap the C2000 ePWM/ADC blocks for the Arduino PWM / Analog
Input blocks. See the study notes for the full mapping:

- Slides + write-up: `Obsidian/Courses/62768 Electrical Energy Systems/` →
  `Lecture Notes/Code Generation — C2000 Workflow.md` (the lecture target) and
  `…/Code Generation — ATmega2560 (Arduino Mega) Workflow.md` (our board).

Needs the **C2000 Microcontroller Blockset** (for the originals) or the **Simulink Support
Package for Arduino Hardware** (to retarget) — see the install steps in those notes.
