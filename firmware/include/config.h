/*
 * config.h - Central konfiguration for 62768 energisystem-firmware
 *
 * Samler alle pins, kalibreringskonstanter, setpoints og styre-
 * parametre ét sted, så hardware-tilpasning kun sker her.
 *
 * Afhængigheder: Arduino.h
 */
#ifndef CONFIG_H
#define CONFIG_H

/* ============ INCLUDES ============ */
#include <Arduino.h>
#include <stdint.h>

/* ============ PINS ============ */
// Motor-PWM. VIGTIGT: undgå Uno D9/D10 (Timer1) — Timer1 bruges til
// styre-loopets interrupt. D3 er Timer2 (Uno) / Timer3 (Mega) = OK.
#define PIN_MOTOR_PWM     3
#define PIN_STATUS_LED    LED_BUILTIN

// ADC-kanaler. Spændinger via spændingsdelere, strøm fra diskret måling.
#define ADC_CH_V1         A0    // Ensretter-bus, mål 15 V   (Krav 1)
#define ADC_CH_V2         A1    // Pulserende last, mål 10 V (Krav 4)
#define ADC_CH_V3         A2    // Energilager, mål 5 V      (Krav 7)
#define ADC_CH_ILOAD      A3    // Laststrøm fra diskret strømmåling (Krav 10)

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
#define DUTY_MIN          0         // analogWrite min
#define DUTY_MAX          255       // analogWrite max (8-bit)

/* ============ MONITOR ============ */
#define SERIAL_BAUD       115200
#define MONITOR_HZ        1         // PC-overvågning opdatering [Hz] (Krav 14)

#endif /* CONFIG_H */
