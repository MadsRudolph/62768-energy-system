/*
 * config.h - Central konfiguration for 62768 energisystem-firmware
 *
 * Samler alle ADC-kanaler, kalibreringskonstanter, setpoints og
 * styre-parametre ét sted, så hardware-tilpasning kun sker her.
 * Bare-metal AVR (ingen Arduino-framework).
 *
 * Afhængigheder: ingen
 */
#ifndef CONFIG_H
#define CONFIG_H

/* ============ INCLUDES ============ */
#include <stdint.h>

/* ============ HARDWARE ============ */
// Motor-PWM ligger på Timer2 OC2B (Uno: PD3/D3, Mega: PH6/D9) — sættes i main.c.
// Timer1 er reserveret til styre-loopets interrupt, så rør ikke OC1A/OC1B.

/* ============ ADC-KANALER ============ */
#define ADC_CH_V1         0    // A0: ensretter-bus, mål 15 V   (Krav 1)
#define ADC_CH_V2         1    // A1: pulserende last, mål 10 V (Krav 4)
#define ADC_CH_V3         2    // A2: energilager, mål 5 V      (Krav 7)
#define ADC_CH_ILOAD      3    // A3: laststrøm fra diskret måling (Krav 10)

/* ============ ADC / KALIBRERING ============ */
#define ADC_VREF          5.0f      // AVcc reference [V]
#define ADC_MAXCOUNT      1023.0f   // 10-bit ADC

// Spændingsdeler-forhold = R2 / (R1 + R2).  TODO: tilpas til faktisk hardware.
#define DIV_V1            0.250f    // 15 V -> 3.75 V  (fx R1=30k, R2=10k)
#define DIV_V2            0.330f    // 10 V -> 3.30 V  (fx R1=20k, R2=10k)
#define DIV_V3            0.500f    // 5 V  -> 2.50 V  (fx R1=10k, R2=10k)

// Strømsensor (fx ACS712). TODO: indsæt værdier fra databladet.
#define ISENS_VPERA       0.185f    // [V/A]  (ACS712-5A = 185 mV/A)
#define ISENS_OFFSET      2.50f     // [V] ved 0 A (typisk VCC/2)

/* ============ STYRING (PID) ============ */
#define CONTROL_HZ        200       // styre-loop frekvens [Hz]
#define SETPOINT_V1       15.0f     // ønsket bus-spænding [V] (Krav 1)
// PID-gains — TODO: tunes på rigtigt setup (start konservativt).
#define PID_KP            8.0f
#define PID_KI            40.0f
#define PID_KD            0.0f
#define DUTY_MIN          0         // PWM min (OCR2B)
#define DUTY_MAX          255       // PWM max (8-bit)

/* ============ MONITOR ============ */
#define SERIAL_BAUD       115200UL
#define MONITOR_HZ        1         // PC-overvågning opdatering [Hz] (Krav 14)

#endif /* CONFIG_H */
