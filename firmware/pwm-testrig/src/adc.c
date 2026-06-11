/*
 * adc.c - Polled ADC-laesning af potmetrene
 *
 * Testriggen har ingen realtidskrav paa maalingerne (display og
 * PWM opdateres ~10 Hz), saa ADC'en laeses blokerende i main-loop
 * i stedet for via interrupt. 8 samples midles for at daempe stoej.
 *
 * Afhaengigheder: config.h
 */

/* ============ INCLUDES ============ */
#include <avr/io.h>
#include <stdint.h>

#include "adc.h"
#include "config.h"

/* ============ PRIVATE FUNKTIONER ============ */
static uint16_t adc_readOnce(uint8_t channel) {
    // Vaelg kanal, behold referencevalg (nederste 4 bit er MUX)
    ADMUX = (ADMUX & 0xF0) | (channel & 0x0F);

    ADCSRA |= (1 << ADSC);              // Start konvertering
    while (ADCSRA & (1 << ADSC));       // Vent til faerdig (~104 us)
    return ADC;
}

/* ============ PUBLIC API ============ */
void adc_init(void) {
    // ADMUX: ADC Multiplexer Selection Register
    // - REFS[1:0] = 01: AVcc (5 V) som reference - matcher potmetrenes forsyning
    // - ADLAR = 0: Hoejrejusteret resultat
    ADMUX = (1 << REFS0);

    // ADCSRA: ADC Control and Status Register A
    // - ADEN = 1: Aktiver ADC
    // - ADPS[2:0] = 111: Prescaler 128 -> 125 kHz ADC-clock @ 16 MHz
    //   (50-200 kHz kraeves for fuld 10-bit noejagtighed)
    ADCSRA = (1 << ADEN) | (1 << ADPS2) | (1 << ADPS1) | (1 << ADPS0);

    // Foerste konvertering efter ADEN er langsommere - smid den vaek
    (void)adc_readOnce(POT_DUTY_CHANNEL);
}

uint16_t adc_readAveraged(uint8_t channel) {
    // 8 samples og >>3: billig midling, daemper skyder-stoej
    uint16_t sum = 0;
    for (uint8_t i = 0; i < 8; i++) {
        sum += adc_readOnce(channel);
    }
    return sum >> 3;
}
