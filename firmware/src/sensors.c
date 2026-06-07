/*
 * sensors.c - ADC-aflæsning og skalering (bare-metal AVR)
 *
 * Enkelt-conversion ADC (blokerende) på AVcc-reference. Aflæsning
 * sker i main-loopet, så blokerende ADC er OK ved styre-frekvensen.
 * Kanaler 0-7 dækker A0-A7 på både ATmega328P og ATmega2560.
 */

/* ============ INCLUDES ============ */
#include <avr/io.h>

#include "config.h"
#include "sensors.h"

/* ============ PRIVATE FUNKTIONER ============ */
// Læs én ADC-conversion på given kanal (0-7)
static uint16_t adc_read(uint8_t channel) {
    // ADMUX: AVcc reference (REFS0), højrejusteret, vælg kanal i MUX[3:0]
    ADMUX = (1 << REFS0) | (channel & 0x07);
    ADCSRA |= (1 << ADSC);              // start conversion
    while (ADCSRA & (1 << ADSC)) {      // vent til den er færdig
        ;
    }
    return ADC;
}

// Rå count -> spænding på selve pinden [V]
static float adc_pinVoltage(uint8_t channel) {
    return ((float)adc_read(channel) / ADC_MAXCOUNT) * ADC_VREF;
}

/* ============ PUBLIC API ============ */
void sensors_init(void) {
    // ADMUX: AVcc reference, kanal 0
    ADMUX = (1 << REFS0);

    // ADCSRA: ADC Control and Status Register A
    // - ADEN = 1: aktiver ADC
    // - ADPS[2:0] = 111: prescaler 128 -> 125 kHz ADC-clock @ 16 MHz
    ADCSRA = (1 << ADEN) | (1 << ADPS2) | (1 << ADPS1) | (1 << ADPS0);

    (void)adc_read(ADC_CH_V1);          // dummy-læsning så sample/hold sætter sig
}

float sensors_readVoltage(uint8_t channel, float dividerRatio) {
    // Faktisk knudespænding = pin-spænding / delerforhold
    return adc_pinVoltage(channel) / dividerRatio;
}

float sensors_readCurrent(uint8_t channel) {
    // I = (Vsensor - offset) / (V per A)
    return (adc_pinVoltage(channel) - ISENS_OFFSET) / ISENS_VPERA;
}
