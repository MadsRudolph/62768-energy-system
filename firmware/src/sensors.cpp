/*
 * sensors.cpp - ADC-aflæsning og skalering
 *
 * Bruger Arduino-frameworkets analogRead (10-bit, AVcc reference).
 * Aflæsning sker i main-loopet (ikke i ISR), så blokerende analogRead
 * er OK ved styre-frekvensen i config.h.
 */

/* ============ INCLUDES ============ */
#include <Arduino.h>

#include "config.h"
#include "sensors.h"

/* ============ PRIVATE FUNKTIONER ============ */
// Rå ADC-count -> spænding på selve pinden [V]
static float sensors_pinVoltage(uint8_t adcChannel) {
    uint16_t raw = analogRead(adcChannel);
    return ((float)raw / ADC_MAXCOUNT) * ADC_VREF;
}

/* ============ PUBLIC API ============ */
void sensors_init(void) {
    // AVcc (5V) som ADC-reference. analogReference er default DEFAULT,
    // men sættes eksplicit for klarhed.
    analogReference(DEFAULT);

    // En "dummy" læsning pr. kanal for at lade ADC-sample/hold sætte sig
    (void)analogRead(ADC_CH_V1);
    (void)analogRead(ADC_CH_V2);
    (void)analogRead(ADC_CH_V3);
    (void)analogRead(ADC_CH_ILOAD);
}

float sensors_readVoltage(uint8_t adcChannel, float dividerRatio) {
    // Faktisk knudespænding = pin-spænding / delerforhold
    return sensors_pinVoltage(adcChannel) / dividerRatio;
}

float sensors_readCurrent(uint8_t adcChannel) {
    // I = (Vsensor - offset) / (V per A)
    float vsens = sensors_pinVoltage(adcChannel);
    return (vsens - ISENS_OFFSET) / ISENS_VPERA;
}
