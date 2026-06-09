# System Architecture — how the circuits fit together

**Read this before wiring blocks together.** It clears up which parts are *separate
circuits* and how they actually connect — and one mix-up that's easy to make.

---

## The system at a glance (the signal/power chain)

```
Arduino ──PWM──▶ [Motor drive] ──▶ DC Motor ──▶ AC Generator ──▶ 3φ Transformer ──▶ Rectifier ──▶ V1 (15 V)
   ▲                                                                                                  │
   └──────────────────────── [Feedback / sensing] ◀──────────────────────────────────────────────────┤
                                                                                                      │
                                                                                                      ▼
                                                                  [Buck] ──▶ Store (1F, V3 = 5 V) ──▶ [Boost] ──▶ Load (V2)
PV panel ──▶ [MPPT] ──────────────────────────────────────────────────────▶ Store
```

The blocks in `[brackets]` are the circuits we build. Power flows **left → right**; the
feedback path closes the control loops back to the Arduino.

---

## The separate circuits (each is its own block)

| # | Circuit | Input → Output | Its job |
|---|---|---|---|
| 1 | **Motor drive** | Arduino PWM → DC motor | spin the motor → generator, which sets **V1**. The Arduino's **PID regulates V1 by varying this PWM** (motor speed). |
| 2 | **Feedback / sensing** | V1, V2, V3, currents → Arduino & converter controllers | measure everything (op-amps + dividers) for the control loops and PC monitoring. |
| 3 | **Buck converter** | **V1 (15 V)** → 5 V store | step the rectified bus down to charge the energy store. Has **its own** switch, gate drive, and control. |
| 4 | **Boost converter** | store (5 V) → load (15 V) | step the store up to the pulsing load. Has **its own** switch, gate drive, and control. |
| (5) | **PV + MPPT** | solar panel → store | maximum-power-point tracking into the store (PV is consumed first). |

---

## What connects to what — the rules

- **Motor drive** is at the **very start** of the chain. Its only output is the **motor**.
  Its PWM exists to **regulate V1** (via motor speed) — nothing else.
- **Buck input = V1** (the rectifier output). **Not** the motor drive.
- **Boost input = the store.** **Not** the buck directly (the store sits between them).
- **Each converter has its OWN gate driver and its OWN feedback** that regulates *its own*
  output. They are independent stages.

---

## ⚠️ Common mix-up: the buck is **NOT** part of the motor drive

It's tempting to tap the motor drive's **IR2110** to switch the buck's MOSFET — they use
the same `opto → IR2110 → MOSFET` pattern, so they look alike. **Don't.** Here's why:

- The motor drive's PWM duty is set by the **V1 loop** (whatever motor speed V1 needs).
- The buck's switch needs a PWM that regulates the **buck's 5 V output** — a *different*
  objective.

If the buck is driven from the motor's IR2110, it just chops at *the motor's* duty. It may
*read* ~5 V (because the motor PWM happens to land near the right duty), but the moment the
V1 loop changes that duty, **the buck output drifts with it.** The two stages become
accidentally chained.

**What the buck should have instead** — its own front-end, fed from V1:

```
   senses buck 5 V output
            │
            ▼
   [Buck control] ──▶ [own gate driver: opto + IR2110 + bootstrap] ──▶ IRF530N ──▶ L-C ──▶ 5 V
                                                                          ▲
                                                                     V1 (15 V) in
```

The control is either a **discrete op-amp loop** (Krav 9 prefers discrete) regulating to
5 V, or a separate Arduino PWM channel — but **independent of the motor drive**. The boost
is the same idea (its own drive + feedback).

**One-liner:** *the motor drive and the buck are different stages — the buck takes V1 in
and needs its own gate driver + its own feedback. Don't drive the buck from the motor's
IR2110.*

---

## Gate-drive reminder (applies to each converter switch)

The **buck switch is high-side** (its source = the switching node SW, which swings up to
15 V). To drive a high-side N-MOSFET you **must** use the IR2110's **high-side** channel:

- gate ← **HO (pin 7)**, *not* LO (pin 1)
- **VS (pin 5) → the SW node** (the MOSFET source)
- **bootstrap**: diode VCC→VB + cap VB→VS

Driving a high-side MOSFET from a **ground-referenced** output (LO) makes it run as a
**source follower** — it "works" (the output gets choppy ~12 V instead of 15 V, so you
need more duty), but the MOSFET sits in its linear region and **dissipates a lot of heat**.
If a switch MOSFET is getting hot, this is usually why. (The boost switch is low-side —
LO is correct there.)
